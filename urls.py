from django.conf.urls.defaults import *
from galena.views import *
import os.path
from settings import MEDIA_ROOT
from django.contrib import admin
admin.autodiscover()

site_media = os.path.join( os.path.dirname(__file__), MEDIA_ROOT)

urlpatterns = patterns('',
    # Example:
    # (r'^omnium/', include('omnium.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),

    (r'^field/([A-Za-z0-9\-]+)/$', field),
    (r'^addriders/', addriders),
    (r'^addresults/', addresults),
    (r'^ftp/',ftp_results),
    (r'^save/',save_results),

    (r'^$', index),


    (r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': site_media }),

)
