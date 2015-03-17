from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    'anatomy_tagging.views',
    url(r'^$', 'home', name='home'),
    url(r'^home/[\w\.-]*', 'home', name='home'),
    url(r'^image/update$', 'image_update', name='image'),
    url(r'^image/[\w\.-]*$', 'home', name='image'),
    url(r'^terms/[\w\.-]*$', 'home', name='image'),
    url(r'^imagejson/$', 'images_json', name='images'),
    url(r'^imagejson/e$', 'images_json', name='images'),
    url(r'^imagejson/(?P<filename_slug>[\w\.-]*)$', 'image_json', name='image'),
    url(r'^termsjson/update$', 'update_term', name='terms'),
    url(r'^termsjson/(?P<filename_slug>[\w\.-]*)$', 'terms', name='terms'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),

)
