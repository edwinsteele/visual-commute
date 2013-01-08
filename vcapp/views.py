from django.views.generic.base import TemplateView
from vcapp.models import Trip, Station
#from profile_decorator import profile

import datetime, logging, math

logger = logging.getLogger(__name__)

class HomeClass(TemplateView):
    template_name = "vcapp/home.html"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})


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
        context = {"trip_list": [t.id for t in trip_list],
                   "sparse": matrix,
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
        x_point_of_departure_station = None

        ordered_station_list = Trip.objects.get_all_stations_in_trips(self.trip_list)
        for arrival_station in ordered_station_list:
            if departure_station is None:
                # this is the first station we've come across
                x_point_of_departure_station = self.x_point_of_y_axis
                departure_station = arrival_station
                continue

            self.station_x_axis_point_map[departure_station] = \
                x_point_of_departure_station
            x_point_of_arrival_station = math.floor(x_point_of_departure_station +
                (departure_station.distance_from(arrival_station) *
                 self.x_scaling_factor))
            # ready for the next iteration
            x_point_of_departure_station = x_point_of_arrival_station
            departure_station = arrival_station

        else:
            self.station_x_axis_point_map[departure_station] = \
                x_point_of_departure_station

    def station_to_x_point(self, station):
        return self.station_x_axis_point_map[station]

    def station_on_station_axis_coord(self, station):
        return self.station_to_x_point(station), self.y_point_of_x_axis

    def draw_station_axis(self):
        content_list = ["ctx.save();",
            "ctx.textAlign = '%s';" % (self.STATION_AXIS_TEXTALIGN,),
            "ctx.textBaseline = '%s';" % (self.STATION_AXIS_TEXTBASELINE,)]
        all_stations = Trip.objects.get_all_stations_in_trips(self.trip_list)
        # when debugging, we want all stations, otherwise just the start and
        #  the end. work out how to set a debug flag later
        if False:
            station_list = all_stations
        else:
            station_list = (all_stations[0], all_stations[-1])

        for station in station_list:
            content_list.append("//Station marker: %s" % (station.short_name(), ))
            sosac = self.station_on_station_axis_coord(station)
            content_list.append("ctx.fillText('%s', %s, %s);" % \
                (station.short_name(), sosac[0], sosac[1]))
        content_list.append("ctx.restore();\n")
        return content_list


    def get_min_timedelta_from_list_of_times(self, dtt_list):
        """
        Takes a list of datetime.time elements and returns the smallest gap
         between two consecutive times

        Poorly named. More specific than the name suggests
        """
        # FIXME - improving naming of this method...
        dtt_list.sort()
        last_time_as_td = None
        # start with the maximum period of time represented on the graph
        #  as the minTripDelta - if there is only one trip on the graph then
        #  the gap calculation should make sense (unlike timedelta.max)
        min_trip_delta = datetime.timedelta(hours=
            int(self.to_hour) - int(self.from_hour))
        for dtt in dtt_list:
            this_time_as_td = datetime.timedelta(hours=dtt.hour, minutes=dtt.minute)
            # Ignore if this is the first reading
            # Ignore if it's the same time as the last time as we can have several
            #  trips starting at the same time (i.e. it isn't a rendering problem)
            if this_time_as_td is not None and \
                   last_time_as_td is not None and \
                   this_time_as_td != last_time_as_td:
                gap = this_time_as_td - last_time_as_td
                min_trip_delta = min(min_trip_delta, gap)
            last_time_as_td = this_time_as_td

        return min_trip_delta

    def get_min_start_hour_for_trips(self):
        # What about the fact that midnight (0) comes after 11pm (23)?
        return reduce(min, [t.get_start_hour() for t in self.trip_list], 23)

    def get_max_end_hour_for_trips(self):
        # What about the fact that 11pm (23) comes before midnight (0)?
        return reduce(max, [t.get_end_hour() for t in self.trip_list], 0)

    def calculate_scaling_factors(self):
        # Note that maxHour is the largest hour e.g if the largest time is
        #  7:15, then the largest hour is 7. This means that in order to get
        #  the correct scaling factor, we need to add 1 to the maxhour because
        #  we need to show up to 59mins past the hour on the x axis
        self.y_scaling_factor = \
            (self.canvas_height - self.GRAPH_BORDER_PADDING_TOP_PX -
             self.GRAPH_BORDER_PADDING_BOTTOM_PX) /\
            (self.max_end_hour_for_trips + 1 -
             self.min_start_hour_for_trips)

        self.x_scaling_factor = (self.canvas_width -
                            self.GRAPH_BORDER_PADDING_LEFT_PX -
                            self.GRAPH_BORDER_PADDING_RIGHT_PX) /\
                        Trip.objects.get_max_trip_distance(self.trip_list)

    def datetime_to_y_point(self, dt):
        # round (down) it as we don't want to do subpixel stuff
        return math.floor(self.GRAPH_BORDER_PADDING_TOP_PX +
              (dt.hour + dt.minute/60.0 - self.min_start_hour_for_trips)
              * self.y_scaling_factor)

    def are_gaps_above_pixel_resolution(self, list_of_times):
        min_gap = self.get_min_timedelta_from_list_of_times(list_of_times)
        # get a point on the graph to see how many pixels the min gap covers
        example_point_as_dtdt = datetime.datetime.combine(
            datetime.datetime.now(),
            list_of_times[0])
        min_gap_in_px = self.datetime_to_y_point(
            example_point_as_dtdt + min_gap) - \
            self.datetime_to_y_point(example_point_as_dtdt)
        # Text height +1 pixel between means the times would be readable
        if min_gap_in_px < (self.TEXT_HEIGHT + 1):
            logging.debug("times are too small to show (%s px/ %s)."
                "Use hour axis on the left", min_gap_in_px, min_gap)
            return False
        else:
            logging.debug("times are spaced well (%s px/ %s)."
                "Use labels on the left" , min_gap_in_px, min_gap)
            return True

    def draw_hour_grid_line(self, hourLabel, thisHour):
        return ["//Grid line at %s" % (hourLabel,),
                "drawHourGridLineJS(ctx, %s, %s, %s, %s);" %
                   (self.x_point_of_y_axis,
                    self.datetime_to_y_point(datetime.time(thisHour)),
                    self.canvas_width - self.GRAPH_BORDER_PADDING_RIGHT_PX,
                    self.datetime_to_y_point(datetime.time(thisHour)))]

    def coords_of_datetime_on_hour_axis(self, dt):
        return (self.x_point_of_y_axis, self.datetime_to_y_point(dt))

    def draw_sub_hour_markers(self, this_hour):
        extra_content = []
        for minute in range(15, 60, 15):
            extra_content.append("//sub-hour line: %s:%s" % (this_hour, minute))
            extra_content.append("ctx.beginPath();")
            # We use TEXT_HEIGHT/2 because we want the dot to be aligned with
            #  the middle of the hour label
            extra_content.append("ctx.moveTo(%s,%s);" % \
               (self.x_point_of_y_axis - (self.TEXT_HEIGHT/2),
                self.datetime_to_y_point(datetime.time(this_hour, minute))))
            extra_content.append("ctx.lineTo(%s,%s);" % \
               (self.x_point_of_y_axis - (self.TEXT_HEIGHT/2) -
                self.MINOR_LINE_MARKER_LEN,
                self.datetime_to_y_point(datetime.time(this_hour, minute))))
            extra_content.append("ctx.stroke();")
        return extra_content

    def draw_hour_axis(self):
        #  we need to show up to 59mins past the hour on the x axis
        hour = None
        extra_content = ["ctx.save();",
            "ctx.textAlign = '%s';" % (self.HOUR_AXIS_TEXTALIGN,),
            "ctx.textBaseline = '%s';" % (self.HOUR_AXIS_TEXTBASELINE,)]

        # Note that getMaxEndHour is the largest hour e.g if the largest time is
        #  7:15, then the largest hour is 7. This means that in order to get
        #  the correct scaling factor, we need to add 1 to the maxhour because
        # getMaxEndHour + 1 because the range function isn't inclusive
        for hour in range(self.min_start_hour_for_trips,
                self.max_end_hour_for_trips + 1):
            extra_content.extend(self.draw_hour_grid_line(hour, hour))
            extra_content.append("//Hour marker: %s" % (hour,))
            codtoha = self.coords_of_datetime_on_hour_axis(datetime.time(hour))
            extra_content.append("ctx.fillText('%s', %s, %s);" % \
                                 (hour, codtoha[0], codtoha[1]))
            extra_content.extend(self.draw_sub_hour_markers(hour))

        if hour is not None:
            extra_content.extend(self.draw_hour_grid_line(hour + 1, hour + 1))
            extra_content.append("//Hour marker: %s" % (hour + 1,))
            codtoha = self.coords_of_datetime_on_hour_axis(datetime.time(hour + 1))
            extra_content.append("ctx.fillText('%s', %s, %s);" % \
                                (hour + 1, codtoha[0], codtoha[1]))

        extra_content.append("ctx.restore();")
        return extra_content

    def draw_time_label(self, tripstop, label_type):
        textalign = getattr(self, label_type + "_LABEL_TEXTALIGN")
        textBaseline = getattr(self, label_type + "_LABEL_TEXTBASELINE")
        extra_content = ["ctx.save();",
                         "ctx.textAlign = '%s';" % (textalign,),
                         "ctx.textBaseline = '%s';" % (textBaseline,)]
        label_x_point = self.station_to_x_point(tripstop.station)
        label_y_point = self.datetime_to_y_point(tripstop.departure_time)
        extra_content.append("//%s label: %s" %\
             (label_type,
              tripstop.departure_time.strftime("%H.%M"), ))
        extra_content.append("ctx.fillText('%s ', %s, %s);" %\
             (tripstop.departure_time.strftime("%H.%M"),
              label_x_point,
              label_y_point))
        extra_content.append("ctx.restore();")
        return extra_content

    def get_segment_line_colour(self, line_id):
        # FIXME - trips may or may not have more than one colour depending
        #  on how many lines make up a trip (or whether a trip can actually
        #  span more than one line
        if line_id in (1,2):
            return "#c5c5c5"
        elif line_id in (3,4):
            return "#fcb514"
        elif line_id == -1:
            # Interchange
            return "black"
        else:
            return "red"
            #return ["red", "orange", "yellow", "green", "blue", "purple"][random.randint(0, 5)]

    def get_segment_bullet_colour(self, line_id):
        if line_id in (1,2):
            return "#fcb514"
        elif line_id in (3,4):
            return "#fcb514"
        elif line_id == -1:
            # Interchange
            return "black"
        else:
            return "green"

    def draw_segment(self, segment):
        # Note that because this draws a circle at the start and end of the
        #  segment, we're actually drawing circles for all but the first
        #  departure station and the last arrival station twice. meh.
        dts = segment.departure_tripstop
        ats = segment.arrival_tripstop
        extra_content = ["//Segment: %s (%s) to %s (%s)" % \
                   (dts.station.short_name(),
                    dts.departure_time,
                    ats.station.short_name(),
                    ats.departure_time)]
        departure_x_point = self.station_to_x_point(dts.station)
        arrival_x_point = self.station_to_x_point(ats.station)
        departure_y_point = self.datetime_to_y_point(dts.departure_time)
        arrival_y_point = self.datetime_to_y_point(ats.departure_time)
        extra_content.append("drawSegmentJS(ctx, %s, %s, %s, %s, '%s', '%s');" %\
                   (departure_x_point, departure_y_point,
                    arrival_x_point, arrival_y_point,
                    self.get_segment_line_colour(segment.trip.line_id),
                    self.get_segment_bullet_colour(segment.trip.line_id)))
        return extra_content

    def draw_trip(self, trip_to_draw, draw_start_label, draw_end_label):
        extra_content = []
        segments = trip_to_draw.get_segments()
        trip_departure_tripstop = segments[0].departure_tripstop
        trip_arrival_tripstop = segments[len(segments)-1].arrival_tripstop

        if draw_start_label:
            extra_content.extend(self.draw_time_label(trip_departure_tripstop, "START"))

        for segment in segments:
            extra_content.extend(self.draw_segment(segment))

        if draw_end_label:
            extra_content.extend(self.draw_time_label(trip_arrival_tripstop, "END"))

        return extra_content

    def draw_trips(self):
#        allTrips = self.tm.getTrips()
        extra_content = []
        trip_departure_times = []
        trip_arrival_times = []
        for trip in self.trip_list:
            trip_segments = trip.get_segments()
            trip_departure_times.append(trip_segments[0].departure_tripstop.departure_time)
            trip_arrival_times.append(trip_segments[len(trip_segments)-1].arrival_tripstop.departure_time)

        draw_start_label = self.are_gaps_above_pixel_resolution(trip_departure_times)
        draw_end_label = self.are_gaps_above_pixel_resolution(trip_arrival_times)

        if not draw_start_label:
            #Draw an axis instead
            extra_content.extend(self.draw_hour_axis())

        for trip in self.trip_list:
            extra_content.extend(
                self.draw_trip(trip, draw_start_label, draw_end_label)
            )

        return extra_content

    def get(self, request, *args, **kwargs):
        if "trip_id" in kwargs:
            self.trip_id = int(kwargs["trip_id"])
            self.trip_list = [Trip.objects.filter(id=self.trip_id)[0]]
        elif "trip_id_list" in kwargs:
            trip_id_list = [int(t) for t in kwargs["trip_id_list"].split(",")]
            self.trip_list = Trip.objects.filter(id__in=trip_id_list)
        else:
            self.trip_list=[]

        from_station_id = int(request.GET.get("from_station_id"))
        from_station = Station.objects.filter(pk=from_station_id)[0]
        to_station_id = int(request.GET.get("to_station_id"))
        to_station = Station.objects.filter(pk=to_station_id)[0]
        self.from_hour = int(request.GET.get("from_hour"))
        self.to_hour = int(request.GET.get("to_hour"))
        self.canvas_width = int(request.GET.get("canvas_width"))
        self.canvas_height = int(request.GET.get("canvas_height"))

        # From TimeVertHTMLDistanceTimeGraph.__init__
        self.x_point_of_y_axis = self.GRAPH_BORDER_PADDING_LEFT_PX
        self.y_point_of_x_axis = self.GRAPH_BORDER_PADDING_TOP_PX
        self.station_x_axis_point_map = {}

        # Fetch end before start to save a query (start slices the qs, but end
        #  doesn't
        self.max_end_hour_for_trips = self.get_max_end_hour_for_trips()
        self.min_start_hour_for_trips = self.get_min_start_hour_for_trips()

        self.calculate_scaling_factors()
        self.populate_station_point_map()
        extra_content_list = self.draw_station_axis()
        extra_content_list.extend(self.draw_trips())
        extra_content_str = "\n".join(extra_content_list)

        context = {"from_station": from_station,
                   "to_station": to_station,
                   "from_hour": self.from_hour,
                   "to_hour": self.to_hour,
                   "canvas_width": self.canvas_width,
                   "canvas_height": self.canvas_height,
                   "text_height": self.TEXT_HEIGHT,
                   "abbrev": self.ABBREV,
                   "extra_content_str": extra_content_str,
        }

        return self.render_to_response(context)