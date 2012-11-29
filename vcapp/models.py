"""
These models can be more easily understood in reference to the old-style paper
 timetable where there are a list of stations down one side, trips are columns
 with each non-empty cell being a tripstop (relating a Station to a point in
 time). A segment is a pair of vertically adjacent non-empty cells (TripStops)

The timetable itself is a collection of trips on a single Line (usually)
"""

from django.db import models
import geometry
import datetime as dt

class Station(models.Model):
    station_id = models.IntegerField(primary_key=True)
    station_name = models.CharField(max_length=50)
    lon = models.FloatField()
    lat = models.FloatField()

    def __unicode__(self):
        return u"%s - lon: %.3f (E-W) lat: %.3f (N-S)" % \
               (self.station_name, self.lon, self.lat)

    def short_name(self):
        # Removes the trailing " Station", at least for now.
        return u"%s" % (self.station_name.rsplit(" ", 1)[0])

    # May be better suited to a point in space time class
    def distance_from(self, location):
        return geometry.line_magnitude(x1=self.lon,
            y1=self.lat,
            x2=location.lon,
            y2=location.lat)

    def find_closest_segment(self):
        pass


class Line(models.Model):
    line_id = models.IntegerField(primary_key=True)
    line_name = models.CharField(max_length=50)

    def __unicode__(self):
        return u"%s (id %s)" % (self.line_name, self.line_id)


class Trip(models.Model):
    """
    A Trip is a column in a traditional timetable. It is a list of TripStops
    """
    TIMETABLE_TYPE_CHOICES = (
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
    )
    trip_id = models.IntegerField(primary_key=True)
    timetable_type = models.CharField(max_length=2, choices=TIMETABLE_TYPE_CHOICES)
    line = models.ForeignKey('Line')

    def __unicode__(self):
        return u"Trip (id:%s) from %s to %s, on line %s" % \
               (self.trip_id,
                self.get_segments()[0].departure_tripstop.station,
                self.get_segments()[0].arrival_tripstop.station,
                self.line.line_id)

    def get_segments(self):
        # FIXME - we need to order the segments explicitly... order do we given we do the initial load?
        return self.segment_set.all()

    def get_trip_distance(self):
        return sum([segment.segment_length() for segment in self.get_segments()])

    # FIXME - Do we really need these methods to be in hours? why not just datetime.time?
    def get_start_hour(self):
        return self.get_segments()[0].departure_tripstop.departure_time.hour

    def get_end_hour(self):
        # departure time of the arrival tripstop???
        return self.get_segments()[len(self.get_segments())-1].arrival_tripstop.departure_time.hour


class TripStop(models.Model):
    """
    A TripStop is a point in space-time on a trip. It corresponds to a cell in a
     traditional timetable, where a trip intersects with a station.

    key should be tripId + stationId. A station can't appear more than once
    on a particular trip (what about city circle?)
    """
    tripstop_id = models.IntegerField(primary_key=True)
    departure_time = models.TimeField()
    trip = models.ForeignKey('Trip')
    station = models.ForeignKey('Station')

    def __unicode__(self):
        return u"%s" % self.tripstop_id


class Segment(models.Model):
    """
    Note that because we only store departure time, we don't know how long a
    train actually waits at a station. close enough for the moment
    """
    segment_id = models.IntegerField(primary_key=True)
    # FIXME - do I really need to create a backwards relation for these FKs?
    # https://docs.djangoproject.com/en/dev/topics/db/queries/#backwards-related-objects
    departure_tripstop = models.ForeignKey('TripStop', related_name='departure_point')
    arrival_tripstop = models.ForeignKey('TripStop', related_name='arrival_point')
    # TODO - work out how interchange stations fit here. Are they an on-the-fly
    #  segment? Or are they not really a segment at all?
    trip = models.ForeignKey('Trip')
    # The old model had line as an attribute. Is it important?

    def __unicode__(self):
        return u"Segment [%s] from %s (%s) to %s (%s)" % \
               (self.segment_id,
                self.departure_tripstop.station,
                self.departure_tripstop.departure_time,
                self.arrival_tripstop.station,
                self.arrival_tripstop.departure_time
            )

    def get_trip_id(self):
        # arrival and departure trip id should be the same, perhaps with the
        #  exception of interchange segments
        assert self.departure_tripstop.trip_id == self.arrival_tripstop.trip_id
        return self.trip.trip_id

    def get_line_id(self):
        # arrival and departure line id should be the same, perhaps with the
        #  exception of interchange segments
        assert self.departure_tripstop.trip.line.line_id == \
               self.arrival_tripstop.trip.line.line_id
        return self.trip.line.line_id

    def get_departure_point_name(self):
        return "%s on trip %s" % (self.departure_tripstop.station.station_name,
            self.get_trip_id())

    def get_arrival_point_name(self):
        return "%s on trip %s" % (self.arrival_tripstop.station.station_name,
            self.get_trip_id())

    def add_as_digraph_edge(self, dg, ignore_lines):
        if ignore_lines:
            dep_name = self.departure_tripstop.station.station_name
            arv_name = self.arrival_tripstop.station.station_name
        else:
            dep_name = self.get_departure_point_name()
            arv_name = self.get_arrival_point_name()

        if dep_name not in dg:
            dg.add_node(dep_name, {"tripId":self.tripId, "pist":self.departure_tripstop})
        if arv_name not in dg:
            dg.add_node(arv_name, {"tripId":self.tripId, "pist":self.arrival_tripstop})

        dtdt = dt.datetime
        duration_time_delta = \
            dtdt.combine(dtdt.today(), self.arrival_tripstop.departure_time) - \
            dtdt.combine(dtdt.today(), self.departure_tripstop.departure_time)
        edge_weight = duration_time_delta.seconds/60
        #print "Adding edge from '%s' to '%s' with weight %s" % (dep_name, arv_name, edge_weight)
        dg.add_edge(dep_name, arv_name, weight=edge_weight)


    def segment_length(self):
        return self.departure_tripstop.station.distance_from(
                self.arrival_tripstop.station)


class InterchangeStation(models.Model):
    line = models.ForeignKey("Line")
    station = models.ForeignKey("Station")

    def __unicode__(self):
        return u"Interchange Station %s on line %s" % (self.station, self.line)

