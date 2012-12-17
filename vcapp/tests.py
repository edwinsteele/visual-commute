from django.test import TestCase
from vcapp import django_transxchange_importer
from vcapp import transxchange_constants
from vcapp.models import InterchangeStation, Line, Segment, Station, Trip, TripStop

import json, os, subprocess

# TODO - fix logging so that transxchange importer is quiet

__author__ = 'esteele'

class DjangoTransxchangeImporterTestCase(TestCase):
    fixtures = ['populated.json']

    @classmethod
    def setUpClass(cls):
        # Yuk... but it works until I can make a way to achieve the same end
        #  without forking a new process
        django_transxchange_importer.populate(
            os.path.join("data", "505_20090828.xml"),
            transxchange_constants.TEST_SERVICES)
        with open("vcapp/fixtures/populated.json", "w") as output_file:
            subprocess.call([
                "/Users/esteele/.virtualenvs/visual-commute/bin/python",
                "manage.py",
                "dumpdata",
                "--settings=visualcommute.dev_settings"],
                stdout=output_file)

    def setUp(self):
        pass

    def test_correct_counts(self):
        self.assertEqual(Line.objects.count(), 4,
            "There are %s Lines" % (Line.objects.count(),))
        self.assertEqual(Station.objects.count(), 315,
            "There are %s Stations" % (Station.objects.count(),))
        self.assertEqual(Trip.objects.count(), 6,
            "There are %s Trips" % (Trip.objects.count(),))
        self.assertEqual(TripStop.objects.count(), 126,
            "There are %s Tripstops" % (TripStop.objects.count(),))
        self.assertEqual(Segment.objects.count(), 120,
            "There are %s Segments" % (Segment.objects.count(),))
        self.assertEqual(InterchangeStation.objects.count(), 48,
            "There are %s InterchangeStations" % (InterchangeStation.objects.count(),))


class TripTestCase(TestCase):
    fixtures = ['populated.json']

    def setUp(self):
        self.a_trip = Trip.objects.get(id=1)

    def test_get_segments(self):
        s = self.a_trip.get_segments()
        self.assertEqual(len(s), 21)

    def test_start_and_end_points(self):
        s = self.a_trip.get_segments()
        self.assertEqual(self.a_trip.get_start_hour(), 13)
        self.assertEqual(self.a_trip.get_end_hour(), 15)
        self.assertEqual(s[0].departure_tripstop.station.short_name(),
            "Katoomba")
        self.assertEqual(s[0].arrival_tripstop.station.short_name(),
            "Leura")
        self.assertEqual(s[len(s) - 1].departure_tripstop.station.short_name(),
            "Strathfield")
        self.assertEqual(s[len(s) - 1].arrival_tripstop.station.short_name(),
            "Central")

    def test_trip_distance(self):
        self.assertAlmostEqual(self.a_trip.get_trip_distance(), 0.99622666097)

class StationTestCase(TestCase):
    fixtures = ['populated.json']

    def setUp(self):
        self.blaxland_station = Station.objects.get(id=253)
        self.glenbrook_station = Station.objects.get(id=132)

    def test_short_name(self):
        self.assertEqual(self.blaxland_station.short_name(), "Blaxland")
        self.assertEqual(self.glenbrook_station.short_name(), "Glenbrook")

    def test_distance_from(self):
        self.assertAlmostEqual(self.blaxland_station.distance_from(
                self.glenbrook_station),
            0.02807315709195226)

    def test_find_closest_segment(self):
        return self.skipTest("Station Find Closest Segment Not implemented yet")

