
import datetime
from django.db import models
from .trip_helpers import MultiTrip, InterchangeTrip


class TripManager(models.Manager):
    MIN_TIME_AT_INTERCHANGE = datetime.timedelta(minutes=2)
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
            for slo in StationLineOrder.objects.select_related().\
                    filter(line=line_id):
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
            segment__departure_tripstop__station__station_name=
            from_station.station_name,
            segment__departure_tripstop__departure_time__gte=from_time,
        ).filter(
            segment__arrival_tripstop__station__station_name=
            to_station.station_name,
            segment__arrival_tripstop__departure_time__lt=to_time,
        ).extra(
            # To make sure the trip is in the right direction
            # This will need to change when we start accepting trips over
            #  midnight
            where=['vcapp_tripstop.departure_time < T6."departure_time"']
        )
        for trip in trip_list:
            trip.starting_endpoint = from_station
            trip.finishing_endpoint = to_station
        return trip_list

    def get_interchange_points_between_stations(self, from_station, to_station):
        from vcapp.models import StationLineOrder, InterchangeStation
        lines_containing_from_station = [
            slo.line for slo in
            StationLineOrder.objects.filter(station=from_station)
        ]
        lines_containing_to_station = [
            slo.line for slo in
            StationLineOrder.objects.filter(station=to_station)
        ]
        from_station_line_interchange_stations = set()
        to_station_line_interchange_stations = set()
        for line_containing_from_station in lines_containing_from_station:
            interchange_stations_on_line = InterchangeStation.objects.filter(
                line=line_containing_from_station
            )
            for interchange_station in interchange_stations_on_line:
                from_station_line_interchange_stations.add(interchange_station)

        for line_containing_to_station in lines_containing_to_station:
            interchange_stations_on_line = InterchangeStation.objects.filter(
                line=line_containing_to_station
            )
            for interchange_station in interchange_stations_on_line:
                to_station_line_interchange_stations.add(interchange_station)

        return from_station_line_interchange_stations.union(
            to_station_line_interchange_stations)

    def find_trips_indirect(self, from_station, to_station, from_time, to_time):
        indirect_trips = []

        common_interchange_points = \
            self.get_interchange_points_between_stations(
                from_station, to_station
            )
#        logging.debug("CIPs are %s", common_interchange_points)
        # Get points from "from station" to interchange point
        start_to_interchange_trips = []
        # Hopefully we can do a single query across interchange points.. perhaps
        for interchange_point in common_interchange_points:
#            logging.debug("Interchange point is %s", interchange_point)
            for start_to_interchange_trip in self.find_trips_direct(
                    from_station,
                    interchange_point.station,
                    from_time, to_time):
                start_to_interchange_trips.append(start_to_interchange_trip)

        # find trips from interchange points to the endpoint that leave the
        #  interchange station no less than 2 minutes (say) after the train
        #  arrives at the interchange point
        for start_to_interchange_trip in start_to_interchange_trips:
            earliest_interchange_departure_time = datetime.datetime.combine(
                datetime.date.today(),
                start_to_interchange_trip.get_end_time()
            ) + self.MIN_TIME_AT_INTERCHANGE
            interchange_to_end_trips = self.find_trips_direct(
                start_to_interchange_trip.get_end_station(),
                to_station,
                earliest_interchange_departure_time.time(),
                to_time,
            )
            for interchange_to_end_trip in interchange_to_end_trips:
                m = MultiTrip(start_to_interchange_trip)
                # we need to create an interchange "trip" but we need to make
                #  sure that it'll be used when we create our graph (so we prob
                #  need to include the line_id in the node name
                m.add_trip(InterchangeTrip(
                    start_to_interchange_trip.get_last_tripstop(),
                    interchange_to_end_trip.get_first_tripstop()
                ))
                m.add_trip(interchange_to_end_trip)
                indirect_trips.append(m)

        # to reduce the amount of options, we should return the best "n" trips
        #  where best is defined as one of two specified criteria:
        # * arrives first
        # * has the shortest trip duration

        # to reduce the amount of lookups and objects that are constructed we
        #  cou;ld make the algo iterative, running n times and only continuing
        #  to consider more stations if we get a better result?
        return indirect_trips
