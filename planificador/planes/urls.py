from django.conf.urls import patterns
from django.conf.urls import url
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
    url(r'^plan/buscar-estructura-arbol/$', views.BuscarEstructuraArbolView.as_view(),
        name='plan_buscar_estructura_arbol'),
    url(r'^plan/buscar-itemplan-eliminados/$', views.BuscarItemplanEliminados.as_view(),
        name='plan_buscar_itemplan_eliminados'),
    url(r'^plan/recuperar-itemplan-eliminados/$', views.RecuperarItemplanEliminados.as_view(),
        name='plan_recuperar_itemplan_eliminados'),
    url(r'^plan/eliminar-itemplan/$', views.EliminarItemplan.as_view(),
        name='plan_eliminar_itemplan'),
    url(r'^plan/crear_itemplan/$', views.CrearItemplan.as_view(),
        name='plan_crear_itemplan'),

    # Vistas para el workflow de trabajo (proyeccion, planificacion y resumen)
    url(r'^plan/trabajar-planificacion/(?P<pk>\d+)/$', views.TrabajarPlanificacionView.as_view(),
        name='plan_trabajo_detail'),
    url(r'^plan/trabajar-planificacion/(?P<pk>\d+)/(?P<slug>[0-9]+)/$', views.TrabajarPlanificacionView.as_view(),
        name='plan_trabajo_detail'),
    url(r'^plan/guardar-proyeccion/$', views.GuardarProyeccionView.as_view()),
    url(r'^plan/buscar-datos-proyeccion/$', views.BuscarDatosProyeccionView.as_view()),
    url(r'^plan/buscar-datos-proyeccion-comp/$', views.BuscarDatosProyeccionCompView.as_view()),
    url(r'^plan/buscar-lista-items/$', views.BuscarListaItemView.as_view()),
    url(r'^plan/buscar-lista-items-comparacion/$', views.BuscarListaItemCompView.as_view()),
    url(r'^plan/guardar-planificacion-tv/$', views.GuardarPlanificacionView.as_view()),
    url(r'^plan/buscar-datos-planificacion-tv/$', views.BuscarDatosPlanificacionView.as_view()),
    url(r'^plan/buscar-datos-planificacion-tv-comp/$', views.BuscarDatosPlanificacionCompView.as_view()),
    url(r'^plan/buscar-datos-resumen/$', views.ResumenDataGraficosView.as_view()),
    url(r'^plan/buscar-datos-resumen-planificacion/$', views.ResumenPlanDataGraficosView.as_view()),
    url(r'^plan/buscar-datos-planificacion-as/$', views.BuscarSaldosAvancesView.as_view()),
    url(r'^plan/buscar-datos-planificacion-as-comp/$', views.BuscarSaldosAvancesCompView.as_view()),
    url(r'^plan/guardar-planificacion-as/$', views.GuardarSaldosAvancesView.as_view()),
    url(r'^plan/actualizar-precio-costo/$', views.GuardarPrecioCostoView.as_view()),
    url(r'^plan/buscar-lista-items-independientes/$', views.BuscarItemIndependientesView.as_view()),

    # Vista para la generacion de un informe XLSX de planificacion
    url(r'^plan/plan_exportar_excel/(?P<pk>\d+)/$', 'planes.views.ExportarPlanificacionExcelView', name='plan_exportar_excel_detail'),
    # Vista para la generacion de un informe PDF de planificacion
    url(r'^plan/plan_exportar_plan_pdf/(?P<pk>\d+)/$', views.ResumenPlanificacionPDFView.as_view(), name='plan_exportar_plan_pdf_detail'),
    url(r'^plan/plan_exportar_pdf/(?P<pk>\d+)/$', views.ResumenPDFView.as_view(), name='plan_exportar_pdf_detail'),
    url(r'^plan/plan_exportar_pdf/(?P<pk>\d+)/(?P<slug1>[0-9]+)/(?P<slug2>[0-9x]+)/$', views.ResumenPDFView.as_view(), name='plan_exportar_pdf_detail'),
    url(r'^plan/portada-pdf/(?P<pk>\d+)/$', views.PortadaPDFView.as_view(), name='plan_portada_pdf'),
)
