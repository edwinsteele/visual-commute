# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Station.station_id'
        db.delete_column('vcapp_station', 'station_id')

        # Adding field 'Station.id'
        db.add_column('vcapp_station', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)

        # Deleting field 'Trip.trip_id'
        db.delete_column('vcapp_trip', 'trip_id')

        # Adding field 'Trip.id'
        db.add_column('vcapp_trip', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)

        # Deleting field 'Line.line_id'
        db.delete_column('vcapp_line', 'line_id')

        # Adding field 'Line.id'
        db.add_column('vcapp_line', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)

        # Deleting field 'Segment.segment_id'
        db.delete_column('vcapp_segment', 'segment_id')

        # Adding field 'Segment.id'
        db.add_column('vcapp_segment', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)

        # Deleting field 'TripStop.tripstop_id'
        db.delete_column('vcapp_tripstop', 'tripstop_id')

        # Adding field 'TripStop.id'
        db.add_column('vcapp_tripstop', 'id',
                      self.gf('django.db.models.fields.AutoField')(default=0, primary_key=True),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Station.station_id'
        raise RuntimeError("Cannot reverse this migration. 'Station.station_id' and its values cannot be restored.")
        # Deleting field 'Station.id'
        db.delete_column('vcapp_station', 'id')


        # User chose to not deal with backwards NULL issues for 'Trip.trip_id'
        raise RuntimeError("Cannot reverse this migration. 'Trip.trip_id' and its values cannot be restored.")
        # Deleting field 'Trip.id'
        db.delete_column('vcapp_trip', 'id')


        # User chose to not deal with backwards NULL issues for 'Line.line_id'
        raise RuntimeError("Cannot reverse this migration. 'Line.line_id' and its values cannot be restored.")
        # Deleting field 'Line.id'
        db.delete_column('vcapp_line', 'id')


        # User chose to not deal with backwards NULL issues for 'Segment.segment_id'
        raise RuntimeError("Cannot reverse this migration. 'Segment.segment_id' and its values cannot be restored.")
        # Deleting field 'Segment.id'
        db.delete_column('vcapp_segment', 'id')


        # User chose to not deal with backwards NULL issues for 'TripStop.tripstop_id'
        raise RuntimeError("Cannot reverse this migration. 'TripStop.tripstop_id' and its values cannot be restored.")
        # Deleting field 'TripStop.id'
        db.delete_column('vcapp_tripstop', 'id')


    models = {
        'vcapp.interchangestation': {
            'Meta': {'object_name': 'InterchangeStation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"})
        },
        'vcapp.line': {
            'Meta': {'object_name': 'Line'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vcapp.segment': {
            'Meta': {'object_name': 'Segment'},
            'arrival_tripstop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'arrival_point'", 'to': "orm['vcapp.TripStop']"}),
            'departure_tripstop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'departure_point'", 'to': "orm['vcapp.TripStop']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Trip']"})
        },
        'vcapp.station': {
            'Meta': {'object_name': 'Station'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'station_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vcapp.trip': {
            'Meta': {'object_name': 'Trip'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'timetable_type': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'vcapp.tripstop': {
            'Meta': {'object_name': 'TripStop'},
            'departure_time': ('django.db.models.fields.TimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Trip']"})
        }
    }

    complete_apps = ['vcapp']