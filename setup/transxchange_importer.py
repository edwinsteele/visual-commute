from lxml import etree
from copy import deepcopy
import datetime, sqlite3

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

interchangeStationMap = {
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

atcoStopMap = {}
atcoStationCodeMap = {}
journeyPatternSectionDict = {}
vehicleJourneyDict = {}
lineDict = {}

allTables = ("Station", "Trip", "Line", "TripStop", "Segment", "InterchangeStation")

conn = sqlite3.connect(os.path.join(PATH_TO_DATA, "visual-commute.db"))
conn.row_factory = sqlite3.Row

# Drop old, populated tables
for tableToDrop in allTables:
    with conn:
        conn.execute("DROP TABLE IF EXISTS %s" % tableToDrop)

# Setup the clean tables
with open("./createTables.sql", "r") as f:
    databaseStructureSql = f.read()
    with conn:
        conn.executescript(databaseStructureSql)

# Parse the timetable data
context = etree.parse(os.path.join(PATH_TO_DATA, "505_20090828.xml"))

# Find the stop points
xpStopPoint = etree.XPath("//T:StopPoint", namespaces=NSMAP)
xpAtcoCode = etree.XPath("//T:AtcoCode", namespaces=NSMAP)
xpCommonName = etree.XPath("//T:Descriptor//T:CommonName", namespaces=NSMAP)
xpLon = etree.XPath("//T:Place//T:Location//T:Longitude", namespaces=NSMAP)
xpLat = etree.XPath("//T:Place//T:Location//T:Latitude", namespaces=NSMAP)

for elem in xpStopPoint(context):
    stopPoint = deepcopy(elem)
    atcoCode = int(xpAtcoCode(stopPoint)[0].text)
    stopName = xpCommonName(stopPoint)[0].text
    lon = float(xpLon(stopPoint)[0].text)
    lat = float(xpLat(stopPoint)[0].text)
    atcoStopMap[atcoCode] = (stopName, lon, lat)
    stopFindSql = "SELECT stationId from Station WHERE stationName = ?"
    oneRow = conn.execute(stopFindSql, (stopName,)).fetchone()
    if oneRow and oneRow["stationId"]:
        stationId = oneRow["stationId"]
    else:
        stopInsertSql = "INSERT INTO Station VALUES (NULL, ?, ?, ?);"
        with conn:
            stationId = conn.execute(stopInsertSql, (stopName, lon, lat)).lastrowid
        # Insert into interchange table here too, while we've got stationId
        if interchangeStationMap.has_key(stopName):
            interchangeInsertSql = "INSERT INTO InterchangeStation VALUES (?, ?)"
            lineIds = interchangeStationMap[stopName]
            print "Interchange station: %s on lines: %s" % (stopName, lineIds)
            with conn:
                 for lineId in lineIds:
                     conn.execute(interchangeInsertSql, (lineId, stationId))

    atcoStationCodeMap[atcoCode] = stationId

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

    journeyPatternSectionDict[journeyPatternSectionId] = journeyPatternTimingLinkList
    #print "JPS id: %s. From %s (%s) to %s (%s)" % (journeyPatternSectionId, fromStop, atcoStopMap[fromStop][0], toStop, atcoStopMap[toStop][0])


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
    vehicleJourneyDict[vehicleJourneyId] = (serviceRefId, lineRefId, journeyPatternRefId, depTime)

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
            serviceRefId, lineRefId, journeyPatternRefId, depTime = vehicleJourneyDict[vehicleJourneyId]
            depTimeDateTime = datetime.datetime.strptime(depTime, "%H:%M:%S")
            # FIXME - we can't handle time comparisons when the system rolls
            #  over past midnight, so for the sake of testing, let's drop any
            #  trip that starts after 8pm
            if depTimeDateTime.time() > datetime.time(hour=20, minute=0):
                print "Bailing on [service code %s] on line %s (%s to %s) because it starts late (%s)" % \
                    (serviceCode, lineId, serviceOrig, serviceDest, depTimeDateTime.strftime("%H:%M"))
                continue

            journeyPatternTimingLinkList = journeyPatternSectionDict[journeyPatternRefId]
            # The first stop is indicative of which direction the train is
            #  going and thus which line it is on. This info isn't provided
            #  in the transxchange data as far as I can tell
            firstStopName = atcoStopMap[int(journeyPatternTimingLinkList[0][0])][0]
            lineId = -1
            if (serviceCode in ALL_BLUE_MOUNTAINS_SERVICES):
                if firstStopName in LITHGOW_TO_CENTRAL_ORIGINS:
                    lineId = 1
                elif firstStopName in CENTRAL_TO_LITHGOW_ORIGINS:
                    lineId = 2
                else:
                    print "Unable to determine trip direction because %s is not a registered Origin on Blue Mountains line" % (firstStopName,)

            elif (serviceCode in YELLOW_LINE_SERVICES):
                if firstStopName in PENRITH_TO_HORNSBY_ORIGINS:
                    lineId = 3
                elif firstStopName in HORNSBY_TO_PENRITH_ORIGINS:
                    lineId = 4
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
Trip.lineId = ? AND
TripStop.stationId = ? AND
depTime = ?
"""
            dupeTrip = conn.execute(dupeTripStopSql, (lineId, atcoStationCodeMap[int(journeyPatternTimingLinkList[0][0])], depTimeDateTime.strftime("%H:%M"))).fetchone()
            if dupeTrip:
                print "== Not inserting trip as duplicate already exists (Trip: %s with TripStop: %s at %s)" % \
                    (dupeTrip["tripId"], dupeTrip["tripStopId"], dupeTrip["depTime"])
                continue

            tripSql = "INSERT INTO Trip VALUES (NULL, ?, 'WD')"
            with conn:
                newTripId = conn.execute(tripSql, (lineId,)).lastrowid

            print "New Trip (%s) [service code %s] on line %s (%s to %s), running on %s" % \
                (newTripId, serviceCode, lineId, serviceOrig, serviceDest, ", ".join(operatingDays))

            stopTime = depTimeDateTime
            fromTripStopId = None
            for fromStopId, toStopId, runTime in journeyPatternTimingLinkList:
                if fromTripStopId == None:
                    # This is the first TripStop point in the trip
                    fromStop = atcoStopMap[int(fromStopId)]
                    fromStopSqlId = atcoStationCodeMap[int(fromStopId)]
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
                toStop = atcoStopMap[int(toStopId)]
                toStopSqlId = atcoStationCodeMap[int(toStopId)]
                tripStopSql = "INSERT INTO TripStop VALUES (NULL, ?, ?, ?)"
                with conn:
                    toTripStopId = conn.execute(tripStopSql, (newTripId, toStopSqlId, stopTime.strftime("%H:%M"))).lastrowid
                    #print "# Added TripStop at %s at %s with tripStopId %s" % (toStop[0], stopTime.strftime("%H:%M"), toTripStopId)

                segmentSql = "INSERT INTO SEGMENT VALUES (NULL, ?, ?)"
                with conn:
                    conn.execute(segmentSql, (fromTripStopId, toTripStopId))
                    #print "# Added Segment between TripStops %s and %s" % (fromTripStopId, toTripStopId)

                fromTripStopId = toTripStopId

