from django.http import HttpResponse

from django.views.generic.base import TemplateView
from vcapp.models import Trip, Station
#from profile_decorator import profile

import logging, math

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
        context = {"trip_list": [t.id for t in trip_list],
                   "sparse": matrix,
                   "ordered_station_list": ordered_station_list,
        }
        return self.render_to_response(context)


class TripViewGraphicalClass(TemplateView):
    template_name = "vcapp/trip_graphical.html"
    MINOR_LINE_MARKER_LEN = 2
    MAJOR_LINE_MARKER_LEN = 4
    TEXT_HEIGHT = 10

    # Make left and right border padding about 2 characters wide.
    # It could be smaller if we know we only have 1 char in the hour label
    GRAPH_BORDER_PADDING_LEFT_PX = 35
    GRAPH_BORDER_PADDING_RIGHT_PX = 35
    GRAPH_BORDER_PADDING_TOP_PX = MAJOR_LINE_MARKER_LEN + TEXT_HEIGHT
    GRAPH_BORDER_PADDING_BOTTOM_PX = 5
    ABBREV = "timeVert"

    STATION_AXIS_TEXTALIGN = "left"
    STATION_AXIS_TEXTBASELINE = "bottom"
    HOUR_AXIS_TEXTALIGN = "right"
    HOUR_AXIS_TEXTBASELINE = "middle"
    START_LABEL_TEXTALIGN = "right"
    START_LABEL_TEXTBASELINE = "middle"
    END_LABEL_TEXTALIGN = "left"
    END_LABEL_TEXTBASELINE = "middle"

    def populate_station_point_map(self):
        departure_station = None
        arrival_station = None
        x_point_of_departure_station = None
        x_point_of_arrival_station = None

        # FIXME - needs to work for multiple trips
        t = Trip.objects.get(pk=self.trip_id)
        # don't need the matrix, just the stops...
        matrix = Trip.objects.get_stop_matrix([t])
        ordered_station_list = [station for station, dep_time_list in
                                matrix]
        for arrival_station_name in ordered_station_list:
            # FIXME - get_stop_matrix or something like it should return Station objects so this isn't neccesary
            arrival_station = Station.objects.filter(station_name=arrival_station_name)[0]
            if departure_station is None:
                # this is the first station we've come across
                x_point_of_departure_station = self.x_point_of_y_axis
                departure_station = arrival_station
                continue

            self.station_x_axis_point_map[departure_station] = \
                x_point_of_departure_station
            x_scaling_factor = (self.canvas_width -
                self.GRAPH_BORDER_PADDING_LEFT_PX -
                self.GRAPH_BORDER_PADDING_RIGHT_PX) / \
                               Trip.objects.get_max_trip_distance([t])
            x_point_of_arrival_station = math.floor(x_point_of_departure_station +
                (departure_station.distance_from(arrival_station) *
                 x_scaling_factor))
            # ready for the next iteration
            x_point_of_departure_station = x_point_of_arrival_station
            departure_station = arrival_station

        else:
            self.station_x_axis_point_map[departure_station.station_name] = \
                x_point_of_departure_station

#    def draw_station_axis(self):
#        self.write("ctx.save();\n")
#        self.write("ctx.textAlign = '%s';\n" % (self.STATION_AXIS_TEXTALIGN,))
#        self.write("ctx.textBaseline = '%s';\n" % (self.STATION_AXIS_TEXTBASELINE,))
#        allStations = self.tm.getAllStationsInTrips()
#        if debug:
#            stationList = allStations
#        else:
#            stationList = (allStations[0], allStations[-1])
#
#        for station in stationList:
#            self.write("//Station marker: %s\n" % (station.shortName(), ))
#            filltextArgs = (station.shortName(),) + self.stationOnStationAxisCoord(station.name)
#            self.write("ctx.fillText('%s', %s, %s);\n" % filltextArgs)
#        self.write("ctx.restore();\n")


    def get(self, request, *args, **kwargs):
        if "trip_id" in kwargs:
            self.trip_id = int(kwargs["trip_id"])
            trip_list = [Trip.objects.filter(id=self.trip_id)[0]]
        elif "trip_id_list" in kwargs:
            trip_id_list = [int(t) for t in kwargs["trip_id_list"].split(",")]
            trip_list = Trip.objects.filter(id__in=trip_id_list)
        else:
            trip_list=[]

        from_station_id = int(request.GET.get("from_station_id"))
        from_station = Station.objects.filter(pk=from_station_id)[0]
        to_station_id = int(request.GET.get("to_station_id"))
        to_station = Station.objects.filter(pk=to_station_id)[0]
        from_hour = int(request.GET.get("from_hour"))
        to_hour = int(request.GET.get("to_hour"))
        self.canvas_width = int(request.GET.get("canvas_width"))
        self.canvas_height = int(request.GET.get("canvas_height"))

        # From TimeVertHTMLDistanceTimeGraph.__init__
        self.x_point_of_y_axis = self.GRAPH_BORDER_PADDING_LEFT_PX
        self.y_point_of_x_axis = self.GRAPH_BORDER_PADDING_TOP_PX
        self.station_x_axis_point_map = {}

        self.populate_station_point_map()
#        self.draw_station_axis()

        context = {"from_station": from_station,
                   "to_station": to_station,
                   "from_hour": from_hour,
                   "to_hour": to_hour,
                   "canvas_width": self.canvas_width,
                   "canvas_height": self.canvas_height,
                   "text_height": self.TEXT_HEIGHT,
                   "abbrev": self.ABBREV,
        }

        return self.render_to_response(context)