from django.test import TestCase
from vcapp import django_transxchange_importer

__author__ = 'esteele'

class DjangoTransxchangeImporterTestCase(TestCase):

    #@classmethod
    #def setUpClass(cls):
    #    print "Doing expensive importer setup stuff"
    #    # Run transxchange importer
    #    # dump to fixture file
    def setUp(self):
        self.x = 1

    def test_stuff(self):
        self.assertEqual(self.x, 1, "is the same")