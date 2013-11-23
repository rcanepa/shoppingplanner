from django.conf.urls import patterns, include, url
from planificador import views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'planificador.views.home', name='home'),
    # url(r'^planificador/', include('planificador.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'planificador.views.login'),
    url(r'^accounts/auth/$', 'planificador.views.auth_view'),
    url(r'^accounts/logout/$', 'planificador.views.logout'),
    url(r'^accounts/loggedin/$', 'planificador.views.loggedin'),
    url(r'^accounts/invalid/$', 'planificador.views.invalid_login'),
    url(r'^accounts/register/$', 'planificador.views.register_user'),
    #url(r'^accounts/register_success/$', 'planificador.views.register_success'),
    url(r'^accounts/register_success/$', views.RegisterSuccessView.as_view()),
    url(r'^accounts/list/$', views.UserListView.as_view(), name="list_user"),
    url(r'^categorias/',  include('categorias.urls', namespace="categorias")),
    url(r'^administracion/',  include('administracion.urls', namespace="administracion")),
    url(r'^planes/',  include('planes.urls', namespace="planes")),
    url(r'^organizaciones/',  include('organizaciones.urls', namespace="organizaciones")),
    url(r'^calendarios/',  include('calendarios.urls', namespace="calendarios")),
)
