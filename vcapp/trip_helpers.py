__author__ = 'esteele'

import transxchange_constants

MULTI_TRIP_LINE_ID = -1
MULTI_TRIP_TRIP_ID = -1
INTERCHANGE_TRIP_LINE_ID = -2
INTERCHANGE_TRIP_TRIP_ID = -2

class AbstractTrip(object):
    """
    Need to make this an old-skool abstract class/mixin as it seems one can't mix
    abc Abstract classes with Django using subclassing and the registration
    method for abc doesn't give registered classes available to the concrete
    method implementations that I want to share
    """

    def get_segments(self):
        raise NotImplementedError

    def as_summary_tuple(self):
        """
        list of tuples
        [(from station string, from station time,
         action string,
         to station string, to station time)]
        """
        raise NotImplementedError

    def get_trip_distance(self):
        return sum([segment.segment_length() for segment in self.get_segments()])

    def get_first_tripstop(self):
        return self.get_segments()[0].departure_tripstop

    def get_start_station(self):
        return self.get_segments()[0].departure_tripstop.station

    def get_start_hour(self):
        return self.get_segments()[0].departure_tripstop.departure_time.hour

    def get_start_time(self):
        return self.get_segments()[0].departure_tripstop.departure_time

    def get_last_tripstop(self):
        segs = self.get_segments()
        return segs[len(segs)-1].arrival_tripstop

    def get_end_station(self):
        return self.get_last_tripstop().station

    def get_end_time(self):
        return self.get_last_tripstop().departure_time

    def get_end_hour(self):
        # departure time of the arrival tripstop???
        return self.get_last_tripstop().departure_time.hour


class MultiTrip(AbstractTrip):
    def __init__(self, initial_trip):
        self._trip_list = [initial_trip]
        self.line_id = MULTI_TRIP_LINE_ID
        self.timetable_type = None
        self.id = MULTI_TRIP_TRIP_ID

    def add_trip(self, trip):
        self._trip_list.append(trip)

    def get_segments(self):
        segs = []
        for trip in self._trip_list:
            segs.extend(trip.get_segments())
        return segs

    def as_summary_tuple(self):
        summary_tuple_list = []
        for trip in self._trip_list:
            summary_tuple_list.extend(trip.as_summary_tuple())
        return summary_tuple_list


class InterchangeTrip(AbstractTrip):
    def __init__(self, from_tripstop, to_tripstop):
        from vcapp.models import Segment, Trip, Line
        self.line = Line.objects.get(
            line_name=transxchange_constants.INTERCHANGE_LINE_NAME)
        self.line_id = self.line.id
        self.timetable_type = None
        self._segment = Segment(departure_tripstop=from_tripstop,
            arrival_tripstop=to_tripstop,
            trip=Trip.objects.get(line=self.line)
            )

    def get_segments(self):
        return [self._segment]

    def as_summary_tuple(self):
        return [(self.get_start_station(), self.get_start_time(),
                "change to",
                self.get_end_station(), self.get_end_time())]

