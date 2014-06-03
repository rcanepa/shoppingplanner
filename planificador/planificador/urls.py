from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from planificador import views, settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.LoginView.as_view(), name="login"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', views.LoginView.as_view(), name="login"),
    url(r'^accounts/logout/$', views.LogoutView.as_view(), name='user_logout'),
    url(r'^accounts/loggedin/$', views.LoggedInView.as_view(), name='home'),
    url(r'^accounts/register/$', views.RegisterUserView.as_view(), name='user_register'),
    url(r'^accounts/register_success/$', views.RegisterSuccessView.as_view()),
    url(r'^accounts/list/$', views.UserListView.as_view(), name="user_list"),
    url(r'^accounts/detail/(?P<pk>\d+)/$', views.UserDetailView.as_view(), name='user_detail'),

    url(r'^categorias/',  include('categorias.urls', namespace="categorias")),
    url(r'^administracion/',  include('administracion.urls', namespace="administracion")),
    url(r'^planes/',  include('planes.urls', namespace="planes")),
    url(r'^organizaciones/',  include('organizaciones.urls', namespace="organizaciones")),
    url(r'^calendarios/',  include('calendarios.urls', namespace="calendarios")),
    url(r'^ventas/',  include('ventas.urls', namespace="ventas")),
)

# Configuracion para templates genericos de codigos de error
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^500/$', TemplateView.as_view(template_name="404.html")),
        (r'^404/$', TemplateView.as_view(template_name="404.html")),
        (r'^403/$', TemplateView.as_view(template_name="404.html")),
    )
