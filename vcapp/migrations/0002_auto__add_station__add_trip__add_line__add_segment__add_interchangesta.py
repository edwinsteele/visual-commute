# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Station'
        db.create_table('vcapp_station', (
            ('station_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('station_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('lon', self.gf('django.db.models.fields.FloatField')()),
            ('lat', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('vcapp', ['Station'])

        # Adding model 'Trip'
        db.create_table('vcapp_trip', (
            ('trip_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('timetable_type', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('line_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Line'])),
        ))
        db.send_create_signal('vcapp', ['Trip'])

        # Adding model 'Line'
        db.create_table('vcapp_line', (
            ('line_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('line_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('vcapp', ['Line'])

        # Adding model 'Segment'
        db.create_table('vcapp_segment', (
            ('segment_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('departure_tripstop_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='departures', to=orm['vcapp.TripStop'])),
            ('arrival_tripstop_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='arrivals', to=orm['vcapp.TripStop'])),
        ))
        db.send_create_signal('vcapp', ['Segment'])

        # Adding model 'InterchangeStation'
        db.create_table('vcapp_interchangestation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Line'])),
            ('station_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Station'])),
        ))
        db.send_create_signal('vcapp', ['InterchangeStation'])

        # Adding model 'TripStop'
        db.create_table('vcapp_tripstop', (
            ('tripstop_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('departure_time', self.gf('django.db.models.fields.TimeField')()),
            ('trip_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Trip'])),
            ('station_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['vcapp.Station'])),
        ))
        db.send_create_signal('vcapp', ['TripStop'])


    def backwards(self, orm):
        # Deleting model 'Station'
        db.delete_table('vcapp_station')

        # Deleting model 'Trip'
        db.delete_table('vcapp_trip')

        # Deleting model 'Line'
        db.delete_table('vcapp_line')

        # Deleting model 'Segment'
        db.delete_table('vcapp_segment')

        # Deleting model 'InterchangeStation'
        db.delete_table('vcapp_interchangestation')

        # Deleting model 'TripStop'
        db.delete_table('vcapp_tripstop')


    models = {
        'vcapp.interchangestation': {
            'Meta': {'object_name': 'InterchangeStation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'station_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"})
        },
        'vcapp.line': {
            'Meta': {'object_name': 'Line'},
            'line_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'line_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vcapp.segment': {
            'Meta': {'object_name': 'Segment'},
            'arrival_tripstop_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'arrivals'", 'to': "orm['vcapp.TripStop']"}),
            'departure_tripstop_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'departures'", 'to': "orm['vcapp.TripStop']"}),
            'segment_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'vcapp.station': {
            'Meta': {'object_name': 'Station'},
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'station_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'station_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vcapp.trip': {
            'Meta': {'object_name': 'Trip'},
            'line_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'timetable_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'trip_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'vcapp.tripstop': {
            'Meta': {'object_name': 'TripStop'},
            'departure_time': ('django.db.models.fields.TimeField', [], {}),
            'station_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"}),
            'trip_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Trip']"}),
            'tripstop_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['vcapp']