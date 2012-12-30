from django.conf.urls import patterns, include, url
import vcapp.views

urlpatterns = patterns('',
    url(r'^$', 'vcapp.views.home', name='home'),
    url(r'^trip/(?P<trip_id>\d+)/$', vcapp.views.TripViewClass.as_view()),
    url(r'^trip/(?P<trip_id_list>[\d,]+)/$',
        vcapp.views.TripViewClass.as_view()),
    url(r'^trip_graph/(?P<trip_id>\d+)/$',
        vcapp.views.TripViewGraphicalClass.as_view()),
)
