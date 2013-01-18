from django.test import TestCase
from vcapp import django_transxchange_importer
from vcapp import transxchange_constants
from vcapp.models import InterchangeStation, Line, Segment, Station, Trip, TripStop

import os, subprocess

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

    def test_segments_are_in_correct_time_order(self):
        for t in Trip.objects.all():
            prev_segment = None
            for this_segment in t.get_segments():
                # Departure time is before Arrival time in the same segment
                self.assertLess(this_segment.departure_tripstop.departure_time,
                    this_segment.arrival_tripstop.departure_time)
                if prev_segment:
                    # Departure time in the previous arrival tripstop is equal to
                    # the departure time in the departure tripstop in this segment
                    self.assertEqual(prev_segment.arrival_tripstop.departure_time,
                        this_segment.departure_tripstop.departure_time)

                prev_segment = this_segment

    def test_segment_count_per_trip(self):
        self.assertListEqual(
            [len(t.get_segments()) for t in Trip.objects.all()],
            [21, 17, 12, 21, 22, 27]
        )

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


class TestManagerTestCase(TestCase):
    fixtures = ['populated.json']

    def setUp(self):
        self.central_str = "Central Station"
        self.parramatta_str = "Parramatta Station"
        self.springwood_str = "Springwood Station"
        self.central_station = Station.objects.get(station_name=self.central_str)
        self.parramatta_station = Station.objects.get(station_name=self.parramatta_str)
        self.springwood_station = Station.objects.get(station_name=self.springwood_str)

    def test_find_trips_direct(self):
        trips_found_forward = Trip.objects.find_trips_direct(
            self.parramatta_station,
            self.central_station,
            15,
            16
        )
        self.assertEquals(len(trips_found_forward), 1)
        self.assertEqual(trips_found_forward[0].id, 1)

        trips_found_reverse = Trip.objects.find_trips_direct(
            self.central_station,
            self.parramatta_station,
            15,
            16
        )
        print trips_found_reverse
        self.assertEquals(len(trips_found_reverse), 0, "Found trips in the wrong "
            "direction i.e. departure_time at to_station is before "
            "departure_time at from_station")

    def test_get_stop_matrix(self):
        trip_one = Trip.objects.get(pk=1)
        matrix_with_to_and_from = Trip.objects.get_stop_matrix(
            [trip_one],
            self.springwood_station,
            self.parramatta_station,
        )

        self.assertEquals(matrix_with_to_and_from[0][0].station_name,
            self.springwood_str)
        self.assertEquals(matrix_with_to_and_from[-1][0].station_name,
            self.parramatta_str)

        matrix_without_to_and_from = Trip.objects.get_stop_matrix(
            [trip_one],
            None,
            None,
        )
        trip_one_segments = trip_one.get_segments()
        self.assertEquals(matrix_without_to_and_from[0][0],
            trip_one_segments[0].departure_tripstop.station)
        self.assertEquals(matrix_without_to_and_from[-1][0],
            trip_one_segments[len(trip_one_segments)-1].arrival_tripstop.station)

        # Trip 1 goes from Katoomba to Central and Trip 2 goes from Springwood
        #  to Gordon. The matrix should go from Katoomba to Gordon
        combined_matrix = Trip.objects.get_stop_matrix(
            [trip_one, Trip.objects.get(pk=2)],
            None,
            None,
        )
        self.assertEquals(combined_matrix[0][0].station_name, "Katoomba Station")
        self.assertEquals(combined_matrix[-1][0].station_name, "Gordon Station")


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

