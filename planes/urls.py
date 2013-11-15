from django.conf.urls import patterns, include, url

from planes import views

urlpatterns = patterns('',
    url(r'^index/$', views.IndexView.as_view(), name='index_list'),
    url(r'^plan/list/$', views.PlanListView.as_view(), name='plan_list'),
    url(r'^plan/create/$', views.PlanCreateView.as_view(), name='plan_create'),
    url(r'^plan/detail/(?P<pk>\d+)/$', views.PlanDetailView.as_view(), name='plan_detail'),
    url(r'^plan/delete/(?P<pk>\d+)/$', views.PlanDeleteView.as_view(), name='plan_delete'),

    url(r'^plan/stage1/(?P<pk>\d+)/$', views.PlanTreeDetailView.as_view(), name='plan_tree_detail'),
    url(r'^plan/savestage1/$', views.GuardarArbolView.as_view()),
    url(r'^plan/stage2/(?P<pk>\d+)/$', views.ProyeccionesView.as_view(), name='plan_proyecciones_detail'),
    url(r'^plan/savestage2/$', views.GuardarProyeccionView.as_view()),
)
