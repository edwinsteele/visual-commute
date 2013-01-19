from django.db import models

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
        station_set = set()
        sparse = {}

        for t in trip_list:
            seg = None
            for seg in t.get_segments():
                if seg.departure_tripstop.station not in sparse:
                    sparse[seg.departure_tripstop.station] = {}

                sparse[seg.departure_tripstop.station][seg.trip_id] = \
                    seg.departure_tripstop.departure_time
                station_set.add(seg.departure_tripstop.station)

            # Append the final arrival station (if there are any segments)
            if seg:
                if seg.arrival_tripstop.station not in sparse:
                    sparse[seg.arrival_tripstop.station] = {}
                sparse[seg.arrival_tripstop.station][seg.trip_id] = \
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


class PartialTripManager(TripManager):

    def find_trips_direct(self, from_station, to_station, from_time, to_time):
        # do we need an order-by clause, as we had in the old system?
        trip_list = self.filter(
            segment__departure_tripstop__station__station_name=from_station.station_name,
            segment__departure_tripstop__departure_time__gte=from_time,
        ).filter(
            segment__arrival_tripstop__station__station_name=to_station.station_name,
            segment__arrival_tripstop__departure_time__lt=to_time,
        ).extra(
            # To make sure the trip is in the right direction
            # This will need to change when we start accepting trips over midnight
            where=['vcapp_tripstop.departure_time < T6."departure_time"']
        )
        for trip in trip_list:
            trip.starting_endpoint = from_station
            trip.finishing_endpoint = to_station
        return trip_list

    def get_interchange_points_between_stations(self, from_station, to_station):
        from vcapp.models import StationLineOrder, InterchangeStation
        lines_containing_from_station = StationLineOrder.objects.filter(
            station=from_station)
        lines_containing_to_station = StationLineOrder.objects.filter(
            station=to_station)
        from_station_line_interchange_points = set()
        to_station_line_interchange_points = set()
        [from_station_line_interchange_points.add(ip)
            for ip in [InterchangeStation.objects.filter(line=lcfs)
            for lcfs in lines_containing_from_station]]
        [to_station_line_interchange_points.add(ip)
            for ip in [InterchangeStation.objects.filter(line=lcts)
            for lcts in lines_containing_to_station]]

        return from_station_line_interchange_points.union(
            to_station_line_interchange_points)


    def find_trips_indirect(self, from_station, to_station, from_time, to_time):
        common_interchange_points = self.get_interchange_points_between_stations(
            from_station, to_station)

        # Get points from "from station" to interchange point
        start_to_interchange_trips = []
        # Hopefully we can do a single query across interchange points... perhaps
        for interchange_point in common_interchange_points:
            for trip in self.find_trips_direct(from_station, to_station,
                    from_time, to_time):
                start_to_interchange_trips.append(trip)




        return []
