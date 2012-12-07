from lxml import etree
from copy import deepcopy
import datetime, os, time
from vcapp import transxchange_constants

from vcapp.models import InterchangeStation, Line, Segment, Station, Trip, TripStop
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

PATH_TO_DATA = "../data"
TRANSXCHANGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE = "{%s}" % TRANSXCHANGE_NAMESPACE
NSMAP = {"T" : TRANSXCHANGE_NAMESPACE}


def determine_line_id(svc_code, first_stop):
    """
    The first stop is indicative of which direction the train is
     going and thus which line it is on. This info isn't provided
     in the transxchange data as far as I can tell
    """
    line_id = -1
    if svc_code in transxchange_constants.ALL_BLUE_MOUNTAINS_SERVICES:
        if first_stop in transxchange_constants.LITHGOW_TO_CENTRAL_ORIGINS:
            line_id = 1
        elif first_stop in transxchange_constants.CENTRAL_TO_LITHGOW_ORIGINS:
            line_id = 2
        else:
            logging.error("Unable to determine trip direction because %s is not"
                  "a registered Origin on Blue Mountains line", first_stop)

    elif svc_code in transxchange_constants.YELLOW_LINE_SERVICES:
        if first_stop in transxchange_constants.PENRITH_TO_HORNSBY_ORIGINS:
            line_id = 3
        elif first_stop in transxchange_constants.HORNSBY_TO_PENRITH_ORIGINS:
            line_id = 4
        else:
            logging.error("Unable to determine trip direction because %s is not"
                  "a registered Origin on the Yellow Line", first_stop)

    else:
        logging.error("Unable to determine trip direction because %s is not a"
              "registered Origin", first_stop)

    return line_id

def create_interchange_stations(interchange_station_map):
    interchange_station_count = 0
    interchange_relationship_count = 0

    start_time = time.time()
    # Setup Interchange Stations
    for station in Station.objects.all():
        if station.station_name in interchange_station_map:
            interchange_station_count += 0
            for line_id in interchange_station_map[station.station_name]:
                InterchangeStation.objects.create(station=station,
                    line=Line.objects.get(id=line_id))
                interchange_relationship_count += 0

    logging.info("Created %s interchange stations and %s relationships in %.2f secs",
        interchange_station_count,
        interchange_relationship_count,
        time.time() - start_time)

def extract_vehicle_journies(parsed_xml):
    """
    Vehicle Journey
     (which has a single Journey Pattern Section reference)
     (which has a departure time)
     (which has a line reference and service reference)
    """
    xp_vehicle_journey = etree.XPath("//T:VehicleJourney", namespaces=NSMAP)
    xp_vehicle_journey_code = etree.XPath("//T:VehicleJourneyCode", namespaces=NSMAP)
    xp_journey_pattern_ref = etree.XPath("//T:JourneyPatternRef", namespaces=NSMAP)
    xp_line_ref = etree.XPath("//T:LineRef", namespaces=NSMAP)
    xp_service_ref = etree.XPath("//T:ServiceRef", namespaces=NSMAP)
    xp_dep_time = etree.XPath("//T:DepartureTime", namespaces=NSMAP)
    # Do I need the Direction element?

    # Store details of each vehicle journey
    vehicle_journey_dict = {}
    start_time = time.time()
    vehicle_journey_count = 0
    for vj in map(deepcopy, xp_vehicle_journey(parsed_xml)):
        vehicle_journey_id = xp_vehicle_journey_code(vj)[0].text
        journey_pattern_ref_id = xp_journey_pattern_ref(vj)[0].text
        line_ref_id = int(xp_line_ref(vj)[0].text)
        service_ref_id = xp_service_ref(vj)[0].text
        departure_time = xp_dep_time(vj)[0].text
        vehicle_journey_dict[vehicle_journey_id] = (service_ref_id, line_ref_id, journey_pattern_ref_id, departure_time)
        vehicle_journey_count += 1

    logging.info("Found %s vehicle journies in %.2f secs",
        vehicle_journey_count,
        time.time() - start_time)

    return vehicle_journey_dict

def extract_stations(parsed_xml):
    # Find the stop points
    xp_stop_point = etree.XPath("//T:StopPoint", namespaces=NSMAP)
    xp_atco_code = etree.XPath("//T:AtcoCode", namespaces=NSMAP)
    xp_common_name = etree.XPath("//T:Descriptor//T:CommonName", namespaces=NSMAP)
    xp_lon = etree.XPath("//T:Place//T:Location//T:Longitude", namespaces=NSMAP)
    xp_lat = etree.XPath("//T:Place//T:Location//T:Latitude", namespaces=NSMAP)

    atcocode_station_map = {}

    created_station_count = 0
    start_time = time.time()
    for stop_point in map(deepcopy, xp_stop_point(parsed_xml)):
        atco_code = int(xp_atco_code(stop_point)[0].text)
        stop_name = xp_common_name(stop_point)[0].text
        lon = float(xp_lon(stop_point)[0].text)
        lat = float(xp_lat(stop_point)[0].text)
        station, created = Station.objects.get_or_create(station_name=stop_name, lon=lon, lat=lat)
        if created:
            created_station_count += 1

        atcocode_station_map[atco_code] = station

    logging.info("Created %s stations in %.2f secs",
        created_station_count,
        time.time() - start_time)
    return atcocode_station_map

def extract_journey_pattern_sections(parsed_xml):
    # Journey Pattern Sections
    #  (which contain 1 or more Journey Pattern Timing Links)
    xp_journey_pattern_section = etree.XPath("//T:JourneyPatternSection", namespaces=NSMAP)
    xp_from_stop_point = etree.XPath("//T:From//T:StopPointRef", namespaces=NSMAP)
    xp_to_stop_point = etree.XPath("//T:To//T:StopPointRef", namespaces=NSMAP)
    xp_run_time = etree.XPath("//T:RunTime", namespaces=NSMAP)
    xp_journey_pattern_timing_link = etree.XPath("//T:JourneyPatternTimingLink", namespaces=NSMAP)

    journey_pattern_section_count = 0
    journey_pattern_timing_link_count = 0
    journey_pattern_section_dict = {}

    start_time = time.time()
    for journey_pattern_section in map(deepcopy, xp_journey_pattern_section(parsed_xml)):
        journey_pattern_timing_link_list = []
        for journey_pattern_timing_link in map(deepcopy, xp_journey_pattern_timing_link(journey_pattern_section)):
            from_stop = xp_from_stop_point(journey_pattern_timing_link)[0].text
            to_stop = xp_to_stop_point(journey_pattern_timing_link)[0].text
            # In the format PT[0-9]{1,}M
            run_time = int(xp_run_time(journey_pattern_timing_link)[0].text[2:-1])
            # TODO: Can possibly use objects here... maybe
            journey_pattern_timing_link_list.append((from_stop, to_stop, run_time))
            journey_pattern_timing_link_count += 1

        journey_pattern_section_dict[journey_pattern_section.attrib["id"]] = \
            journey_pattern_timing_link_list
        journey_pattern_section_count += 1

    logging.info("Found %s journey pattern timing links with %s sections in %.2f secs",
        journey_pattern_timing_link_count,
        journey_pattern_section_count,
        time.time() - start_time)

    return journey_pattern_section_dict

def create_tripstops_and_segments(journey_pattern_timing_link_list, atcocode_station_map, this_trip, departure_time_dt):
    # Create Tripstops
    departure_tripstop = None
    segment_count = 0
    tripstop_count = 0
    for from_stop_id, to_stop_id, run_time in journey_pattern_timing_link_list:
        #logging.debug("Processing jptl: From %s, To %s, Run time %s",
        #    from_stop_id, to_stop_id, run_time)
        if departure_tripstop == None:
            # This is the first TripStop point in the trip so we need
            #  to setup the starting point
            departure_station = atcocode_station_map[int(from_stop_id)]
            logging.debug("Initial tripstop: From %s (id %s) at %s (trip id %s)",
                departure_station.station_name,
                departure_station.id,
                departure_time_dt, this_trip.id)
            departure_tripstop = TripStop(
                departure_time=departure_time_dt,
                trip=this_trip,
                station=departure_station)
            departure_tripstop.save()
            tripstop_count += 1

        # Departure time isn't always the same as arrival time, but that's what we're using
        arrival_tripstop = TripStop(
            departure_time=departure_tripstop.departure_time + datetime.timedelta(minutes=run_time),
            trip=this_trip,
            station=atcocode_station_map[int(to_stop_id)])
        arrival_tripstop.save()
        logging.debug("Arrival Tripstop: %s at %s (trip id %s)",
            arrival_tripstop.station.station_name,
            arrival_tripstop.departure_time,
            arrival_tripstop.trip.id)
        tripstop_count += 1

        s = Segment(departure_tripstop=departure_tripstop,
            arrival_tripstop=arrival_tripstop,
            trip=this_trip)
        s.save()
        segment_count += 1
        departure_tripstop = arrival_tripstop

    logging.info("Added %s TripStops and %s Segments to Trip with Id %s"
                 "that departs at %s)",
        tripstop_count,
        segment_count,
        this_trip.id,
        departure_time_dt)

def create_trips(parsed_xml, service_list, vehicle_journey_dict, atcocode_station_map, journey_pattern_section_dict):
    # Service
    #  (which contains a list of Journey Pattern Section references)
    #  (which has an origin and destination)
    #  (which lists the operating period (which days of the week)

    xp_service = etree.XPath("//T:Service", namespaces=NSMAP)
    xp_service_code = etree.XPath("//T:ServiceCode", namespaces=NSMAP)
    #xp_service_desc = etree.XPath("//T:Description", namespaces=NSMAP)
    xp_service_origin = etree.XPath("//T:StandardService//T:Origin", namespaces=NSMAP)
    xp_service_dest = etree.XPath("//T:StandardService//T:Destination", namespaces=NSMAP)
    xp_journey_pattern = etree.XPath("//T:StandardService//T:JourneyPattern", namespaces=NSMAP)
    #xp_journey_pattern_section_ref = etree.XPath("//T:StandardService//T:JourneyPattern//T:JourneyPatternSectionRefs", namespaces=NSMAP)
    xp_days_of_week = etree.XPath("//T:OperatingProfile//T:RegularDayType//T:DaysOfWeek//T:*", namespaces=NSMAP)

    for s in map(deepcopy, xp_service(parsed_xml)):
        service_code = int(xp_service_code(s)[0].text)
        # There are lots of repeated spaces in the service desc
        #service_desc = " ".join(xp_service_desc(s)[0].text.split())
        service_origin = xp_service_origin(s)[0].text
        service_dest = xp_service_dest(s)[0].text
        # abbreviated to three letters
        operating_days = [day.tag[len(TRANSXCHANGE):][:3] for day in xp_days_of_week(s)]
        if service_code in service_list:
            # FIXME - get the journey pattern section refs from the actual
            #  jpsr element, not from the id of the journey pattern element
            #  even though they're the same in the example file
            for vehicle_journey_ref in xp_journey_pattern(s):
                #service_ref_id =  vehicle_journey_dict[vehicle_journey_ref.attrib["id"]][0]
                #line_ref_id =  vehicle_journey_dict[vehicle_journey_ref.attrib["id"]][1]
                journey_pattern_ref_id =  vehicle_journey_dict[vehicle_journey_ref.attrib["id"]][2]
                departure_time_dt = datetime.datetime.strptime(
                    vehicle_journey_dict[vehicle_journey_ref.attrib["id"]][3], "%H:%M:%S")
                # FIXME - we can't handle time comparisons when the system rolls
                #  over past midnight, so for the sake of testing, let's drop any
                #  trip that starts after 8pm
                if departure_time_dt.time() > datetime.time(hour=20, minute=0):
                    logging.info("Bailing on service code %s (%s to %s) because"
                                 "it starts late (%s)",
                        service_code,
                        service_origin,
                        service_dest,
                        departure_time_dt.strftime("%H:%M"))
                    continue

                journey_pattern_timing_link_list = \
                    journey_pattern_section_dict[journey_pattern_ref_id]
                first_stop_name = atcocode_station_map[int(journey_pattern_timing_link_list[0][0])].station_name
                # One of these is (should be) redundant
                #print "FSN ->%s<- SO ->%s<-" % (first_stop_name, service_origin)
                #assert first_stop_name == service_origin
                line_id = determine_line_id(service_code, first_stop_name)
                if line_id == -1:
                    logging.warn("Couldn't determine a line id for service code %s"
                                 "with first stop %s",
                        service_code,
                        first_stop_name)
                    continue

                # Check for duplicate trips by looking for TripStops on the same
                # line starting with the stop_time at the same station
                dupe_tripstop_list = TripStop.objects.filter(
                    trip__line__id=line_id,
                    station=atcocode_station_map[int(journey_pattern_timing_link_list[0][0])],
                    departure_time=departure_time_dt)
                if dupe_tripstop_list:
                    logging.info("Not inserting trip as duplicate already exists"
                                 "(Trip: %s with TripStop: %s at %s)",
                        dupe_tripstop_list[0].trip.id,
                        dupe_tripstop_list[0].station.short_name(),
                        dupe_tripstop_list[0].departure_time)
                    continue
                else:
                    new_trip = Trip(timetable_type='WD',
                        line=Line.objects.get(id=line_id))
                    new_trip.save()
                    logging.info("Created New Trip (%s) [service code %s] on line %s"
                                 "(%s to %s), running on %s",
                        new_trip.id,
                        service_code,
                        new_trip.line.id,
                        service_origin,
                        service_dest,
                        ", ".join(operating_days))

                create_tripstops_and_segments(journey_pattern_timing_link_list,
                    atcocode_station_map, new_trip, departure_time_dt)

def populate(transxchange_file, service_list):
    """
    Assumes empty tables, but should not add any repeat objects if
     run over a populated database
    """
    # TODO - build lines automatically using Service->Lines->Line->LineName and possibly cross-check with Service->Description
    context = etree.parse(transxchange_file)

    # Map transxchange atcocode to station object
    a_s_map = extract_stations(context)
    create_interchange_stations(transxchange_constants.INTERCHANGE_STATION_MAP)
    jps_dict = extract_journey_pattern_sections(context)
    vj_dict = extract_vehicle_journies(context)
    create_trips(context, service_list, vj_dict, a_s_map, jps_dict)

if __name__ == '__main__':
    populate(os.path.join(PATH_TO_DATA, "505_20090828.xml"), transxchange_constants.TEST_SERVICES)

