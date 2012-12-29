from django.http import HttpResponse

from django.views.generic.base import TemplateView
from vcapp.models import Trip

import logging

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

class TripViewClass(TemplateView):
    template_name = "vcapp/trip.html"

    def initialise_stop_matrix(self):
        self.stop_matrix = []
        self.trip_list = []

    def add_trip_to_stop_matrix(self, trip):
        self.trip_list.append(trip)
        s = None
        for s in trip.get_segments():
            self.stop_matrix.append((s.departure_tripstop.station.station_name,
                s.trip.id,
                s.departure_tripstop.departure_time))
        # Append the final arrival station (if there are any segments)
        if s:
            self.stop_matrix.append((s.arrival_tripstop.station.station_name,
                                     s.trip.id,
                                     s.arrival_tripstop.departure_time))

    def get_stop_matrix(self):
        combined_sorted_station_list = self.get_ordered_station_list()

        # Create a sparse matrix
        sparse = {}
        for station in combined_sorted_station_list:
            sparse[station] = {}

        # Initialise with empty value
        for t in self.trip_list:
            for station in combined_sorted_station_list:
                logging.debug("Inserting empty for trip %s station %s", t.id, station)
                sparse[station][str(t.id)] = None

        # Then populate properly
        for station, trip_id, departure_time in self.stop_matrix:
            logging.debug("Inserting proper for trip %s station %s", trip_id, station)
            sparse[station][str(trip_id)] = departure_time

        s2 = []
        for station in combined_sorted_station_list:
            dep_time_list = []
            for dep_time in sparse[station].itervalues():
                dep_time_list.append(dep_time)
            s2.append([station, dep_time_list])

        logging.info("Sparse is %s", sparse)
        logging.info("S2 is %s", s2)
        return s2

    def get_ordered_station_list(self):
        station_set = set()
        for t in self.trip_list:
            seg = None
            for seg in t.get_segments():
                station_set.add(seg.departure_tripstop.station.station_name)
            if seg:
                station_set.add(seg.arrival_tripstop.station.station_name)

        line = self.trip_list[0].line
        return sorted(list(station_set), key=line.index_on_line)

    def get(self, request, *args, **kwargs):
        if "trip_id" in kwargs:
            trip_id = int(kwargs["trip_id"])
            trip_list = [Trip.objects.filter(id=trip_id)[0]]
        elif "trip_id_list" in kwargs:
            trip_id_list = [int(t) for t in kwargs["trip_id_list"].split(",")]
            trip_list = Trip.objects.filter(id__in=trip_id_list)
        else:
            trip_list=[]

        self.initialise_stop_matrix()
        for t in trip_list:
            self.add_trip_to_stop_matrix(t)
        z = [t.id for t in trip_list]
        matrix = self.get_stop_matrix()
        osl = self.get_ordered_station_list()
        logging.info(osl)
        context = {"trip_list": z,
                   "sparse": matrix,
                   "ordered_station_list": osl,
        }
        return self.render_to_response(context)

