from django.http import HttpResponse

from django.views.generic.base import TemplateView
from vcapp.models import Trip
from collections import OrderedDict

import logging

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

class TripViewClass(TemplateView):
    template_name = "vcapp/trip.html"

    def initialise_stop_matrix(self):
        self.stop_matrix = []

    def add_trip_to_stop_matrix(self, trip):
        for s in trip.get_segments():
            self.stop_matrix.append((s.departure_tripstop.station.station_name,
                s.trip.id,
                s.departure_tripstop.departure_time))
        else:
            self.stop_matrix.append((s.arrival_tripstop.station.station_name,
                                     s.trip.id,
                                     s.arrival_tripstop.departure_time))

    def get_stop_matrix(self):
        station_list = list(set([station for station, dummy1, dummy2 in
                                self.stop_matrix]))
        trip_list = list(set([trip_id for dummy1, trip_id, dummy2 in
                                self.stop_matrix]))

        # FIXME - sort the station list so that it appears in the order that
        #  a train would encounter it
        # Create a sparse matrix
        sparse = OrderedDict()
        for station in station_list:
            sparse[station] = {}

        # Initialise with empty value
        for trip_id in trip_list:
            for station in station_list:
                sparse[station][trip_id] = None

        # Then populate properly
        for station, trip_id, departure_time in self.stop_matrix:
            sparse[station][trip_id] = departure_time

        s2 = OrderedDict()
        for station in sparse.keys():
            s2[station] = []
            for trip_id in sparse[station].keys():
                s2[station].append(sparse[station][trip_id])

        return s2

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
        sparse = self.get_stop_matrix()
        context = {"trip_list": trip_list,
                   "sparse": sparse,}
        return self.render_to_response(context)

