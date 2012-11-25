from django.db import models

class Station(models.Model):
    station_id = models.IntegerField(primary_key=True)
    station_name = models.CharField(max_length=50)
    lon = models.FloatField()
    lat = models.FloatField()

    def __unicode__(self):
        return u"%s" % self.id


class Line(models.Model):
    line_id = models.IntegerField(primary_key=True)
    line_name = models.CharField(max_length=50)

    def __unicode__(self):
        return u"%s" % self.id


class Trip(models.Model):
    TIMETABLE_TYPE_CHOICES = (
        ('WD', 'Weekday'),
        ('WE', 'Weekend'),
    )
    trip_id = models.IntegerField(primary_key=True)
    timetable_type = models.CharField(max_length=2, choices=TIMETABLE_TYPE_CHOICES)
    line_id = models.ForeignKey('Line')

    def __unicode__(self):
        return u"%s" % self.id


class TripStop(models.Model):
    """
    key should be tripId + stationId. A station can't appear more than once
    on a particular trip (what about city circle?)
    """
    tripstop_id = models.IntegerField(primary_key=True)
    departure_time = models.TimeField()
    trip_id = models.ForeignKey('Trip')
    station_id = models.ForeignKey('Station')

    def __unicode__(self):
        return u"%s" % self.id


class Segment(models.Model):
    segment_id = models.IntegerField(primary_key=True)
    departure_tripstop_id = models.ForeignKey('TripStop', related_name='departures')
    arrival_tripstop_id = models.ForeignKey('TripStop', related_name='arrivals')

    def __unicode__(self):
        return u"%s" % self.id


class InterchangeStation(models.Model):
    line_id = models.ForeignKey("Line")
    station_id = models.ForeignKey("Station")

    def __unicode__(self):
        return u"%s" % self.id

