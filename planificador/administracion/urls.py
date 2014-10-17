from django.conf.urls import patterns, include, url

from administracion import views

urlpatterns = patterns('',
    url(r'^index/$', views.AdminView.as_view(), name='index'),
    url(r'^indexAngular/$', views.AdminAngularView.as_view(), name='index'),
    url(r'^$', views.AdminView.as_view(), name="index"),
)
