from django.http import HttpResponse

from django.views.generic.base import TemplateView
from vcapp.models import Trip, StationLineOrder
#from profile_decorator import profile

import logging

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, world. You're at the poll index.")

class TripViewClass(TemplateView):
    template_name = "vcapp/trip.html"

    #@profile("TripViewClass.prof")
    def get(self, request, *args, **kwargs):
        if "trip_id" in kwargs:
            trip_id = int(kwargs["trip_id"])
            trip_list = [Trip.objects.filter(id=trip_id)[0]]
        elif "trip_id_list" in kwargs:
            trip_id_list = [int(t) for t in kwargs["trip_id_list"].split(",")]
            trip_list = Trip.objects.filter(id__in=trip_id_list)
        else:
            trip_list=[]

        matrix = Trip.objects.get_stop_matrix(trip_list)
        ordered_station_list = [station for station, dep_time_list in
            matrix]
        logging.info("matrix: %s", matrix)
        logging.info("OSL: %s", ordered_station_list)
        context = {"trip_list": [t.id for t in trip_list],
                   "sparse": matrix,
                   "ordered_station_list": ordered_station_list,
        }
        return self.render_to_response(context)

