# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Station'
        db.create_table('vcapp_station', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('station_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('lon', self.gf('django.db.models.fields.FloatField')()),
            ('lat', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('vcapp', ['Station'])

        # Adding model 'Line'
        db.create_table('vcapp_line', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('vcapp', ['Line'])

        # Adding model 'Trip'
        db.create_table('vcapp_trip', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timetable_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('line', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Line'])),
        ))
        db.send_create_signal('vcapp', ['Trip'])

        # Adding model 'TripStop'
        db.create_table('vcapp_tripstop', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('departure_time', self.gf('django.db.models.fields.TimeField')()),
            ('trip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Trip'])),
            ('station', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Station'])),
        ))
        db.send_create_signal('vcapp', ['TripStop'])

        # Adding model 'Segment'
        db.create_table('vcapp_segment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('departure_tripstop', self.gf('django.db.models.fields.related.ForeignKey')(related_name='departure_point', to=orm['vcapp.TripStop'])),
            ('arrival_tripstop', self.gf('django.db.models.fields.related.ForeignKey')(related_name='arrival_point', to=orm['vcapp.TripStop'])),
            ('trip', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Trip'])),
        ))
        db.send_create_signal('vcapp', ['Segment'])

        # Adding model 'InterchangeStation'
        db.create_table('vcapp_interchangestation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Line'])),
            ('station', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Station'])),
        ))
        db.send_create_signal('vcapp', ['InterchangeStation'])


    def backwards(self, orm):
        # Deleting model 'Station'
        db.delete_table('vcapp_station')

        # Deleting model 'Line'
        db.delete_table('vcapp_line')

        # Deleting model 'Trip'
        db.delete_table('vcapp_trip')

        # Deleting model 'TripStop'
        db.delete_table('vcapp_tripstop')

        # Deleting model 'Segment'
        db.delete_table('vcapp_segment')

        # Deleting model 'InterchangeStation'
        db.delete_table('vcapp_interchangestation')


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