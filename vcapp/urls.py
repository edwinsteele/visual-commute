from django.conf.urls import patterns, include, url
import vcapp.views

urlpatterns = patterns('vcapp.views',
    url(r'^$', 'home', name='home'),
    url(r'^latest$', sensors.views.LatestViewClass.as_view(), name='latest'),
)
