from django.conf.urls import patterns, include, url
from calendarios import views

urlpatterns = patterns('',
	url(r'^calendario/list/$', views.CalendarioListView.as_view(), name='calendario_list'),
	#url(r'^calendario/detail/(?P<pk>\d+)/$', views.CalendarioDetailView.as_view(), name='calendario_detail'),
    #url(r'^calendario/update/(?P<pk>\d+)/$', views.CalendarioUpdateView.as_view(), name='calendario_update'),
    url(r'^calendario/create/$', views.CalendarioCreateView.as_view(), name='calendario_create'),
	#url(r'^calendario/delete/(?P<pk>\d+)/$', views.CalendarioDeleteView.as_view(), name='calendario_delete'),

)