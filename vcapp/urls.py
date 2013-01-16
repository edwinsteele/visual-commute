from django.conf.urls import patterns, url
import vcapp.views

urlpatterns = patterns('',
    url(r'^$', vcapp.views.HomeClass.as_view()),
    url(r'^trip/(?P<trip_id>\d+)/$', vcapp.views.TripTabularDisplayViewClass.as_view()),
    url(r'^trip/(?P<trip_id_list>[\d,]+)/$',
        vcapp.views.TripTabularDisplayViewClass.as_view()),
    url(r'^trip_graph/(?P<trip_id>\d+)/$',
        vcapp.views.TripGraphicalDisplayViewClass.as_view()),
    url(r'^trip_graph/(?P<trip_id_list>[\d,]+)/$',
        vcapp.views.TripGraphicalDisplayViewClass.as_view()),
    url(r'^trip_finder_tabular/$',
        vcapp.views.TripFinderTabularViewClass.as_view()),
    url(r'^trip_finder_graphical/$',
        vcapp.views.TripFinderGraphicalViewClass.as_view()),
)
