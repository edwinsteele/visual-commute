#from unittest import TestCase
from django.test import TestCase
from models import Station, Trip

__author__ = 'esteele'

class StationTestCase(TestCase):
    def setUp(self):
        self.blaxland_station = Station.objects.get(station_id=252)
        self.glenbrook_station = Station.objects.get(station_id=132)

    def test_short_name(self):
        self.assertEqual(self.blaxland_station.short_name(), "Blaxland")

    def test_distance_from(self):
        self.assertAlmostEqual(self.blaxland_station.distance_from(self.glenbrook_station), 0.0364895750499)

    def test_find_closest_segment(self):
        return self.skipTest("Not implemented yet")

class TripTestCase(TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.a_trip = Trip.objects.get(trip_id=1)

    def test_get_segments(self):
        s = self.a_trip.get_segments()
        self.assertEqual(len(s), 3)

    def test_start_and_end_points(self):
        s = self.a_trip.get_segments()
        self.assertEqual(self.a_trip.get_start_hour(), 8)
        self.assertEqual(self.a_trip.get_end_hour(), 9)
        self.assertEqual(s[0].departure_tripstop.station.short_name(), "Blaxland")
        self.assertEqual(s[len(s) - 1].arrival_tripstop.station.short_name(), "Emu Plains")

    def test_trip_distance(self):
        self.assertAlmostEqual(self.a_trip.get_trip_distance(), 0.08228760)
