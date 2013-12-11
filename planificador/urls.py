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
    url(r'^accounts/logout/$', 'planificador.views.logout', name='user_logout'),
    url(r'^accounts/loggedin/$', views.LoggedInView.as_view(), name='home'),
    url(r'^accounts/invalid/$', views.InvalidLogin.as_view()),
    url(r'^accounts/register/$', views.RegisterUserView.as_view(), name='user_register'),
    url(r'^accounts/register_success/$', views.RegisterSuccessView.as_view()),
    url(r'^accounts/list/$', views.UserListView.as_view(), name="user_list"),
    url(r'^accounts/detail/(?P<pk>\d+)/$', views.UserDetailView.as_view(), name='user_detail'),

    url(r'^categorias/',  include('categorias.urls', namespace="categorias")),
    url(r'^administracion/',  include('administracion.urls', namespace="administracion")),
    url(r'^planes/',  include('planes.urls', namespace="planes")),
    url(r'^organizaciones/',  include('organizaciones.urls', namespace="organizaciones")),
    url(r'^calendarios/',  include('calendarios.urls', namespace="calendarios")),
)