from django.conf.urls import patterns, include, url

from administracion import views

urlpatterns = patterns('',
	url(r'^index/$', 'administracion.views.index'),
    #url(r'^get/(?P<categoria_id>\d+)/$', 'categorias.views.detail'),
    #url(r'^language/(?P<language>[a-z\-]+)/$', 'categorias.views.language'),
)