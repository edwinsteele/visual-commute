from django.conf.urls import patterns, include, url

VCAPP_PREFIX="vcapp/"

urlpatterns = patterns('',
    # Examples:
    url(r'^%s' % (VCAPP_PREFIX,), include('vcapp.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
