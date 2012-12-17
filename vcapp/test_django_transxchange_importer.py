#from django.test.utils import setup_test_environment
from django.test import TestCase
from vcapp import django_transxchange_importer
from vcapp import transxchange_constants
from vcapp.models import InterchangeStation, Line, Segment, Station, Trip, TripStop

import os, subprocess

# TODO - fix logging so that transxchange importer is quiet

__author__ = 'esteele'

class DjangoTransxchangeImporterTestCase():
    fixtures = ['populated.json']

    @classmethod
    def dont_setUpClass_dont(cls):
        # Yuk... but it works until I can make a way to achieve the same end
        #  without forking a new process
        django_transxchange_importer.populate(os.path.join("../data", "505_20090828.xml"), transxchange_constants.TEST_SERVICES)
        output = subprocess.check_output(["/Users/esteele/.virtualenvs/visual-commute/bin/python", "../manage.py", "dumpdata", "--settings=visualcommute.dev_settings"])
        with open("fixtures/testzzz.json", "w") as f:
            f.write(output)

        # Run transxchange importer
        # dump to fixture file

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
        self.assertEqual(InterchangeStation.objects.count(), 144,
            "There are %s InterchangeStations" % (InterchangeStation.objects.count(),))

#setup_test_environment()

