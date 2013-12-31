from django.conf.urls import patterns, include, url
from ventas import views

urlpatterns = patterns('',
	url(r'^controlventa/list/$', views.ControlventaListView.as_view(), name='controlventa_list'),
	url(r'^controlventa/detail/(?P<pk>\d+)/$', views.ControlventaDetailView.as_view(), name='controlventa_detail'),
    url(r'^controlventa/update/(?P<pk>\d+)/$', views.ControlventaUpdateView.as_view(), name='controlventa_update'),
    url(r'^controlventa/create/$', views.ControlventaCreateView.as_view(), name='controlventa_create'),
	#url(r'^calendario/delete/(?P<pk>\d+)/$', views.CalendarioDeleteView.as_view(), name='calendario_delete'),

)