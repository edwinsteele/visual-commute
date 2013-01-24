"""
These models can be more easily understood in reference to the old-style paper
 timetable where there are a list of stations down one side, trips are columns
 with each non-empty cell being a tripstop (relating a Station to a point in
 time). A segment is a pair of vertically adjacent non-empty cells (TripStops)

The timetable itself is a collection of trips on a single Line (usually)
"""

from django.db import models
from django.db.models.signals import post_init
import vcapp.managers
import vcapp.trip_helpers
import vcapp.geometry
import datetime as dt
import logging

class Station(models.Model):
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
        return vcapp.geometry.line_magnitude(x1=self.lon,
            y1=self.lat,
            x2=location.lon,
            y2=location.lat)

    def find_closest_segment(self):
        pass


class Line(models.Model):
    line_name = models.CharField(max_length=50)

    def __unicode__(self):
        return u"%s (id %s)" % (self.line_name, self.id)

    def index_on_line(self, station_name):
        idx = StationLineOrder.objects.filter(station__station_name=station_name,
            line=self.id)
        return idx[0].line_index


class StationLineOrder(models.Model):
    station = models.ForeignKey("Station")
    line = models.ForeignKey("Line")
    # Starts at 1, with 1 being the station at the start of the trip
    line_index = models.PositiveIntegerField()

    def __unicode__(self):
        return u"StationLineOrder: Station %s with index %s on line %s" % \
               (self.station, self.line_index, self.line)


class Trip(models.Model, vcapp.trip_helpers.AbstractTrip):
    """
    A Trip is a column in a traditional timetable. It is a list of TripStops
    """
    TIMETABLE_TYPE_CHOICES = (
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
    )
    timetable_type = models.CharField(max_length=2, choices=TIMETABLE_TYPE_CHOICES)
    line = models.ForeignKey('Line')
    objects = vcapp.managers.TripManager()

    def __unicode__(self):
        segs = self.get_segments()
        if segs:
            return u"Trip (id:%s) from %s to %s, on line %s" % \
                   (self.id,
                    self.get_start_station(),
                    self.get_end_station(),
                    self.line.id)
        else:
            return u"Trip (id:%s) (no segments), on line %s" % \
                   (self.id,
                    self.line.id)

    def get_segments(self):
        """
        Segments are loaded in increasing time order, so the implicit ordering
        is actually the ordering that he wanted
        """
        # FIXME - use post_init signal to set _segment_cache to None
        # http://stackoverflow.com/questions/9415616/adding-to-the-constructor-of-a-django-model?lq=1
        # We use None because we can have an empty segment cache and want them
        #  to be distinct (so queries that return nothing don't get re-run)
        if not hasattr(self, "_segment_cache"):
            self._segment_cache = self.segment_set.select_related().all()
        return self._segment_cache

    def as_summary_tuple(self):
        return [(self.get_start_station(), self.get_start_time(),
                "travel to",
                self.get_end_station(), self.get_end_time())]


class PartialTrip(Trip):
    """
    A Trip with defined starting and finishing endpoints. Note that because
     we can't override the constructor we need to make sure that the endpoints
     are set as some normal ways of obtaining a PartialTrip can leave these
     unset. Hence the asserts in the get_segments method.
    """
    objects = vcapp.managers.PartialTripManager()

    class Meta:
        proxy = True

    def __unicode__(self):
        segs = self.get_segments()
        if segs:
            return u"PartialTrip (based on id:%s) from %s to %s, on line %s" %\
                   (self.id,
                    segs[0].departure_tripstop.station,
                    segs[len(segs)-1].arrival_tripstop.station,
                    self.line.id)
        else:
            return u"PartialTrip (based on id:%s) (no segments), on line %s" %\
                   (self.id,
                    self.line.id)

    def get_segments(self):
        filtered_segments = []
        currently_including_segments = False
        #noinspection PyUnresolvedReferences
        assert(self.starting_endpoint is not None)
        #noinspection PyUnresolvedReferences
        assert(self.finishing_endpoint is not None)
        segs = Trip.get_segments(self)
        for seg in segs:
            #noinspection PyUnresolvedReferences
            if seg.departure_tripstop.station == self.starting_endpoint:
                currently_including_segments = True

            if currently_including_segments:
                filtered_segments.append(seg)

            #noinspection PyUnresolvedReferences
            if seg.arrival_tripstop.station == self.finishing_endpoint:
                currently_including_segments = False

        return filtered_segments


class TripStop(models.Model):
    """
    A TripStop is a point in space-time on a trip. It corresponds to a cell in a
     traditional timetable, where a trip intersects with a station.

    key should be tripId + stationId. A station can't appear more than once
    on a particular trip (what about city circle?)
    """
    departure_time = models.TimeField()
    trip = models.ForeignKey('Trip')
    station = models.ForeignKey('Station')

    def __unicode__(self):
        return u"%s" % self.id


class Segment(models.Model):
    """
    Note that because we only store departure time, we don't know how long a
    train actually waits at a station. close enough for the moment
    """
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
               (self.id,
                self.departure_tripstop.station,
                self.departure_tripstop.departure_time,
                self.arrival_tripstop.station,
                self.arrival_tripstop.departure_time
            )

    def get_trip_id(self):
        # arrival and departure trip id should be the same, perhaps with the
        #  exception of interchange segments
        assert self.departure_tripstop.trip_id == self.arrival_tripstop.trip_id
        return self.trip.id

    def get_line_id(self):
        # arrival and departure line id should be the same, perhaps with the
        #  exception of interchange segments
        assert self.departure_tripstop.trip.line.id == \
               self.arrival_tripstop.trip.line.id
        return self.trip.line.id

    def get_departure_point_name(self):
        return "%s on trip %s" % (self.departure_tripstop.station.station_name,
            self.get_trip_id())

    def get_arrival_point_name(self):
        return "%s on trip %s" % (self.arrival_tripstop.station.station_name,
            self.get_trip_id())

    def add_as_digraph_edge(self, dg, ignore_lines):
        if self.departure_tripstop.station not in dg:
            dg.add_node(self.departure_tripstop.station)
        if self.arrival_tripstop.station not in dg:
            dg.add_node(self.arrival_tripstop.station)

        dtdt = dt.datetime
        duration_time_delta = \
            dtdt.combine(dtdt.today(), self.arrival_tripstop.departure_time) - \
            dtdt.combine(dtdt.today(), self.departure_tripstop.departure_time)
        edge_weight = duration_time_delta.seconds/60
        logging.debug("Adding edge from '%s' to '%s' with weight %s",
            self.departure_tripstop.station.short_name(),
            self.arrival_tripstop.station.short_name(),
            edge_weight)
        dg.add_edge(self.departure_tripstop.station,
            self.arrival_tripstop.station,
            weight=edge_weight)

    def segment_length(self):
        return self.departure_tripstop.station.distance_from(
                self.arrival_tripstop.station)


class InterchangeStation(models.Model):
    line = models.ForeignKey("Line")
    station = models.ForeignKey("Station")

    def __unicode__(self):
        return u"Interchange Station %s on line %s" % (self.station, self.line)


def set_empty_endpoints_on_trip(sender, *args, **kwargs):
    instance = kwargs.get('instance')
    instance.starting_endpoint = None
    instance.finishing_endpoint = None

post_init.connect(set_empty_endpoints_on_trip, PartialTrip)
