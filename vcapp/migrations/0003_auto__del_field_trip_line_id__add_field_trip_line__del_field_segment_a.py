# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Trip.line_id'
        db.delete_column('vcapp_trip', 'line_id_id')

        # Adding field 'Trip.line'
        db.add_column('vcapp_trip', 'line',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Line']),
                      keep_default=False)

        # Deleting field 'Segment.arrival_tripstop_id'
        db.delete_column('vcapp_segment', 'arrival_tripstop_id_id')

        # Deleting field 'Segment.departure_tripstop_id'
        db.delete_column('vcapp_segment', 'departure_tripstop_id_id')

        # Adding field 'Segment.departure_tripstop'
        db.add_column('vcapp_segment', 'departure_tripstop',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='departure_point', to=orm['vcapp.TripStop']),
                      keep_default=False)

        # Adding field 'Segment.arrival_tripstop'
        db.add_column('vcapp_segment', 'arrival_tripstop',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='arrival_point', to=orm['vcapp.TripStop']),
                      keep_default=False)

        # Adding field 'Segment.trip'
        db.add_column('vcapp_segment', 'trip',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Trip']),
                      keep_default=False)

        # Deleting field 'InterchangeStation.line_id'
        db.delete_column('vcapp_interchangestation', 'line_id_id')

        # Deleting field 'InterchangeStation.station_id'
        db.delete_column('vcapp_interchangestation', 'station_id_id')

        # Adding field 'InterchangeStation.line'
        db.add_column('vcapp_interchangestation', 'line',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Line']),
                      keep_default=False)

        # Adding field 'InterchangeStation.station'
        db.add_column('vcapp_interchangestation', 'station',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Station']),
                      keep_default=False)

        # Deleting field 'TripStop.trip_id'
        db.delete_column('vcapp_tripstop', 'trip_id_id')

        # Deleting field 'TripStop.station_id'
        db.delete_column('vcapp_tripstop', 'station_id_id')

        # Adding field 'TripStop.trip'
        db.add_column('vcapp_tripstop', 'trip',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Trip']),
                      keep_default=False)

        # Adding field 'TripStop.station'
        db.add_column('vcapp_tripstop', 'station',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Station']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Trip.line_id'
        db.add_column('vcapp_trip', 'line_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Line']),
                      keep_default=False)

        # Deleting field 'Trip.line'
        db.delete_column('vcapp_trip', 'line_id')

        # Adding field 'Segment.arrival_tripstop_id'
        db.add_column('vcapp_segment', 'arrival_tripstop_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='arrivals', to=orm['vcapp.TripStop']),
                      keep_default=False)

        # Adding field 'Segment.departure_tripstop_id'
        db.add_column('vcapp_segment', 'departure_tripstop_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='departures', to=orm['vcapp.TripStop']),
                      keep_default=False)

        # Deleting field 'Segment.departure_tripstop'
        db.delete_column('vcapp_segment', 'departure_tripstop_id')

        # Deleting field 'Segment.arrival_tripstop'
        db.delete_column('vcapp_segment', 'arrival_tripstop_id')

        # Deleting field 'Segment.trip'
        db.delete_column('vcapp_segment', 'trip_id')

        # Adding field 'InterchangeStation.line_id'
        db.add_column('vcapp_interchangestation', 'line_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Line']),
                      keep_default=False)

        # Adding field 'InterchangeStation.station_id'
        db.add_column('vcapp_interchangestation', 'station_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Station']),
                      keep_default=False)

        # Deleting field 'InterchangeStation.line'
        db.delete_column('vcapp_interchangestation', 'line_id')

        # Deleting field 'InterchangeStation.station'
        db.delete_column('vcapp_interchangestation', 'station_id')

        # Adding field 'TripStop.trip_id'
        db.add_column('vcapp_tripstop', 'trip_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Trip']),
                      keep_default=False)

        # Adding field 'TripStop.station_id'
        db.add_column('vcapp_tripstop', 'station_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['vcapp.Station']),
                      keep_default=False)

        # Deleting field 'TripStop.trip'
        db.delete_column('vcapp_tripstop', 'trip_id')

        # Deleting field 'TripStop.station'
        db.delete_column('vcapp_tripstop', 'station_id')


    models = {
        'vcapp.interchangestation': {
            'Meta': {'object_name': 'InterchangeStation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"})
        },
        'vcapp.line': {
            'Meta': {'object_name': 'Line'},
            'line_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'line_name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vcapp.segment': {
            'Meta': {'object_name': 'Segment'},
            'arrival_tripstop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'arrival_point'", 'to': "orm['vcapp.TripStop']"}),
            'departure_tripstop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'departure_point'", 'to': "orm['vcapp.TripStop']"}),
            'segment_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Trip']"})
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
            'line': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Line']"}),
            'timetable_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'trip_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        'vcapp.tripstop': {
            'Meta': {'object_name': 'TripStop'},
            'departure_time': ('django.db.models.fields.TimeField', [], {}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Station']"}),
            'trip': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['vcapp.Trip']"}),
            'tripstop_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['vcapp']