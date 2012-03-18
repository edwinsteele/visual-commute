# LATITUDE is NORTH-SOUTH e.g. 33 deg SOUTH (Sydney)
# LONGITUDE is EAST-WEST e.g. 151 deg EAST (Sydney)

from optparse import OptionParser
import datetime, math, sqlite3, sys
import networkx

#http://nodedangles.wordpress.com/2010/05/16/measuring-distance-from-a-point-to-a-line-segment/

# Options
debug = None

dbConn = None
def getDbConn():
    global dbConn
    if dbConn == None:
        dbConn = sqlite3.connect('../data/visual-commute.db')
        dbConn.row_factory = sqlite3.Row

    return dbConn

def lineMagnitude (x1, y1, x2, y2):
    return math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1), 2))

#Calc minimum distance from a point and a line segment (i.e. consecutive vertices in a polyline).
def distancePointLine (px, py, x1, y1, x2, y2):
    #http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba
    LineMag = lineMagnitude(x1, y1, x2, y2)

    if LineMag < 0.00000001:
        dpl = 9999
        return dpl

    u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
    u = u1 / (LineMag * LineMag)

    if (u < 0.00001) or (u > 1):
        #// closest point does not fall within the line segment, take the shorter distance
        #// to an endpoint
        ix = lineMagnitude(px, py, x1, y1)
        iy = lineMagnitude(px, py, x2, y2)
        if ix > iy:
            dpl = iy
        else:
            dpl = ix
    else:
        # Intersecting point is on the line, use the formula
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        dpl = lineMagnitude(px, py, ix, iy)

    return dpl


class PointInSpaceTime(object):
    def __init__(self, name, lat, lon, timeOfDay):
        self.name = name
        self.lat = lat
        self.lon = lon
        # datetime.time object
        self.timeOfDay = timeOfDay

    def __str__(self):
        return "%s - lon: %s (E-W) lat: %s (N-S) at time: %s" % (self.name, self.lon, self.lat, self.timeOfDay)

    def distanceFrom(self, location):
        return lineMagnitude(x1=self.lon, y1=self.lat, x2=location.lon, y2=location.lat)

    def shortName(self):
        # Removes the trailing " Station", at least for now. More options possible
        return self.name.rsplit(" ", 1)[0]

    def findClosestSegment(self):
        # Find possible segments from the db to avoid constructing segment
        #  objects for EVERYTHING in the db. If we don't get a match here
        #  within an acceptable threshold,
        #  perhaps because the train is late, we'll have to do a wider search
        conn = getDbConn()
        segmentFinderSql = """
        select segmentId, dep.tripId, d.stationName as depStn, d.lat as depLat, d.lon as depLon, dep.depTime as depDepTime, a.stationName as arvStn, a.lat as arvLat, a.lon as arvLon, arv.depTime as arvDepTime
        from Station d, Station a, TripStop dep, TripStop arv, Segment
        where
        Segment.depTripStopId = dep.tripStopId and
        Segment.arvTripStopId = arv.tripStopId and
        d.stationId = dep.stationId and
        a.stationId = arv.stationId and
        a`ep.depTime <= ? and
        arv.depTime >= ?;
        """
        closestSegment = None
        closestDistance = 9999
        for row in conn.execute(segmentFinderSql, (self.timeOfDay.strftime("%H:%M"), \
                self.timeOfDay.strftime("%H:%M"))):
            dt = datetime.datetime.strptime(row["depDepTime"], "%H:%M")
            startStation = PointInSpaceTime(row["depStn"], \
                lat=row["depLat"], lon=row["depLon"], \
                timeOfDay=datetime.time(dt.hour, dt.minute))
            dt = datetime.datetime.strptime(row["arvDepTime"], "%H:%M")
            endStation = PointInSpaceTime(row["arvStn"], \
                lat=row["arvLat"], lon=row["arvLon"], \
                timeOfDay=datetime.time(dt.hour, dt.minute))
            segment = TimetableSegment(startStation, endStation, None, None)
            d = segment.latLonDistanceFromPoint(lon=self.lon, lat=self.lat)
            if d < closestDistance:
                closestSegment = segment
                closestDistance = d

        return closestSegment

class HTMLdoc(object):
    def __init__(self, htmlFileName):
        self.htmlFile = open(htmlFileName, "w")
        self.htmlFile.write("""
        <HTML>
        <HEAD>
        <TITLE>Visual Timetable</TITLE>
        </HEAD>
        <BODY bgcolor="grey">
        """)

    def write(self, s):
        self.htmlFile.write(s)

    def finalise(self):
        self.write("</BODY></HTML>\n") 
        self.htmlFile.close()

class BaseHTMLDistanceTimeGraph(object):
    MINOR_LINE_MARKER_LEN = 2
    MAJOR_LINE_MARKER_LEN = 4
    TEXT_HEIGHT = 10


    def __init__(self, htmlDoc, tripManager, canvasWidth, canvasHeight):
        self.htmlDoc = htmlDoc
        self.tm = tripManager
        self.canvasWidth = canvasWidth
        self.canvasHeight = canvasHeight
        self.write("""
        <canvas id="%(a)scanvas%(w)sX%(h)s" width="%(w)s" height="%(h)s">
          <p>Your browser doesn't support canvas.</p>
        </canvas>
        <script type="text/javascript">

        function drawSegmentJS(context, departureXPoint, departureYPoint, arrivalXPoint, arrivalYPoint, lineColour, bulletColour)
        {
            context.save();
            context.strokeStyle = lineColour;
            context.fillStyle = bulletColour;
            context.beginPath();
            context.arc(departureXPoint, departureYPoint, 2, 0, 359, true);
            context.closePath();
            context.fill();
            context.beginPath();
            context.moveTo(departureXPoint,departureYPoint);
            context.lineTo(arrivalXPoint,arrivalYPoint);
            context.stroke();
            context.beginPath();
            context.arc(arrivalXPoint, arrivalYPoint, 2, 0, 359, true);
            context.closePath();
            context.fill();
            context.restore();
        }

        function drawHourGridLineJS(context, startX, startY, endX, endY)
        {
            context.save();
            context.strokeStyle = '#ECF1EF';
            context.beginPath();
            context.moveTo(startX, startY);
            context.lineTo(endX, endY);
            context.stroke();
            context.restore();
        }

        var drawingCanvas = document.getElementById('%(a)scanvas%(w)sX%(h)s');
        var ctx = drawingCanvas.getContext('2d');
        ctx.save();
        ctx.fillStyle = '#E6E6E6'
        ctx.fillRect(0,0,%(w)s,%(h)s);
        ctx.restore();
        // Preserve the original context
        ctx.save();
        ctx.font = '%(t)spt Arial';
""" % {"w":self.canvasWidth, "h":self.canvasHeight, "t":self.TEXT_HEIGHT, "a":self.ABBREV})

    def write(self, s):
        self.htmlDoc.write(s)

    def getSegmentLineColour(self, lineId):
        # FIXME - trips may or may not have more than one colour depending
        #  on how many lines make up a trip (or whether a trip can actually
        #  span more than one line
        if lineId in (1,2):
            return "#c5c5c5"
        elif lineId in (3,4):
            return "#fcb514"
        elif lineId == -1:
            # Interchange
            return "black"
        else:
            return "red"
        #return ["red", "orange", "yellow", "green", "blue", "purple"][random.randint(0, 5)]

    def getSegmentBulletColour(self, lineId):
        if lineId in (1,2):
            return "#fcb514"
        elif lineId in (3,4):
            return "#fcb514"
        elif lineId == -1:
            # Interchange
            return "black"
        else:
            return "green"

    def drawTrips(self):
        allTrips = self.tm.getTrips()
        tripDepTimeList = []
        tripArvTimeList = []
        for trip in allTrips:
            ttSegments = trip.getSegments()
            tripDepTimeList.append(ttSegments[0].departurePoint.timeOfDay)
            tripArvTimeList.append(ttSegments[-1].arrivalPoint.timeOfDay)

        minDepTripDelta = self.tm.getMinTimeDeltaFromTimes(tripDepTimeList)
        minArvTripDelta = self.tm.getMinTimeDeltaFromTimes(tripArvTimeList)

        # get a point on the graph to see how many pixels the min deltas cover
        exampleDepPoint = datetime.datetime.combine(datetime.datetime.now(), tripDepTimeList[0])
        minPxBetweenDepPoints = self.datetimeToYPoint(exampleDepPoint + minDepTripDelta) - \
            self.datetimeToYPoint(exampleDepPoint)
        # Text height +1 pixel between means the times would be readable
        if minPxBetweenDepPoints < (self.TEXT_HEIGHT + 1):
            print "Departures are too close (%spx/%s). Use hour axis on the left" % \
                (minPxBetweenDepPoints, minDepTripDelta)
            drawStartLabel = False
        else:
            print "Departures are spaced well (%spx/%s). Use labels on the left" % \
                (minPxBetweenDepPoints, minDepTripDelta)
            drawStartLabel = True

        # get a point on the graph to see how many pixels the min deltas cover
        exampleArvPoint = datetime.datetime.combine(datetime.datetime.now(), tripArvTimeList[0])
        minPxBetweenArvPoints = self.datetimeToYPoint(exampleArvPoint + minArvTripDelta) - \
            self.datetimeToYPoint(exampleArvPoint)
        # Text height +1 pixel between means the times would be readable
        if minPxBetweenArvPoints < (self.TEXT_HEIGHT + 1):
            print "Arrivals are too close (%spx/%s). Use hour axis on the right" % \
                (minPxBetweenArvPoints, minArvTripDelta)
            drawEndLabel = False
        else:
            print "Arrivals are spaced well (%spx/%s). Use labels on the right" % \
                (minPxBetweenArvPoints, minArvTripDelta)
            drawEndLabel = True

        if not drawStartLabel:
            self.drawHourAxis()

        for trip in allTrips:
            self.drawTrip(trip, drawStartLabel, drawEndLabel)
        #[self.drawTrip(trip) for trip in self.tm.getTrips()]

    def finalise(self):
        self.write("""
        ctx.restore();
        </SCRIPT>
        """)

    def drawStationAxis(self):
        self.write("ctx.save();\n")
        self.write("ctx.textAlign = '%s';\n" % (self.STATION_AXIS_TEXTALIGN,))
        self.write("ctx.textBaseline = '%s';\n" % (self.STATION_AXIS_TEXTBASELINE,))
        allStations = self.tm.getAllStationsInTrips()
        if debug:
            stationList = allStations
        else:
            stationList = (allStations[0], allStations[-1])

        for station in stationList:
            self.write("//Station marker: %s\n" % (station.shortName(), ))
            filltextArgs = (station.shortName(),) + self.stationOnStationAxisCoord(station.name)
            self.write("ctx.fillText('%s', %s, %s);\n" % filltextArgs)
        self.write("ctx.restore();\n")

    def drawHourAxis(self):
        #  we need to show up to 59mins past the hour on the x axis
        self.write("ctx.save();\n")
        self.write("ctx.textAlign = '%s';\n" % (self.HOUR_AXIS_TEXTALIGN,))
        self.write("ctx.textBaseline = '%s';\n" % (self.HOUR_AXIS_TEXTBASELINE,))

        # Note that getMaxEndHour is the largest hour e.g if the largest time is 
        #  7:15, then the largest hour is 7. This means that in order to get
        #  the correct scaling factor, we need to add 1 to the maxhour because
        # getMaxEndHour + 1 because the range function isn't inclusive
        for hour in range(self.tm.getMinTripStartHour(), \
            self.tm.getMaxTripEndHour() + 1):
            self.drawHourGridLine(hour, hour)
            self.write("//Hour marker: %s\n" % (hour,))
            filltextArgs = (hour, ) + self.datetimeOnHourAxisCoord(datetime.time(hour))
            self.write("ctx.fillText('%s', %s, %s);\n" % filltextArgs)
            self.drawSubHourMarkers(hour)
        else:
            self.drawHourGridLine(hour + 1, hour + 1)
            self.write("//Hour marker: %s\n" % (hour + 1,))
            filltextArgs = (hour + 1, ) + self.datetimeOnHourAxisCoord(datetime.time(hour + 1))
            self.write("ctx.fillText('%s', %s, %s);\n" % filltextArgs)

        self.write("ctx.restore();\n")


class TimeVertHTMLDistanceTimeGraph(BaseHTMLDistanceTimeGraph):
    # 2 characters wide (ish). Could be smaller if we know we only have 1 char in the hour label
    GRAPH_BORDER_PADDING_LEFT_PX = 35
    GRAPH_BORDER_PADDING_RIGHT_PX = 35
    GRAPH_BORDER_PADDING_TOP_PX = \
        BaseHTMLDistanceTimeGraph.MAJOR_LINE_MARKER_LEN + \
        BaseHTMLDistanceTimeGraph.TEXT_HEIGHT
    GRAPH_BORDER_PADDING_BOTTOM_PX = 5
    ABBREV = "timeVert"

    STATION_AXIS_TEXTALIGN = "left"
    STATION_AXIS_TEXTBASELINE = "bottom"
    HOUR_AXIS_TEXTALIGN = "right"
    HOUR_AXIS_TEXTBASELINE = "middle"
    START_LABEL_TEXTALIGN = "right"
    START_LABEL_TEXTBASELINE = "middle"
    END_LABEL_TEXTALIGN = "left"
    END_LABEL_TEXTBASELINE = "middle"

    def __init__(self, htmlDoc, tripManager, canvasWidth, canvasHeight):
        super(TimeVertHTMLDistanceTimeGraph, self).__init__(htmlDoc, tripManager, canvasWidth, canvasHeight)
        self.stationXAxisPointMap = {}
        self.xPointOfYAxis = self.GRAPH_BORDER_PADDING_LEFT_PX
        self.yPointOfXAxis = self.GRAPH_BORDER_PADDING_TOP_PX

    def drawTrip(self, tripToDraw, drawStartLabel, drawEndLabel):
        ttSegments = tripToDraw.getSegments()
        tripDepPoint = ttSegments[0].departurePoint
        tripArrPoint = ttSegments[-1].arrivalPoint

        if drawStartLabel:
            self.drawStartTimeLabel(tripDepPoint)
        #self.drawSegment(TimetableSegment(tripDepPoint, tripArrPoint))
        for segment in ttSegments:
            self.drawSegment(segment)
        if drawEndLabel:
            self.drawEndTimeLabel(tripArrPoint)

    def drawGraph(self):
        self.drawStationAxis()
        self.drawTrips()

    def datetimeToYPoint(self, dt):
        # Note that maxHour is the largest hour e.g if the largest time is 
        #  7:15, then the largest hour is 7. This means that in order to get
        #  the correct scaling factor, we need to add 1 to the maxhour because
        #  we need to show up to 59mins past the hour on the x axis
        yScalingFactor = (self.canvasHeight - \
                self.GRAPH_BORDER_PADDING_TOP_PX - \
                self.GRAPH_BORDER_PADDING_BOTTOM_PX) / \
                (self.tm.getMaxTripEndHour() + 1 - \
                self.tm.getMinTripStartHour())
        # round (down) it as we probably don't want to do subpixel stuff
        return math.floor(self.GRAPH_BORDER_PADDING_TOP_PX + \
            (dt.hour + dt.minute/60.0 - \
            self.tm.getMinTripStartHour()) * \
            yScalingFactor)

    def stationNameToXPoint(self, sn):
        return self.stationXAxisPointMap[sn]

    def stationOnStationAxisCoord(self, stationName):
        return (self.stationNameToXPoint(stationName), self.yPointOfXAxis)

    def datetimeOnHourAxisCoord(self, dt):
        return (self.xPointOfYAxis, self.datetimeToYPoint(dt))

    def drawStartTimeLabel(self, pist):
        self.write("ctx.save();\n")
        self.write("ctx.textAlign = '%s';\n" % (self.START_LABEL_TEXTALIGN,))
        self.write("ctx.textBaseline = '%s';\n" % (self.START_LABEL_TEXTBASELINE,))
        labelXPoint = self.stationNameToXPoint(pist.name)
        labelYPoint = self.datetimeToYPoint(pist.timeOfDay)
        self.write("//Start label: %s\n" % (pist.timeOfDay.strftime("%H.%M"), ))
        self.write("ctx.fillText('%s ', %s, %s);\n" % \
            (pist.timeOfDay.strftime("%H.%M"), labelXPoint, labelYPoint))
        self.write("ctx.restore();\n")

    def drawEndTimeLabel(self, pist):
        self.write("ctx.save();\n")
        self.write("ctx.textAlign = '%s';\n" % (self.END_LABEL_TEXTALIGN,))
        self.write("ctx.textBaseline = '%s';\n" % (self.END_LABEL_TEXTBASELINE,))
        labelXPoint = self.stationNameToXPoint(pist.name)
        labelYPoint = self.datetimeToYPoint(pist.timeOfDay)
        self.write("//End label: %s\n" % (pist.timeOfDay.strftime("%H.%M"), ))
        self.write("ctx.fillText(' %s', %s, %s);\n" % \
            (pist.timeOfDay.strftime("%H.%M"), labelXPoint, labelYPoint))
        self.write("ctx.restore();\n")

    def drawSubHourMarkers(self, thisHour):
        for minute in range(15, 60, 15):
            self.write("//sub-hour line: %s:%s\n" % (thisHour, minute))
            self.write("ctx.beginPath();\n")
            # TEXT_HEIGH/2 because we want the dot to be aligned with the
            #  middle of the hour label
            self.write("ctx.moveTo(%s,%s);\n" % \
                (self.xPointOfYAxis - (self.TEXT_HEIGHT/2), \
                self.datetimeToYPoint(datetime.time(thisHour, minute))))
            self.write("ctx.lineTo(%s,%s);\n" % \
                (self.xPointOfYAxis - (self.TEXT_HEIGHT/2) - self.MINOR_LINE_MARKER_LEN, \
                self.datetimeToYPoint(datetime.time(thisHour, minute))))
            self.write("ctx.stroke();\n")

    def drawHourGridLine(self, hourLabel, thisHour):
        self.write("//Grid line at %s\n" % (hourLabel,))
        self.write("drawHourGridLineJS(ctx, %s, %s, %s, %s);\n" %
            (self.xPointOfYAxis, \
            self.datetimeToYPoint(datetime.time(thisHour)), \
            self.canvasWidth - self.GRAPH_BORDER_PADDING_RIGHT_PX, \
            self.datetimeToYPoint(datetime.time(thisHour))))

    def populateStationPointMap(self):
        departureStation = None
        allStations = self.tm.getAllStationsInTrips()
        if not allStations:
            assert 0, "Trip Manager can't find any stations on the trips"

        for arrivalStation in allStations:
            if departureStation == None:
                # this is the first station we've come across
                xPointOfDepartureStation = self.xPointOfYAxis
                departureStation = arrivalStation
                continue

            self.stationXAxisPointMap[departureStation.name] = xPointOfDepartureStation
            xScalingFactor = (self.canvasWidth - \
                self.GRAPH_BORDER_PADDING_LEFT_PX - \
                self.GRAPH_BORDER_PADDING_RIGHT_PX)/self.tm.getMaxTripDistance()
            xPointOfArrivalStation = math.floor(xPointOfDepartureStation + \
                (departureStation.distanceFrom(arrivalStation) * \
                xScalingFactor))
            # ready for the next iteration
            xPointOfDepartureStation = xPointOfArrivalStation
            departureStation = arrivalStation
        else:
            self.stationXAxisPointMap[departureStation.name] = xPointOfDepartureStation

    def drawSegment(self, timetableSegment):
        # Note that because this draws a circle at the start and end of the
        #  segment, we're actually drawing circles for all but the first
        #  departure station and the last arrival station twice. meh.
        self.write("//Segment: %s (%s) to %s (%s)\n" % \
            (timetableSegment.departurePoint.name, \
            timetableSegment.departurePoint.timeOfDay, \
            timetableSegment.arrivalPoint.name, \
            timetableSegment.arrivalPoint.timeOfDay))
        departureXPoint = self.stationNameToXPoint(timetableSegment.departurePoint.name)
        arrivalXPoint = self.stationNameToXPoint(timetableSegment.arrivalPoint.name)
        departureYPoint = self.datetimeToYPoint(timetableSegment.departurePoint.timeOfDay)
        arrivalYPoint = self.datetimeToYPoint(timetableSegment.arrivalPoint.timeOfDay)
        self.write("drawSegmentJS(ctx, %s, %s, %s, %s, '%s', '%s');\n" % \
            (departureXPoint, departureYPoint, \
            arrivalXPoint, arrivalYPoint, \
            self.getSegmentLineColour(timetableSegment.lineId), \
            self.getSegmentBulletColour(timetableSegment.lineId)))


class TimetableSegment(object):
    def __init__(self, departurePoint, arrivalPoint, tripId, lineId):
        self.departurePoint = departurePoint
        self.arrivalPoint = arrivalPoint
        self.tripId = tripId
        self.lineId = lineId

    def __str__(self):
        return "Segment from %s (%s) to %s (%s)" % \
            (self.getDepartureName(), self.departurePoint.timeOfDay, \
            self.getArrivalName(), self.arrivalPoint.timeOfDay)

    def getDepartureName(self):
        #return "%s on line %s" % (self.departurePoint.name, self.lineId)
        return "%s on trip %s" % (self.departurePoint.name, self.tripId)

    def getArrivalName(self):
        #return "%s on line %s" % (self.arrivalPoint.name, self.lineId)
        return "%s on trip %s" % (self.arrivalPoint.name, self.tripId)

    def distance(self):
        return self.departurePoint.distanceFrom(self.arrivalPoint)

    def addAsDiGraphEdge(self, dg, ignoreLines):
        if ignoreLines:
            depName = self.departurePoint.name
            arvName = self.arrivalPoint.name
        else:
            depName = self.getDepartureName()
            arvName = self.getArrivalName()

        if depName not in dg:
            dg.add_node(depName, {"tripId":self.tripId, "pist":self.departurePoint})
        if arvName not in dg:
            dg.add_node(arvName, {"tripId":self.tripId, "pist":self.arrivalPoint})
        durationTimeDelta = datetime.datetime.combine(datetime.datetime.today(), self.arrivalPoint.timeOfDay) - \
                datetime.datetime.combine(datetime.datetime.today(), self.departurePoint.timeOfDay)
        edgeWeight = durationTimeDelta.seconds/60
        #print "Adding edge from '%s' to '%s' with weight %s" % (depName, arvName, edgeWeight)
        dg.add_edge(depName, arvName, weight=edgeWeight)

    def latLonDistanceFromPoint(self, lon, lat):
        return distancePointLine(lon, lat, \
                self.departurePoint.lon, self.departurePoint.lat, \
                self.arrivalPoint.lon, self.arrivalPoint.lat)

class Trip(object):
    def __init__(self, tripId, startStation, endStation):
        self._tripId = tripId
        self._startStation = startStation
        self._endStation = endStation
        conn = getDbConn()
        tripStopSql = "select lineId from Trip where tripId = ?"
        self._lineId = conn.execute(tripStopSql, (self._tripId,)).fetchone()["lineId"]
        self._segments = []

    def __str__(self):
        return "Trip (id:%s) from %s to %s, on line %s" % \
            (self._tripId, self._startStation, self._endStation, self._lineId)

    def getTripId(self):
        return self._tripId

    def getSegments(self):
        if self._segments:
            #print "Returning cached segments for tripId %s: %s" % (self._tripId, self._segments)
            return self._segments
        else:
            conn = getDbConn()
            # TODO Should update this to use Segment table.
            tripStopSql = "select stationName, lat, lon, depTime from TripStop, Station where Station.stationId = TripStop.stationId and tripId = ?"
            lastStop = None
            seenStartStation = False
            for row in conn.execute(tripStopSql, (self._tripId,)):
                if row["stationName"] == self._startStation:
                    seenStartStation = True
                if not seenStartStation:
                    # Trip hasn't started yet
                    continue

                dt = datetime.datetime.strptime(row["depTime"], "%H:%M")
                thisStop = PointInSpaceTime(row["stationName"], \
                        lat=row["lat"], lon=row["lon"], \
                        timeOfDay=datetime.time(dt.hour, dt.minute))
                if lastStop:
                    self._segments.append(TimetableSegment(lastStop, thisStop, self._tripId, self._lineId))

                if row["stationName"] == self._endStation:
                    # The journey's over
                    break

                lastStop = thisStop
            return self._segments

    def getTripDistance(self):
        return sum([segment.distance() for segment in self.getSegments()])

    def getStartHour(self):
        return self.getSegments()[0].departurePoint.timeOfDay.hour

    def getEndHour(self):
        return self.getSegments()[-1].arrivalPoint.timeOfDay.hour

class MultiTrip(object):
    def __init__(self):
        self._tripList = []
        self._segList = []

    def __str__(self):
        #return "MultiTrip with %s trips. Ids: %s" % (len(self._tripList), ", ".join([str(t.getTripId()) for t in self._tripList]))
        return "MultiTrip with %s trips (%s)" % (len(self._tripList), ", ".join([str(t) for t in self._tripList]))

    def addTrip(self, tripId, startStation, endStation):
        self._tripList.append(Trip(tripId, startStation, endStation))

    def getSegments(self):
        if self._segList:
            return self._segList
        else:
            segList = []
            lastInterchangeStation = None
            for t in self._tripList:
                #print "Segments for subtrip of multitrip: %s" % (t,)
                segs = t.getSegments()
                if lastInterchangeStation:
                    # We need to indicate waiting time at the interchange
                    segList.append(TimetableSegment(lastInterchangeStation, segs[0].departurePoint, -1, -1))

                segList.extend(segs)
                lastInterchangeStation = segs[-1].arrivalPoint

            return segList

    #XXX Three methods below pinched from Trip. Subclass?
    def getTripDistance(self):
        return sum([segment.distance() for segment in self.getSegments()])
    def getStartHour(self):
        return self.getSegments()[0].departurePoint.timeOfDay.hour
    def getEndHour(self):
        return self.getSegments()[-1].arrivalPoint.timeOfDay.hour


class TripManager(object):

    def __init__(self, startHour, endHour, startStation, endStation):
        # Timeperiod will be something like "from xam to yam", which means
        #  startHour is inclusive, but endHour is not.
        self.startHour = startHour
        self.endHour = endHour
        self.startStation = startStation
        self.endStation = endStation
        self._trips = []
        # While we develop the method
        #self.getTrips = self.getTripsDirect
        self.getTrips = self.getTripsWithChanges

    # Takes a list of datetime.time elements
    def getMinTimeDeltaFromTimes(self, dttList):
        dttList.sort()
        lastTime = None
        # start with the maximum period of time represented on the graph
        #  as the minTripDelta - if there is only one trip on the graph then
        #  the gap calculation should make sense (unlike timedelta.max)
        minTripDelta = datetime.timedelta(hours=int(self.endHour) - int(self.startHour))
        for dtt in dttList:
            thisTime = datetime.timedelta(hours=dtt.hour, \
                    minutes=dtt.minute)
            # Ignore this is the first reading
            # Ignore if it's the same time as this isn't a rendering problem
            if lastTime != None and lastTime != thisTime:
                gap = thisTime - lastTime
                minTripDelta = min(minTripDelta, gap)
            lastTime = thisTime

        return minTripDelta


    def getInterchangePointsOnLine(self, lineId):
        conn = getDbConn()
        interchangeList = []
        interchangeSql = """
        select stationName
        from InterchangeStation, Station
        where
        InterchangeStation.stationId = Station.stationId and
        lineId = ?
        """
        for row in conn.execute(interchangeSql, (lineId,)):
            interchangeList.append(row["stationName"])
        return interchangeList

    def getLinesContainingStation(self, stationName):
        conn = getDbConn()
        lineList = []
        lineSql = """
        select distinct(lineId)
        from Trip t, TripStop ts, Station s
        where
        t.tripId = ts.tripId and
        ts.stationId = s.stationId and
        s.stationName = ?
        """
        for row in conn.execute(lineSql, (stationName,)):
            lineList.append(row["lineId"])
        return lineList

    def getInterchangePoints(self):
        #get a list of lines that include start point (startpoint lines)
        startPointLines = self.getLinesContainingStation(self.startStation)
        #get a list of lines that include the end point (endpoint lines)
        endPointLines = self.getLinesContainingStation(self.endStation)

        startPointLineInterchangePoints = set()
        endPointLineInterchangePoints = set()
        for line in startPointLines:
            [startPointLineInterchangePoints.add(p) for p in self.getInterchangePointsOnLine(line)]
        for line in endPointLines:
            [endPointLineInterchangePoints.add(p) for p in self.getInterchangePointsOnLine(line)]

        return startPointLineInterchangePoints.union(endPointLineInterchangePoints)


    def getTripsWithChanges(self):
        if self._trips:
            return self._trips
        else:
            commonInterchangePoints = self.getInterchangePoints()

            # Map of tripId to a list of trip objects (starting from the start
            #  station and ending at an interchange station)
            startToInterchangeTrips = {}
            for interchangePoint in commonInterchangePoints:
                # Get trips from the start station to the interchange point
                #  (within the time bracket)
                for trip in self._getTripsDirectWithParams(self.startStation, \
                        self.startHour, interchangePoint, self.endHour):
                    # Form a list of trip objects from start station to interchange
                    #  point, keyed by tripId (the same tripId can refer to multiple trips
                    #  in this case as long as its finish station is different)
                    tripsWithTripId = startToInterchangeTrips.get(trip.getTripId(), [])
                    tripsWithTripId.append(trip)
                    startToInterchangeTrips[trip.getTripId()] = tripsWithTripId

            multiTripList = []
            for stitTripId, stitList in startToInterchangeTrips.items():
            #for stitTripId, stitList in [(41, startToInterchangeTrips[41])]:
                dg = networkx.DiGraph()
                # Start and end need to be treated like interchange points in that
                #  we need to get to them regardless of the line (and the node name
                #  includes lines). Start and stop stations don't have a tripId as
                #  they'll be connected to some trip at the same station that does
                #  have a tripId
                dg.add_node(self.startStation, {"tripId":None})
                dg.add_node(self.endStation, {"tripId":None})

                print "Processing Start to Interchange Trips for TripId %s" % (stitTripId,)
                interchangeFormat = "%s Interchange"
                # Add all the interchange points to the graph noting that
                #  Interchange Points don't have a tripId
                [dg.add_node(interchangeFormat % (cip,), {"tripId":None}) for cip in commonInterchangePoints]

                for stit in stitList:
                    for seg in stit.getSegments():
                        # add all the segments to the graph
                        seg.addAsDiGraphEdge(dg, ignoreLines=False)
                        # Shortest path works from start station to end station
                        #  and the node name doesn't have the trip number in them
                        #  so we need to add the start station and end station
                        #  to the graph somehow.
                        if seg.departurePoint.name == self.startStation:
                            dg.add_edge(self.startStation, seg.getDepartureName(), \
                                weight=0)

                        # add zero-weight edge from the station node to their
                        #  corresponding interchange partner node.
                        # Only need to do this for arrival nodes because all nodes
                        #  are represented by both departure and arrival with the
                        #  exception of the initial departure point, and we'll
                        #  never need to change trains at the initial departure
                        #  point
                        if seg.arrivalPoint.name in commonInterchangePoints:
                            dg.add_edge(seg.getArrivalName(), \
                                interchangeFormat % (seg.arrivalPoint.name,), \
                                weight=0)
                            interchangeToEndTrips = self._getTripsDirectWithParams( \
                                seg.arrivalPoint.name, \
                                seg.arrivalPoint.timeOfDay.hour, \
                                self.endStation, self.endHour)
                            if interchangeToEndTrips:
                                interchangeToEndTripId = interchangeToEndTrips[0].getTripId()
                                soonestArrivalSegOne = interchangeToEndTrips[0].getSegments()[0]
                                soonestArrivalLastSeg = interchangeToEndTrips[0].getSegments()[-1]
                                timeAtInterchange = \
                                    datetime.datetime.combine(datetime.datetime.today(), \
                                    soonestArrivalSegOne.departurePoint.timeOfDay) - \
                                    datetime.datetime.combine(datetime.datetime.today(), \
                                    seg.arrivalPoint.timeOfDay)
                                dg.add_node(soonestArrivalSegOne.getDepartureName(), \
                                    {"tripId":interchangeToEndTripId, \
                                    "pist":soonestArrivalSegOne.departurePoint})
                                dg.add_edge(interchangeFormat % (seg.arrivalPoint.name,), \
                                    soonestArrivalSegOne.getDepartureName(), \
                                    weight=timeAtInterchange.seconds/60)
                                [s.addAsDiGraphEdge(dg, ignoreLines=False) for s in interchangeToEndTrips[0].getSegments()]
                                #print "------Adding end edge: %s to %s" % (soonestArrivalLastSeg.getArrivalName(), self.endStation)
                                dg.add_edge(soonestArrivalLastSeg.getArrivalName(), self.endStation, \
                                    weight=0)
                            else:
                                #print "No matches from this interchange (%s) to the end (%s) > %sh and < %sh" % \
                                #    (seg.arrivalPoint.name, \
                                #    self.endStation, \
                                #    seg.arrivalPoint.timeOfDay.hour, \
                                #    self.endHour)
                                pass

                #print "########### Graph start ###########"
                #with open("dg.graphml", "w") as f:
                #    networkx.readwrite.graphml.write_graphml(dg, f)
                #networkx.readwrite.edgelist.write_edgelist(dg, sys.stdout)
                #networkx.readwrite.graphml.write_graphml(dg, sys.stdout)
                #print "########### Graph end ###########"

                #print "Nodes"
                #for n, ndata in dg.nodes(data=True):
                #    print "N: %s nData: %s" % (n, ndata)

                sp = networkx.shortest_path(dg, source=self.startStation, target=self.endStation, weight=True)
                print "Shortest path:", sp
                thisStartStationPIST = None
                thisStopStationPIST = None
                thisTripId = None
                mt = MultiTrip()
                for n in sp:
                    #print "Node '%s': %s" % (n, dg.node[n])
                    if dg.node[n]["tripId"] is None:
                        if thisTripId is None:
                            # At an interchange station (with the Trip already saved),
                            #  or right at the start, with nothing to save.
                            #print "bail... tripId is None and thisTripId is none"
                            continue
                        else:
                            # We're at an interchange station. Save the last trip to the mt
                            # FIXME - populate lineId somehow
                            print "Adding to Multitrip: TripId %s" % (thisTripId,)
                            mt.addTrip(thisTripId, thisStartStationPIST.name, thisStopStationPIST.name)
                            thisTripId = None
                    else:
                        if dg.node[n]["tripId"] != thisTripId:
                            # We're onto a new trip.
                            thisStartStationPIST = dg.node[n]["pist"]
                            thisTripId = dg.node[n]["tripId"]
                        else:
                            # We're continuing a trip.
                            thisStopStationPIST = dg.node[n]["pist"]

                print mt
                multiTripList.append(mt)

            self._trips = multiTripList
        return self._trips

    def _getTripsDirectWithParams(self, startStation, startHour, endStation, endHour):
        #print "Trips with Params: %s (>=%sh) to %s (<%sh)" % \
        #        (startStation, startHour, endStation, endHour)
        # FIXME - make sure the calling functions pass in uniform data types
        if type(startHour) == int:
            startHour = "%02d" % (startHour,)
        if type(endHour) == int:
            endHour = "%02d" % (endHour,)
        assert type(startHour) == type("") and type(endHour) == type(""), "Hours need to be strings"
        assert len(startHour) == 2 and len(endHour) == 2, "Hours need to be two stringified numbers, zero padded"

        tripList = []
        conn = getDbConn()
        # Order by arrival time. It helps for multi-stage trips and does no
        #  harm to other queries.
        tripsSql = """
        select dep.tripId, a.stationName, arv.depTime, d.stationName, dep.depTime, t.lineId
        from Station d, Station a, TripStop dep, TripStop arv, Trip t
        where
        -- start station and start hour
        d.stationName = ? and
        dep.depTime >= ? and
        -- end station and end hour
        a.stationName = ? and
        arv.depTime < ? and
        dep.depTime < arv.depTime and
        arv.tripId = dep.tripId and
        d.stationId = dep.stationId and
        a.stationId = arv.stationId and
        arv.tripId = t.tripId and
        dep.tripId = t.tripId
        order by arv.depTime
        """
        for row in conn.execute(tripsSql, (startStation, startHour, \
                endStation, endHour)):
            tripList.append(Trip(row["tripId"], startStation, endStation))

        #for t in tripList:
        #    print "- %s" % (t,)
        return tripList

    def getTripsDirect(self):
        if self._trips:
            return self._trips
        else:
            self._trips = self._getTripsDirectWithParams(self.startStation, self.startHour, \
                self.endStation, self.endHour)
            return self._trips

    def getMinTripStartHour(self):
        # What about the fact that midnight (0) comes after 11pm (23)?
        return reduce(min, [t.getStartHour() for t in self.getTrips()], 23)

    def getMaxTripEndHour(self):
        # What about the fact that 11pm (23) comes before midnight (0)?
        return reduce(max, [t.getEndHour() for t in self.getTrips()], 0)

    def getMaxTripDistance(self):
        return reduce(max, [t.getTripDistance() for t in self.getTrips()], 0)

    def getAllStationsInTrips(self):
        # FIXME: What exactly should this do now, given trips aren't linear
        #  i.e. the x-axis doesn't make sense now...
        allStations = []
        for trip in self.getTrips():
            for seg in trip.getSegments():
                if seg.arrivalPoint not in allStations:
                    allStations.append(seg.arrivalPoint)
                if seg.departurePoint not in allStations:
                    allStations.append(seg.departurePoint)
                # Ignore interchange segments because they aren't... hmm... do we want them?
                #if seg.lineId != -1:
                    #print "Segment on trip %s: %s" % (trip, seg)
                    # Ignoring the lines because we're trying to get a list
                    #  of all stations to get ordering along the tracks so
                    #  lines aren't helpful
        return allStations

def main():
    parser = OptionParser()
    parser.add_option("-f", "--from", dest="fromStation",
        help="the origin station")
    parser.add_option("-t", "--to", dest="toStation",
        help="the destination station")
    parser.add_option("-s", "--start-hour", dest="startHour",
        help="the start time in the window")
    parser.add_option("-e", "--end-hour", dest="endHour",
        help="the end time in the window")
    parser.add_option("-d", "--debug", dest="debug",
        action="store_true", help="send debug messages to stdout")

    (options, args) = parser.parse_args()

    if not (options.startHour and options.endHour and options.fromStation and options.toStation):
        parser.error("Options -f, -t, -s and -e are compulsory")

    try:
        if int(options.endHour) < 0 or \
                int(options.endHour) > 23 or \
                int(options.startHour) < 0 or \
                int(options.startHour) > 23:
            parser.error("Options -s and -e must be greater than 0 and less than 24")

        # We need leading zeros for hours less than 10
        if len(options.endHour) == 1:
            endHourStr = "0" + options.endHour
        else:
            endHourStr = options.endHour

        if len(options.startHour) == 1:
            startHourStr = "0" + options.startHour
        else:
            startHourStr = options.startHour
    except ValueError:
        parser.error("Options -s and -e must be numbers")

    # Append " Station" if it's been left off, as full names are used in the db
    if options.fromStation.find(" Station") == -1:
        fromStationStr = options.fromStation + " Station"
    else:
        fromStationStr = options.fromStation

    if options.toStation.find(" Station") == -1:
        toStationStr = options.toStation + " Station"
    else:
        toStationStr = options.toStation

    if options.debug:
        global debug
        debug = True

    me = PointInSpaceTime("me", lon=150.615, lat=-33.743, timeOfDay=datetime.time(6, 37))
    tm = TripManager(startHourStr, endHourStr, fromStationStr, toStationStr)
    doc = HTMLdoc("./canvas.html")

    for gClass, w, h in ((TimeVertHTMLDistanceTimeGraph, 320, 480), \
            (TimeVertHTMLDistanceTimeGraph, 480, 320)):
        g = gClass(doc, tm, canvasWidth=w, canvasHeight=h)
        g.populateStationPointMap()
        g.drawGraph()
        g.finalise()

    doc.finalise()

    #print "Closest segment: %s" % me.findClosestSegment()
    #print me

    getDbConn().close()

if __name__ == '__main__':
    main()
# Centre: -33.7500, 150.6500
