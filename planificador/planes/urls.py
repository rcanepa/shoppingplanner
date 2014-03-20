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

    # Vistas relacionadas a la seleccion del arbol de planificacion
    url(r'^plan/arbol-planificacion/(?P<pk>\d+)/$', views.PlanTreeDetailView.as_view(), name='plan_tree_detail'),
    url(r'^plan/savestage1/$', views.GuardarArbolView.as_view()),

    # Vistas relacionadas a las proyecciones
    url(r'^plan/proyeccion/(?P<pk>\d+)/$', views.ProyeccionesView.as_view(), name='plan_proyecciones_detail'),
    url(r'^plan/savestage2/$', views.GuardarProyeccionView.as_view()),
    url(r'^plan/itemplanventasearch/$', views.BuscarVentaItemplanProyeccionView.as_view()),
    url(r'^plan/itemplancompventasearch/$', views.BuscarVentaItemplanCompProyeccionView.as_view()),
    url(r'^plan/categoriasearchlist/$', views.BuscarCategoriaListProyeccionView.as_view()),
    url(r'^plan/categoriacompsearchlist/$', views.BuscarCategoriaListCompProyeccionView.as_view()),
    url(r'^plan/proystats/$', views.BuscarStatsProyeccionView.as_view()),
    
    # Para testing
    #url(r'^plan/test_ventas/$', views.BuscarStatsProyeccionView.as_view()),

    # Vistas relacionadas a la planificacion
    url(r'^plan/planificacion/(?P<pk>\d+)/$', views.PlanificacionView.as_view(), name='plan_planificacion_detail'),
    url(r'^plan/savestage3/$', views.GuardarPlanificacionView.as_view()),
    url(r'^plan/itemplanventatemp/$', views.BuscarVentaTemporadaItemplanView.as_view()),
    url(r'^plan/itemplanventatempcomp/$', views.BuscarVentaTemporadaItemplanCompView.as_view()),
    url(r'^plan/planstats/$', views.BuscarStatsPlanView.as_view()),

    # Vistas relacionadas al resultado de la planificacion
    url(r'^plan/resumen/(?P<pk>\d+)/$', views.ResumenPlanView.as_view(), name='resumen_plan_detail'),
    url(r'^plan/resumendata/$', views.ResumenDataGraficosView.as_view()),

    # Vistas relacionadas a la planificacion de saldos y avances
    url(r'^plan/saldos-avances/(?P<pk>\d+)/$', views.SaldosAvancesView.as_view(), name='plan_saldosavances_detail'),
    url(r'^plan/buscar-saldos-avances/$', views.BuscarVentaSaldosAvancesView.as_view()),
)
