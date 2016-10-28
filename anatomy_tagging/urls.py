from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.http import HttpResponse

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    'anatomy_tagging.views',
    url(r'^$', 'home', name='home'),
    url(r'^home/[\w\.-]*', 'home', name='home'),
    url(r'^image/update$', 'image_update', name='image'),
    url(r'^image/[\w\.-]*$', 'home', name='image'),
    url(r'^terms/[\w\.-]*$', 'home', name='image'),
    url(r'^relations/[\w\.-]*$', 'home', name='image'),
    url(r'^practice/[\w\.-]*$', 'home', name='image'),

    url(r'^imagejson/$', 'images_json', name='images'),
    url(r'^imagejson/e$', 'images_json', name='images'),
    url(r'^imagejson/(?P<filename_slug>[\w\.-]*)$', 'image_json', name='image'),
    url(r'^termsjson/update$', 'update_term', name='terms'),
    url(r'^termsjson/merge$', 'merge_terms', name='merge_terms'),
    url(r'^termsjson/(?P<filename_slug>[\w\.-]*)$', 'terms', name='terms'),

    url(r'^relationsjson/update$', 'update_relations', name='update_relations'),
    url(r'^relationsjson/(?P<wiki_page>[\w\.-]*)$', 'relations_json', name='relations_json'),
    url(r'^relationsexport/(?P<relation_type>[\w\.-]*)$', 'relations_export', name='relations_export'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^favicon\.ico$', RedirectView.as_view(url='static/img/favicon.png')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^robots.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /", content_type="text/plain"))

)
