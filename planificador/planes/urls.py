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
    url(r'^plan/guardar-arbol/$', views.GuardarArbolView.as_view()),
    url(r'^plan/buscar-estructura-arbol/$', views.BuscarEstructuraArbolView.as_view(), name='plan_buscar_estructura_arbol'),

    # Vista para trabajar una planificacion (proyectar, planificar y resumen)
    url(r'^plan/trabajar-planificacion/(?P<pk>\d+)/$', views.TrabajarPlanificacionView.as_view(), name='plan_trabajo_detail'),

    # Vistas relacionadas a las proyecciones
    url(r'^plan/proyeccion/(?P<pk>\d+)/$', views.ProyeccionesView.as_view(), name='plan_proyecciones_detail'),
    url(r'^plan/guardar-proyeccion/$', views.GuardarProyeccionView.as_view()),
    url(r'^plan/buscar-datos-proyeccion/$', views.BuscarVentaItemplanProyeccionView.as_view()),
    url(r'^plan/buscar-datos-proyeccion-comp/$', views.BuscarVentaItemplanCompProyeccionView.as_view()),
    url(r'^plan/buscar-lista-items/$', views.BuscarCategoriaListProyeccionView.as_view()),
    url(r'^plan/buscar-lista-items-comparacion/$', views.BuscarCategoriaListCompProyeccionView.as_view()),
    
    # Vistas relacionadas a la planificacion
    url(r'^plan/planificacion/(?P<pk>\d+)/$', views.PlanificacionView.as_view(), name='plan_planificacion_detail'),
    url(r'^plan/guardar-planificacion-tv/$', views.GuardarPlanificacionView.as_view()),
    url(r'^plan/buscar-datos-planificacion-tv/$', views.BuscarVentaTemporadaItemplanView.as_view()),
    url(r'^plan/buscar-datos-planificacion-tv-comp/$', views.BuscarVentaTemporadaItemplanCompView.as_view()),
    url(r'^plan/planstats/$', views.BuscarStatsPlanView.as_view()),

    # Vistas relacionadas al resultado de la planificacion
    url(r'^plan/resumen/(?P<pk>\d+)/$', views.ResumenPlanView.as_view(), name='resumen_plan_detail'),
    url(r'^plan/buscar-datos-resumen/$', views.ResumenDataGraficosView.as_view()),

    # Vistas relacionadas a la planificacion de saldos y avances
    url(r'^plan/saldos-avances/(?P<pk>\d+)/$', views.SaldosAvancesView.as_view(), name='plan_saldosavances_detail'),
    url(r'^plan/buscar-datos-planificacion-as/$', views.BuscarSaldosAvancesView.as_view()),
    url(r'^plan/buscar-datos-planificacion-as-comp/$', views.BuscarSaldosAvancesCompView.as_view()),
    url(r'^plan/guardar-planificacion-as/$', views.GuardarSaldosAvancesView.as_view()),

    url(r'^plan/plan_exportar_excel/(?P<pk>\d+)/$', 'planes.views.ExportarExcelView', name='plan_exportar_excel_detail'),
)
