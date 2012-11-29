from lxml import etree
from copy import deepcopy
import datetime, os, time

from vcapp.models import InterchangeStation, Line, Station, Trip

PATH_TO_DATA="../data"

TRANSXCHANGE_NAMESPACE = "http://www.transxchange.org.uk/"
TRANSXCHANGE = "{%s}" % TRANSXCHANGE_NAMESPACE

NSMAP = {"T" : TRANSXCHANGE_NAMESPACE}

ALL_BLUE_MOUNTAINS_SERVICES = range(9833,9848)
INBOUND_BLUE_MOUNTAINS_SERVICES = (9833, 9835, 9838, 9840, 9841, 9843, 9844, 9847)
YELLOW_LINE_SERVICES= [9901, 9903, 9904, 9906, 9908, 9909, 9911, 9964, 9965, 9966, 9967, 9968, 9969, 9972, 9973, 9974]
# 9847 has a hornsby to springwood service thrown in for good measure :-(
#INBOUND_BLUE_MOUNTAINS_SERVICES = (9833, 9835, 9838, 9840, 9841, 9843, 9844)
TEST = (9843,)

SERVICE_LIST = YELLOW_LINE_SERVICES + ALL_BLUE_MOUNTAINS_SERVICES
#SERVICE_LIST = ALL_BLUE_MOUNTAINS_SERVICES

LITHGOW_TO_CENTRAL_ORIGINS = ("Lithgow Station", "Mount Victoria Station", "Katoomba Station", "Springwood Station")
CENTRAL_TO_LITHGOW_ORIGINS = ("Central Station", "Hornsby Station",)
PENRITH_TO_HORNSBY_ORIGINS = ("Emu Plains Station", "Penrith Station","Richmond Station", "Blacktown Station", "Quakers Hill Station")
HORNSBY_TO_PENRITH_ORIGINS = ("Berowra Station", "Hornsby Station", "Gordon Station", "North Sydney Station", "Wyong Station", "Lindfield Station")

# List the stations that are on each line
# TODO: Generate this automatically?
interchange_station_map = {
    "Emu Plains Station":(1,2,3,4),
    "Penrith Station":(1,2,3,4),
    "Blacktown Station":(1,2,3,4),
    "Westmead Station":(1,2,3,4),
    "Parramatta Station":(1,2,3,4),
    "Granville Station":(1,2,3,4),
    "Lidcombe Station":(1,2,3,4),
    "Strathfield Station":(1,2,3,4),
    "Burwood Station":(3,4),
    "Redfern Station":(1,2,3,4),
    "Central Station":(1,2,3,4),
    "Town Hall Station":(3,4),
    "Wynyard Station":(3,4),
    "North Sydney Station":(3,4)
}

atco_stop_map = {}
atco_stationcode_map = {}
journey_pattern_section_dict = {}
vehicle_journey_map = {}
line_dict = {}

# TODO - how do I programatically drop the tables (and then load initial data)?

# Parse the timetable data
context = etree.parse(os.path.join(PATH_TO_DATA, "505_20090828.xml"))

# Find the stop points
xp_stop_point = etree.XPath("//T:StopPoint", namespaces=NSMAP)
xp_atco_code = etree.XPath("//T:AtcoCode", namespaces=NSMAP)
xp_common_name = etree.XPath("//T:Descriptor//T:CommonName", namespaces=NSMAP)
xp_lon = etree.XPath("//T:Place//T:Location//T:Longitude", namespaces=NSMAP)
xp_lat = etree.XPath("//T:Place//T:Location//T:Latitude", namespaces=NSMAP)

created_station_count = 0
start_time = time.time()
for elem in xp_stop_point(context):
    stop_point = deepcopy(elem)
    atco_code = int(xp_atco_code(stop_point)[0].text)
    stop_name = xp_common_name(stop_point)[0].text
    lon = float(xp_lon(stop_point)[0].text)
    lat = float(xp_lat(stop_point)[0].text)
    atco_stop_map[atco_code] = (stop_name, lon, lat)
    # TODO - it's possible that we don't need stations in our initial_data as this script will populate
    station, created = Station.objects.get_or_create(station_name=stop_name, lon=lon, lat=lat)
    if created:
        created_station_count += 1

    atco_stationcode_map[atco_code] = station

print "Created %s stations in %.2f secs" % (created_station_count, time.time() - start_time)

interchange_station_count = 0
interchange_relationship_count = 0

start_time = time.time()
# Setup Interchange Stations
for station in Station.objects.all():
    if station.station_name in interchange_station_map:
        interchange_station_count += 0
        for line_id in interchange_station_map[station.station_name]:
            InterchangeStation.objects.create(station=station,
                line=Line.objects.get(line_id=line_id))
            interchange_relationship_count += 0


print "Created %s interchange stations and %s relationships in %.2f secs" % \
    (interchange_station_count, interchange_relationship_count, time.time() - start_time)

# Journey Pattern Sections
#  (which contain 1 or more Journey Pattern Timing Links)
xp_journey_pattern_section = etree.XPath("//T:JourneyPatternSection", namespaces=NSMAP)
xp_from_stop_point = etree.XPath("//T:From//T:StopPointRef", namespaces=NSMAP)
xp_to_stop_point = etree.XPath("//T:To//T:StopPointRef", namespaces=NSMAP)
xp_run_time = etree.XPath("//T:RunTime", namespaces=NSMAP)
xp_journey_pattern_timing_link = etree.XPath("//T:JourneyPatternTimingLink", namespaces=NSMAP)

journey_pattern_section_count = 0
journey_pattern_timing_link_count = 0

start_time = time.time()
for elem in xp_journey_pattern_section(context):
    journey_pattern_section = deepcopy(elem)
    journey_pattern_section_id = elem.attrib["id"]
    journey_pattern_timing_link_list = []
    for elem2 in xp_journey_pattern_timing_link(journey_pattern_section):
        journey_pattern_timing_link = deepcopy(elem2)
        from_stop = xp_from_stop_point(journey_pattern_timing_link)[0].text
        to_stop = xp_to_stop_point(journey_pattern_timing_link)[0].text
        # In the format PT[0-9]{1,}M
        run_time = int(xp_run_time(journey_pattern_timing_link)[0].text[2:-1])
        journey_pattern_timing_link_list.append((from_stop, to_stop, run_time))
        journey_pattern_timing_link_count += 1

    journey_pattern_section_dict[journey_pattern_section_id] = \
        journey_pattern_timing_link_list
    journey_pattern_section_count += 1
    #print "JPS id: %s. From %s (%s) to %s (%s)" % \
    # (journey_pattern_sectionId, from_stop, atco_stop_map[from_stop][0], to_stop, atco_stop_map[to_stop][0])

print "Found %s journey pattern timing links with %s sections in %.2f secs" % \
      (journey_pattern_timing_link_count,
       journey_pattern_section_count,
       time.time() - start_time)

# Vehicle Journey
#  (which has a single Journey Pattern Section reference)
#  (which has a departure time)
#  (which has a line reference and service reference)

xp_vehicle_journey = etree.XPath("//T:VehicleJourney", namespaces=NSMAP)
xp_vehicle_journey_code = etree.XPath("//T:VehicleJourneyCode", namespaces=NSMAP)
xp_journey_pattern_ref = etree.XPath("//T:JourneyPatternRef", namespaces=NSMAP)
xp_line_ref = etree.XPath("//T:LineRef", namespaces=NSMAP)
xp_service_ref = etree.XPath("//T:ServiceRef", namespaces=NSMAP)
xp_dep_time = etree.XPath("//T:DepartureTime", namespaces=NSMAP)
# Do I need the Direction element?

start_time = time.time()
vehicle_journey_count = 0
for e in xp_vehicle_journey(context):
    vj = deepcopy(e)
    vehicle_journey_id = xp_vehicle_journey_code(vj)[0].text
    journey_pattern_ref_id = xp_journey_pattern_ref(vj)[0].text
    line_ref_id = int(xp_line_ref(vj)[0].text)
    service_ref_id = xp_service_ref(vj)[0].text
    departure_time = xp_dep_time(vj)[0].text
    vehicle_journey_map[vehicle_journey_id] = (service_ref_id, line_ref_id, journey_pattern_ref_id, departure_time)
    vehicle_journey_count += 1

print "Found %s vehicle journies in %.2f secs" % \
      (vehicle_journey_count, time.time() - start_time)

# Service
#  (which contains a list of Journey Pattern Section references)
#  (which has an origin and destination)
#  (which lists the operating period (which days of the week)

xp_service = etree.XPath("//T:Service", namespaces=NSMAP)
xp_service_code = etree.XPath("//T:ServiceCode", namespaces=NSMAP)
xp_service_desc = etree.XPath("//T:Description", namespaces=NSMAP)
xp_service_origin = etree.XPath("//T:StandardService//T:Origin", namespaces=NSMAP)
xp_service_dest = etree.XPath("//T:StandardService//T:Destination", namespaces=NSMAP)
xp_journey_pattern = etree.XPath("//T:StandardService//T:JourneyPattern", namespaces=NSMAP)
xp_days_of_week = etree.XPath("//T:OperatingProfile//T:RegularDayType//T:DaysOfWeek//T:*", namespaces=NSMAP)

for e in xp_service(context):
    s = deepcopy(e)
    service_code = int(xp_service_code(s)[0].text)
    # There are lots of repeated spaces in the service desc
    service_desc = " ".join(xp_service_desc(s)[0].text.split())
    service_origin = xp_service_origin(s)[0].text
    service_dest = xp_service_dest(s)[0].text
    # abbreviated to three letters
    operating_days = [day.tag[len(TRANSXCHANGE):][:3] for day in xp_days_of_week(s)]
    #vehicleJourneyList = []
    if service_code in SERVICE_LIST:
        # FIXME - get the journey pattern section refs from the actual
        #  jpsr element, not from the id of the journey pattern element
        #  even though they're the same in the example file
        for vehicle_journey_ref in xp_journey_pattern(s):
            vehicle_journey_id = vehicle_journey_ref.attrib["id"]
            service_ref_id, line_ref_id, journey_pattern_ref_id, departure_time = \
                vehicle_journey_map[vehicle_journey_id]
            departure_timeDateTime = datetime.datetime.strptime(
                departure_time, "%H:%M:%S")
            # FIXME - we can't handle time comparisons when the system rolls
            #  over past midnight, so for the sake of testing, let's drop any
            #  trip that starts after 8pm
            if departure_timeDateTime.time() > datetime.time(hour=20, minute=0):
                print "Bailing on service code %s (%s to %s) because it starts late (%s)" %\
                      (service_code,
                       service_origin,
                       service_dest,
                       departure_timeDateTime.strftime("%H:%M"))
                continue

            journey_pattern_timing_link_list = \
                journey_pattern_section_dict[journey_pattern_ref_id]
            # The first stop is indicative of which direction the train is
            #  going and thus which line it is on. This info isn't provided
            #  in the transxchange data as far as I can tell
            first_stop_name = atco_stop_map[int(journey_pattern_timing_link_list[0][0])][0]
            line_id = -1
            if (service_code in ALL_BLUE_MOUNTAINS_SERVICES):
                if first_stop_name in LITHGOW_TO_CENTRAL_ORIGINS:
                    line_id = 1
                elif first_stop_name in CENTRAL_TO_LITHGOW_ORIGINS:
                    line_id = 2
                else:
                    print "Unable to determine trip direction because %s is not"\
                    "a registered Origin on Blue Mountains line" % (first_stop_name,)

            elif (service_code in YELLOW_LINE_SERVICES):
                if first_stop_name in PENRITH_TO_HORNSBY_ORIGINS:
                    line_id = 3
                elif first_stop_name in HORNSBY_TO_PENRITH_ORIGINS:
                    line_id = 4
                else:
                    print "Unable to determine trip direction because %s is not"\
                    "a registered Origin on the Yellow Line" % (first_stop_name,)

            else:
                print "Unable to determine trip direction because %s is not a"\
                "registered Origin" % (first_stop_name,)
                print "Trip data follows:"

            # Check for duplicate trips by looking for TripStops on the same line starting with the stopTime at the same station
            dupeTripStopSql = """
SELECT TripStop.tripId, TripStop.tripStopId, departure_time FROM TripStop, Trip
WHERE
TripStop.tripId = Trip.tripId AND
Trip.line_id = ? AND
TripStop.station_id = ? AND
departure_time = ?
"""
            dupeTrip = conn.execute(dupeTripStopSql, (line_id, atco_stationcode_map[int(journey_pattern_timing_link_list[0][0])], departure_timeDateTime.strftime("%H:%M"))).fetchone()
            if dupeTrip:
                print "== Not inserting trip as duplicate already exists (Trip: %s with TripStop: %s at %s)" %\
                      (dupeTrip["tripId"], dupeTrip["tripStopId"], dupeTrip["departure_time"])
                continue

            tripSql = "INSERT INTO Trip VALUES (NULL, ?, 'WD')"
            with conn:
                newTripId = conn.execute(tripSql, (line_id,)).lastrowid

            print "New Trip (%s) [service code %s] on line %s (%s to %s), running on %s" %\
                  (newTripId, service_code, line_id, service_origin, service_dest, ", ".join(operating_days))

            stopTime = departure_timeDateTime
            g = None
            for from_stopId, to_stopId, run_time in journey_pattern_timing_link_list:
                if g == None:
                    # This is the first TripStop point in the trip
                    from_stop = atco_stop_map[int(from_stopId)]
                    from_stopSqlId = atco_stationcode_map[int(from_stopId)]
                    tripStopSql = "INSERT INTO TripStop VALUES (NULL, ?, ?, ?)"
                    with conn:
                        g = conn.execute(tripStopSql, (newTripId, from_stopSqlId, stopTime.strftime("%H:%M"))).lastrowid
                        print "# Added First TripStop at %s at %s with tripStopId %s" % (from_stop[0], stopTime.strftime("%H:%M"), g)
                else:
                    # Nothing to do. The from_stop from this jptl is always
                    #  the same as the to_stop from the previous jptl
                    pass

                run_timeTimeDelta = datetime.timedelta(minutes=run_time)
                stopTime = stopTime + run_timeTimeDelta
                to_stop = atco_stop_map[int(to_stopId)]
                to_stopSqlId = atco_stationcode_map[int(to_stopId)]
                tripStopSql = "INSERT INTO TripStop VALUES (NULL, ?, ?, ?)"
                with conn:
                    to_tripstop_id = conn.execute(tripStopSql, (newTripId, to_stopSqlId, stopTime.strftime("%H:%M"))).lastrowid
                    #print "# Added TripStop at %s at %s with tripStopId %s" % (to_stop[0], stopTime.strftime("%H:%M"), to_tripstop_id)

                segmentSql = "INSERT INTO SEGMENT VALUES (NULL, ?, ?)"
                with conn:
                    conn.execute(segmentSql, (g, to_tripstop_id))
                    #print "# Added Segment between TripStops %s and %s" % (g, to_tripstop_id)

                g = to_tripstop_id

