from django.conf.urls import patterns, include, url

from planes import views

urlpatterns = patterns('',
    url(r'^index/$', views.IndexView.as_view(), name='index'),

    url(r'^temporada/list/$', views.TemporadaListView.as_view(), name='temporada_list'),
    url(r'^temporada/create/$', views.TemporadaCreateView.as_view(), name='temporada_create'),
    url(r'^temporada/detail/(?P<pk>\d+)/$', views.TemporadaDetailView.as_view(), name='temporada_detail'),
    url(r'^temporada/update/(?P<pk>\d+)/$', views.TemporadaUpdateView.as_view(), name='temporada_update'),
    url(r'^temporada/delete/(?P<pk>\d+)/$', views.TemporadaDeleteView.as_view(), name='temporada_delete'),

    url(r'^plan/list/$', views.PlanListView.as_view(), name='plan_list'),
    url(r'^plan/create/$', views.PlanCreateView.as_view(), name='plan_create'),
    url(r'^plan/detail/(?P<pk>\d+)/$', views.PlanDetailView.as_view(), name='plan_detail'),
    url(r'^plan/delete/(?P<pk>\d+)/$', views.PlanDeleteView.as_view(), name='plan_delete'),

    url(r'^plan/stage1/(?P<pk>\d+)/$', views.PlanTreeDetailView.as_view(), name='plan_tree_detail'),
    url(r'^plan/savestage1/$', views.GuardarArbolView.as_view()),
    url(r'^plan/stage2/(?P<pk>\d+)/$', views.ProyeccionesView.as_view(), name='plan_proyecciones_detail'),
    url(r'^plan/savestage2/$', views.GuardarProyeccionView.as_view()),
    url(r'^plan/itemplansearchlist/$', views.BuscarItemplanListProyeccionView.as_view()),
    #url(r'^plan/itemplansearch/$', views.BuscarItemplanProyeccionView.as_view()),
    url(r'^plan/itemplanventasearch/$', views.BuscarVentaItemplanProyeccionView.as_view()),

    url(r'^plan/categoriasearchlist/$', views.BuscarCategoriaListProyeccionView.as_view()),
)
