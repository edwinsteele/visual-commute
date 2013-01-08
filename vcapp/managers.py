
from django.db import models

import logging


class TripManager(models.Manager):
    index_on_line_cache = {}

    def get_all_stations_in_trips(self, trip_list):
        matrix = self.get_stop_matrix(trip_list)
        ordered_station_list = [station for station, dep_time_list in
                                matrix]
        return ordered_station_list

    def get_max_trip_distance(self, trip_list):
        return reduce(max, [t.get_trip_distance() for t in trip_list], 0)

    def get_line_cache(self, line_id):
        if line_id not in self.index_on_line_cache:
            from vcapp.models import StationLineOrder
            d = {}
            for slo in StationLineOrder.objects.select_related().filter(line=line_id):
                d[slo.station] = slo.line_index
            self.index_on_line_cache[line_id] = d

        return self.index_on_line_cache[line_id]

    def get_stop_matrix(self, trip_list):
        # Create a sparse matrix
        station_set = set()
        sparse = {}
        for t in trip_list:
            seg = None
            for seg in t.get_segments():
                if seg.departure_tripstop.station not in sparse:
                    sparse[seg.departure_tripstop.station] = {}

                sparse[seg.departure_tripstop.station][seg.trip_id] =\
                    seg.departure_tripstop.departure_time
                station_set.add(seg.departure_tripstop.station)
            # Append the final arrival station (if there are any segments)
            if seg:
                if seg.arrival_tripstop.station not in sparse:
                    sparse[seg.arrival_tripstop.station] = {}
                sparse[seg.arrival_tripstop.station][seg.trip_id] =\
                    seg.arrival_tripstop.departure_time
                station_set.add(seg.arrival_tripstop.station)

        # Assumes all of the trips are on the same line... do we want to accept
        #  that or do we reject at a higher level?
        key_cmp_fn = self.get_line_cache(trip_list[0].line_id).get
        combined_sorted_station_list = sorted(list(station_set), key=key_cmp_fn)

        s2 = []
        for station in combined_sorted_station_list:
            dep_time_list = []
            for t in trip_list:
                dep_time_list.append(sparse[station].get(t.id))
            s2.append([station, dep_time_list])

        return s2
