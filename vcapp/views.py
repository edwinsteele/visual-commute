from django.http import HttpResponse

from django.views.generic.base import TemplateView
from vcapp.models import Trip, StationLineOrder
from profile_decorator import profile

import logging

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

class TripViewClass(TemplateView):
    template_name = "vcapp/trip.html"

    def get_stop_matrix(self):
        combined_sorted_station_list = self.get_ordered_station_list()

        # Create a sparse matrix
        sparse = {}
        for station in combined_sorted_station_list:
            sparse[station] = {}

        for t in self.trip_list:
            s = None
            for s in t.segment_set.select_related().all():
                sparse[s.departure_tripstop.station.station_name][s.trip_id] = \
                                         s.departure_tripstop.departure_time
            # Append the final arrival station (if there are any segments)
            if s:
                sparse[s.arrival_tripstop.station.station_name][s.trip_id] = \
                                         s.arrival_tripstop.departure_time

        s2 = []
        for station in combined_sorted_station_list:
            dep_time_list = []
            for t in self.trip_list:
                dep_time_list.append(sparse[station].get(t.id))
            s2.append([station, dep_time_list])

        return s2

    def get_ordered_station_list(self):
        station_set = set()
        for t in self.trip_list:
            seg = None
            for seg in t.segment_set.select_related().all():
                station_set.add(seg.departure_tripstop.station.station_name)
            if seg:
                station_set.add(seg.arrival_tripstop.station.station_name)

        line = self.trip_list[0].line
        # FIXME: The lookups in the key method result in lots of database calls
        #  Can they be moved to a manager or something that can prefetch them?
        return sorted(list(station_set), key=line.index_on_line)

    #@profile("TripViewClass.prof")
    def get(self, request, *args, **kwargs):
        if "trip_id" in kwargs:
            trip_id = int(kwargs["trip_id"])
            self.trip_list = [Trip.objects.filter(id=trip_id)[0]]
        elif "trip_id_list" in kwargs:
            trip_id_list = [int(t) for t in kwargs["trip_id_list"].split(",")]
            self.trip_list = Trip.objects.filter(id__in=trip_id_list)
        else:
            self.trip_list=[]

        context = {"trip_list": [t.id for t in self.trip_list],
                   "sparse": self.get_stop_matrix(),
                   "ordered_station_list": self.get_ordered_station_list(),
        }
        return self.render_to_response(context)

