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

print "Created %s stations" % (created_station_count,)

interchange_station_count = 0
interchange_relationship_count = 0

# Setup Interchange Stations
for station in Station.objects.all():
    if station.station_name in interchange_station_map:
        interchange_station_count += 0
        for line_id in interchange_station_map[station.station_name]:
            InterchangeStation.objects.create(station=station,
                line=Line.objects.get(line_id=line_id))
            interchange_relationship_count += 0


print "Created %s interchange stations and %s relationships" % \
    (interchange_station_count, interchange_relationship_count)

die

# Journey Pattern Sections
#  (which contain 1 or more Journey Pattern Timing Links)
xpJourneyPatternSection = etree.XPath("//T:JourneyPatternSection", namespaces=NSMAP)
xpFromStopPoint = etree.XPath("//T:From//T:StopPointRef", namespaces=NSMAP)
xpToStopPoint = etree.XPath("//T:To//T:StopPointRef", namespaces=NSMAP)
xpRunTime = etree.XPath("//T:RunTime", namespaces=NSMAP)
xpJourneyPatternTimingLink = etree.XPath("//T:JourneyPatternTimingLink", namespaces=NSMAP)

for elem in xpJourneyPatternSection(context):
    journeyPatternSection = deepcopy(elem)
    journeyPatternSectionId = elem.attrib["id"]
    journeyPatternTimingLinkList = []
    for elem2 in xpJourneyPatternTimingLink(journeyPatternSection):
        journeyPatternTimingLink = deepcopy(elem2)
        fromStop = xpFromStopPoint(journeyPatternTimingLink)[0].text
        toStop = xpToStopPoint(journeyPatternTimingLink)[0].text
        # In the format PT[0-9]{1,}M
        runTime = int(xpRunTime(journeyPatternTimingLink)[0].text[2:-1])
        journeyPatternTimingLinkList.append((fromStop, toStop, runTime))

    journey_pattern_section_dict[journeyPatternSectionId] = journeyPatternTimingLinkList
    #print "JPS id: %s. From %s (%s) to %s (%s)" % (journeyPatternSectionId, fromStop, atco_stop_map[fromStop][0], toStop, atco_stop_map[toStop][0])


# Vehicle Journey
#  (which has a single Journey Pattern Section reference)
#  (which has a departure time)
#  (which has a line reference and service reference)

xpVehicleJourney = etree.XPath("//T:VehicleJourney", namespaces=NSMAP)
xpVehicleJourneyCode = etree.XPath("//T:VehicleJourneyCode", namespaces=NSMAP)
xpJourneyPatternRef = etree.XPath("//T:JourneyPatternRef", namespaces=NSMAP)
xpLineRef = etree.XPath("//T:LineRef", namespaces=NSMAP)
xpServiceRef = etree.XPath("//T:ServiceRef", namespaces=NSMAP)
xpDepTime = etree.XPath("//T:DepartureTime", namespaces=NSMAP)
# Do I need the Direction element?

for e in xpVehicleJourney(context):
    vj = deepcopy(e)
    vehicleJourneyId = xpVehicleJourneyCode(vj)[0].text
    journeyPatternRefId = xpJourneyPatternRef(vj)[0].text
    lineRefId = int(xpLineRef(vj)[0].text)
    serviceRefId = xpServiceRef(vj)[0].text
    depTime = xpDepTime(vj)[0].text
    vehicle_journey_map[vehicleJourneyId] = (serviceRefId, lineRefId, journeyPatternRefId, depTime)

# Service
#  (which contains a list of Journey Pattern Section references)
#  (which has an origin and destination)
#  (which lists the operating period (which days of the week)

xpService = etree.XPath("//T:Service", namespaces=NSMAP)
xpServiceCode = etree.XPath("//T:ServiceCode", namespaces=NSMAP)
xpServiceDesc = etree.XPath("//T:Description", namespaces=NSMAP)
xpServiceOrig = etree.XPath("//T:StandardService//T:Origin", namespaces=NSMAP)
xpServiceDest = etree.XPath("//T:StandardService//T:Destination", namespaces=NSMAP)
xpJourneyPattern = etree.XPath("//T:StandardService//T:JourneyPattern", namespaces=NSMAP)
xpDaysOfWeek = etree.XPath("//T:OperatingProfile//T:RegularDayType//T:DaysOfWeek//T:*", namespaces=NSMAP)

for e in xpService(context):
    s = deepcopy(e)
    serviceCode = int(xpServiceCode(s)[0].text)
    # There are lots of repeated spaces in the service desc
    serviceDesc = " ".join(xpServiceDesc(s)[0].text.split())
    serviceOrig = xpServiceOrig(s)[0].text
    serviceDest = xpServiceDest(s)[0].text
    # abbreviated to three letters
    operatingDays = [day.tag[len(TRANSXCHANGE):][:3] for day in xpDaysOfWeek(s)]
    #vehicleJourneyList = []
    if serviceCode in SERVICE_LIST:
        # FIXME - get the journey pattern section refs from the actual
        #  jpsr element, not from the id of the journey pattern element
        #  even though they're the same in the example file
        for vehicleJourneyRef in xpJourneyPattern(s):
            vehicleJourneyId = vehicleJourneyRef.attrib["id"]
            serviceRefId, lineRefId, journeyPatternRefId, depTime = vehicle_journey_map[vehicleJourneyId]
            depTimeDateTime = datetime.datetime.strptime(depTime, "%H:%M:%S")
            # FIXME - we can't handle time comparisons when the system rolls
            #  over past midnight, so for the sake of testing, let's drop any
            #  trip that starts after 8pm
            if depTimeDateTime.time() > datetime.time(hour=20, minute=0):
                print "Bailing on [service code %s] on line %s (%s to %s) because it starts late (%s)" %\
                      (serviceCode, line_id, serviceOrig, serviceDest, depTimeDateTime.strftime("%H:%M"))
                continue

            journeyPatternTimingLinkList = journey_pattern_section_dict[journeyPatternRefId]
            # The first stop is indicative of which direction the train is
            #  going and thus which line it is on. This info isn't provided
            #  in the transxchange data as far as I can tell
            firstStopName = atco_stop_map[int(journeyPatternTimingLinkList[0][0])][0]
            line_id = -1
            if (serviceCode in ALL_BLUE_MOUNTAINS_SERVICES):
                if firstStopName in LITHGOW_TO_CENTRAL_ORIGINS:
                    line_id = 1
                elif firstStopName in CENTRAL_TO_LITHGOW_ORIGINS:
                    line_id = 2
                else:
                    print "Unable to determine trip direction because %s is not a registered Origin on Blue Mountains line" % (firstStopName,)

            elif (serviceCode in YELLOW_LINE_SERVICES):
                if firstStopName in PENRITH_TO_HORNSBY_ORIGINS:
                    line_id = 3
                elif firstStopName in HORNSBY_TO_PENRITH_ORIGINS:
                    line_id = 4
                else:
                    print "Unable to determine trip direction because %s is not a registered Origin on the Yellow Line" % (firstStopName,)

            else:
                print "Unable to determine trip direction because %s is not a registered Origin" % (firstStopName,)
                print "Trip data follows:"

            # Check for duplicate trips by looking for TripStops on the same line starting with the stopTime at the same station
            dupeTripStopSql = """
SELECT TripStop.tripId, TripStop.tripStopId, depTime FROM TripStop, Trip
WHERE
TripStop.tripId = Trip.tripId AND
Trip.line_id = ? AND
TripStop.station_id = ? AND
depTime = ?
"""
            dupeTrip = conn.execute(dupeTripStopSql, (line_id, atco_stationcode_map[int(journeyPatternTimingLinkList[0][0])], depTimeDateTime.strftime("%H:%M"))).fetchone()
            if dupeTrip:
                print "== Not inserting trip as duplicate already exists (Trip: %s with TripStop: %s at %s)" %\
                      (dupeTrip["tripId"], dupeTrip["tripStopId"], dupeTrip["depTime"])
                continue

            tripSql = "INSERT INTO Trip VALUES (NULL, ?, 'WD')"
            with conn:
                newTripId = conn.execute(tripSql, (line_id,)).lastrowid

            print "New Trip (%s) [service code %s] on line %s (%s to %s), running on %s" %\
                  (newTripId, serviceCode, line_id, serviceOrig, serviceDest, ", ".join(operatingDays))

            stopTime = depTimeDateTime
            fromTripStopId = None
            for fromStopId, toStopId, runTime in journeyPatternTimingLinkList:
                if fromTripStopId == None:
                    # This is the first TripStop point in the trip
                    fromStop = atco_stop_map[int(fromStopId)]
                    fromStopSqlId = atco_stationcode_map[int(fromStopId)]
                    tripStopSql = "INSERT INTO TripStop VALUES (NULL, ?, ?, ?)"
                    with conn:
                        fromTripStopId = conn.execute(tripStopSql, (newTripId, fromStopSqlId, stopTime.strftime("%H:%M"))).lastrowid
                        print "# Added First TripStop at %s at %s with tripStopId %s" % (fromStop[0], stopTime.strftime("%H:%M"), fromTripStopId)
                else:
                    # Nothing to do. The fromStop from this jptl is always
                    #  the same as the toStop from the previous jptl
                    pass

                runTimeTimeDelta = datetime.timedelta(minutes=runTime)
                stopTime = stopTime + runTimeTimeDelta
                toStop = atco_stop_map[int(toStopId)]
                toStopSqlId = atco_stationcode_map[int(toStopId)]
                tripStopSql = "INSERT INTO TripStop VALUES (NULL, ?, ?, ?)"
                with conn:
                    toTripStopId = conn.execute(tripStopSql, (newTripId, toStopSqlId, stopTime.strftime("%H:%M"))).lastrowid
                    #print "# Added TripStop at %s at %s with tripStopId %s" % (toStop[0], stopTime.strftime("%H:%M"), toTripStopId)

                segmentSql = "INSERT INTO SEGMENT VALUES (NULL, ?, ?)"
                with conn:
                    conn.execute(segmentSql, (fromTripStopId, toTripStopId))
                    #print "# Added Segment between TripStops %s and %s" % (fromTripStopId, toTripStopId)

                fromTripStopId = toTripStopId

