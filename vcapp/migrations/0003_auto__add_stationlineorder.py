# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StationLineOrder'
        db.create_table('vcapp_stationlineorder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('station', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Station'])),
            ('line', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Line'])),
            ('line_index', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('vcapp', ['StationLineOrder'])


    def backwards(self, orm):
        # Deleting model 'StationLineOrder'
        db.delete_table('vcapp_stationlineorder')


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
        'vcapp.stationlineorder': {
            'Meta': {'object_name': 'StationLineOrder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'line_index': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"})
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