# -*- coding: utf-8 -*-
from collections import defaultdict
from collections import OrderedDict
from decimal import Decimal
from django import db
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import Q, F, Sum, Avg, Min
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import View, TemplateView, ListView, DetailView
from braces.views import LoginRequiredMixin, GroupRequiredMixin
from xlsxwriter.workbook import Workbook
from wkhtmltopdf.views import PDFTemplateResponse
from .models import Plan, Itemplan, Temporada
from ventas.models import Ventaperiodo, Controlventa
from calendarios.models import Periodo
from categorias.models import Categoria
from categorias.models import Item
from categorias.models import Itemjerarquia
from forms import PlanForm, TemporadaForm
from planificador.views import UserInfoMixin
import cStringIO as StringIO
import json
import math
import pprint
import time


class TemporadaListView(LoginRequiredMixin, UserInfoMixin, ListView):
    context_object_name = "temporadas"
    template_name = "planes/temporada_list.html"

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Temporada.objects.filter(organizacion=self.request.user.get_profile().organizacion)


class TemporadaCreateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, CreateView):
    model = Temporada
    template_name = "planes/temporada_create.html"
    form_class = TemporadaForm
    group_required = u'Administrador'

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
        return super(TemporadaCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(TemporadaCreateView, self).get_context_data(**kwargs)
        return context


class TemporadaDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    model = Temporada
    template_name = "planes/temporada_detail.html"

    def get_context_data(self, **kwargs):
        context = super(TemporadaDetailView, self).get_context_data(**kwargs)
        return context


class TemporadaUpdateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, UpdateView):
    model = Temporada
    template_name = "planes/temporada_update.html"
    form_class = TemporadaForm
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(TemporadaUpdateView, self).get_context_data(**kwargs)
        return context


class TemporadaDeleteView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, DeleteView):
    model = Temporada
    template_name = "planes/temporada_delete.html"
    success_url = reverse_lazy('planes:temporada_list')
    group_required = u'Administrador'


class IndexView(LoginRequiredMixin, UserInfoMixin, TemplateView):
    template_name = "planes/index.html"


class PlanListView(LoginRequiredMixin, UserInfoMixin, ListView):
    context_object_name = "planes"
    template_name = "planes/plan_list.html"

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Plan.objects.filter(usuario_creador=self.request.user).order_by('-anio', 'temporada__nombre')


class PlanCreateView(LoginRequiredMixin, UserInfoMixin, CreateView):
    """
    Vista para la creacion de un Plan.
    """
    model = Plan
    template_name = "planes/plan_create.html"
    form_class = PlanForm

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        form.instance.nombre = str(form.instance.anio) + " - " + form.instance.temporada.nombre
        return super(PlanCreateView, self).form_valid(form)

    def get_initial(self):
        self.initial.update({'usuario': self.request.user})
        return self.initial


class PlanDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    Vista para visualizar la ficha de una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_detail.html"


class PlanDeleteView(LoginRequiredMixin, UserInfoMixin, DeleteView):
    '''
    Vista para eliminar una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_delete.html"
    success_url = reverse_lazy('planes:plan_list')


class PlanTreeDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    1era fase del proceso de planificacion.
    Vista principal para la seleccion del arbol de planificacion.
    '''
    model = Plan
    template_name = "planes/plan_arbol_detail.html"

    def get_context_data(self, **kwargs):
        context = super(PlanTreeDetailView, self).get_context_data(**kwargs)
        # Se incorporan datos estadisticos a la vista
        context['nodos_visibles'] = Itemplan.objects.filter(plan=context['plan'].id).count()
        context['nodos_planificables'] = Itemplan.objects.filter(plan=context['plan'].id, planificable=True).count()
        return context


class BuscarEstructuraArbolView(LoginRequiredMixin, View):
    """
    Recibe un ID de Plan y devuelve en formato JSON, la estructura
    del arbol de planificacion.
    """
    def get(self, request, *args, **kwargs):
        if request.GET:
            data = {}
            id_plan = request.GET['id_plan']
            # Manejar error en caso de que no se encuentre el plan
            try:
                plan_obj = Plan.objects.get(pk=id_plan)
            except ObjectDoesNotExist:
                return HttpResponse(json.dumps(data), mimetype='application/json')
            data = plan_obj.obtener_arbol(self.request.user)
            return HttpResponse(data, mimetype='application/json')


class GuardarArbolView(LoginRequiredMixin, View):
    '''
    Vista que recibe como parametros el plan y un arreglo de ID con todos los
    items que deben ser planificados.
    '''
    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['plan'])
            # Reset queries
            db.reset_queries()
            # Si el arbol existe, debe ser eliminado
            if bool(Itemplan.objects.filter(plan=data['plan'])):
                Itemplan.objects.filter(plan=data['plan']).delete()
            plan_obj = Plan.objects.get(pk=data['plan'])
            #items_obj_arr = [Item.objects.get(pk=val) for val in data['items']]
            items_obj_arr = Item.objects.filter(pk__in=data['items']).prefetch_related('item_padre', 'venta_item')
            itemplan_obj_arr = [Itemplan(nombre=x.nombre, plan=plan_obj, item=x, item_padre=None, precio=x.precio, costo=x.calcular_costo_unitario(plan_obj.anio-1)) for x in items_obj_arr]
            # Se marcan los itemplan que pueden ser planificados
            for itemplan_obj in itemplan_obj_arr:
                if itemplan_obj.item.id in data['items_planificables']:
                    itemplan_obj.planificable = True
            plan_obj.estado = 1
            plan_obj.save()

            # Se guardar los itemplan que componen el arbol de planificacion
            Itemplan.objects.bulk_create(itemplan_obj_arr)
            print "QUERIES PRIMERA FASE: " + str(len(db.connection.queries))

            # Reset queries
            db.reset_queries()

            # A continuacion se deben actualizar el campo item_padre, el cual tiene el ID del itemplan padre de
            # cada uno de los itemplan del arbol. Es un proceso posterior, ya que se requiere que cada itemplan
            # tenga ID, es decir, haya sido almacenado anteriormente en la base de datos

            # Se genera nuevamente la lista con los itemplan creados a nivel de BD, es decir, ahora tienen ID
            #Itemplan.objects.filter(plan=plan_obj).update(item_padre=F('item__item_padre__item_proyectados'))
            itemplan_obj_arr = Itemplan.objects.filter(plan=plan_obj).prefetch_related('item__item_padre')
            for itemplan_obj in itemplan_obj_arr:
                #item_padre = itemplan_obj.item.item_padre
                #print itemplan_obj.item.item_padre.item_proyectados.filter(plan=plan_obj)
                try:
                    #itemplan_padre = Itemplan.objects.get(plan=plan_obj,item=item_padre)
                    itemplan_padre = itemplan_obj.item.item_padre.item_proyectados.get(plan=plan_obj)
                except ObjectDoesNotExist:
                    itemplan_padre = None
                itemplan_obj.item_padre = itemplan_padre
                # Se guarda la asignacion del itemplan padre
                itemplan_obj.save()
            print "QUERIES SEGUNDA FASE: " + str(len(db.connection.queries))
            # Reset queries
            db.reset_queries()
        return HttpResponseRedirect(reverse('planes:plan_detail', args=(plan_obj.id,)))


class TrabajarPlanificacionView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    2da fase del proceso de planificacion.
    Vista principal para la proyeccion de datos historicos de items.
    '''
    model = Plan
    template_name = "planes/plan_trabajo_detail.html"

    def get_context_data(self, **kwargs):
        context = super(TrabajarPlanificacionView, self).get_context_data(**kwargs)
        if 'slug' in self.kwargs:
            context['actividad'] = self.kwargs['slug']
        else:
            context['actividad'] = 1
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto, no se puede proyectar informacion
            context['msg'] = "Primero debe definir el árbol de planificación."
        else:
            # Lista de items sobre los cuales es el usuario es responsable
            items_responsable = Item.objects.filter(usuario_responsable=self.request.user)

            # Lista de items que pertenecen a la categoria mas alta a mostrar
            items_categoria_raiz = []

            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a proyectar
            # Las categorias no pueden ser planificables ni ser la ultima (organizacion)
            combo_categorias = Categoria.objects.filter(organizacion=self.request.user.get_profile().organizacion).exclude(Q(categoria_padre=None) | Q(planificable=True))

            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a comparar
            combo_categorias_comp = Categoria.objects.filter(organizacion=self.request.user.get_profile().organizacion).exclude(categoria_padre=None)

            # Se obtiene la categoria mas alta que cumple con estos requisitos (sera el primer combobox)
            categoria_raiz = sorted(items_responsable, key=lambda t: t.categoria.get_nivel())[0]

            # Se recalculan las listas de categorias a mostrar como comboboxes
            # Se deben mostrar a partir de la categoria sobre la cual el usuario es responsable
            combo_categorias_comp = [x for x in combo_categorias_comp if x.get_nivel() >= categoria_raiz.get_nivel()]
            combo_categorias = [x for x in combo_categorias if x.get_nivel() >= categoria_raiz.get_nivel()]

            # Luego se busca la lista de items que pertenecen a la categoria_raiz y que el usuario
            # debiese poder ver, es decir, es el item padre del item sobre el cual es responsable
            # Ejemplo: si el usuario es responsable del rubro Adulto Masculino, entonces debiese
            # poder ver como division a Hombre
            items_categoria_raiz = self.request.user.get_profile().items_visibles(categoria_raiz)

            context['combo_categorias'] = combo_categorias
            context['combo_categorias_comp'] = sorted(combo_categorias_comp, key=lambda t: t.get_nivel())
            context['num_combo_categorias_comp'] = len(combo_categorias_comp)
            context['items_categoria_raiz'] = items_categoria_raiz

            # Si la organizacion cuenta con una categoria con jerarquia independiente (ver modelo), entonces
            # se debe generar un buscador por esa categoria
            try:
                context['categoria_independiente'] = Categoria.objects.get(
                    organizacion=self.request.user.get_profile().organizacion,
                    jerarquia_independiente=True)
                context['categoria_raiz'] = categoria_raiz
            except ObjectDoesNotExist:
                context['categoria_independiente'] = None
        return context


class GuardarProyeccionView(UserInfoMixin, View):
    """
    Guarda la proyección asociada al item recibido como pararametro.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['datos_tarea'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'], plan=plan_obj)

            # Se revisa si la categoria del item que esta siendo proyectado tiene hijos (si pertenece
            # a una categoria hoja o no), en caso de tener hijos, se imputa la proyeccion al primero de ellos
            if itemplan_obj.item.categoria.get_children():
                item_proyectado = itemplan_obj.item.get_children()[0]
            else:
                item_proyectado = itemplan_obj.item

            # Se itera por cada temporada, periodo del objeto de proyeccion
            for temporada, periodos in data['ventas'].iteritems():
                temporada_obj = Temporada.objects.get(nombre=temporada)
                # Se itera por cada venta de cada periodo
                for periodo, venta in periodos.iteritems():
                    # Se seleccionan las ventas que no son reales (proyectadas o por proyectar)
                    if venta['tipo'] == 3:
                        defaults = {
                            'vta_n': venta['vta_n'],
                            'ctb_n': venta['ctb_n'],
                            'costo': venta['costo'],
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen'],
                            'precio_real': venta['precio_real'],
                            'costo_unitario': venta['costo_unitario'],
                            'dcto': venta['dcto']

                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            plan=plan_obj,
                            item=item_proyectado,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj,
                            tipo=1,  # Tipo = 1 -> Proyectada
                            defaults=defaults)
                        if created is False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = venta['dcto']
                            obj.margen = venta['margen']
                            obj.costo = venta['costo']
                            obj.costo_unitario = venta['costo_unitario']
                            obj.precio_real = venta['precio_real']
                            if venta['vta_u'] != 0:
                                # Tipo = 1 -> Proyectada
                                obj.tipo = 1
                            obj.save()
            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            itemplan_obj.estado = 1
            itemplan_obj.save()
        data = {'msg': "Proyección guardada."}
        return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarListaItemView(View):
    '''
    Recibe como parametro un ID de item y devuelve la lista de items hijos del item, y que el usuario
    puede ver, es decir, pertenecen a una rama sobre la cual tiene visibilidad
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            data = {}
            items = []
            id_item = json.loads(request.GET['id_item'])
            id_plan = request.GET['id_plan']
            # Se busca el objeto de plan
            plan_obj = Plan.objects.get(pk=id_plan)
            # Se busca el objeto de item asociado al parametro id_item
            item_seleccionado = Item.objects.get(pk=id_item)
            # Se busca el objecto de itemplan asociado al item escogido
            itemplan_seleccionado = Itemplan.objects.get(plan=plan_obj, item=item_seleccionado)
            # Se buscan todos los hijos del item pasado por parametro
            items_temp = item_seleccionado.get_children()

            if bool(items_temp):
                # Si la categoria del hijo no es planificable, entonces se debe generar otro combobox
                # Por el contrario, si es planificable, entonces se debe cargar el ultimo combobox con
                # todos los items a proyectar (agrupaciones y articulos)
                if items_temp[0].categoria.planificable is False:
                    for item_validar in items_temp:
                        # Solo se devuelven los items que pueden ser vistos por el usuario
                        #if self.request.user.get_profile().validar_visibles(item_validar):
                        if bool(Itemplan.objects.filter(item=item_validar, plan=plan_obj)):
                                items.append({'id': item_validar.id, 'nombre': item_validar.nombre, 'id_cat': item_validar.categoria.id})
                else:
                    # Se itera sobre la lista de hijos planificables del item seleccionado en el combobox
                    for itemplan in itemplan_seleccionado.get_hijos_planificables():
                        items.append({'id':itemplan.id, 'nombre': itemplan.nombre, 'estado': itemplan.get_estado_display(), 'precio': itemplan.item.precio, 'categoria_nombre': itemplan.item.categoria.nombre})
                data['items'] = items
                data['categoria'] = {'id_categoria': items_temp[0].categoria.id, 'planificable': items_temp[0].categoria.planificable}
            return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarListaItemCompView(View):
    '''
    Recibe como parametro un o varios IDs de item y devuelve la lista de items hijos del item, y que el usuario
    puede ver, es decir, pertenecen a una rama sobre la cual tiene visibilidad
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            data = {}
            items = []
            get_item = request.GET['id_item']
            id_item_busqueda = map(int, get_item.split(','))
            id_descendientes = Itemjerarquia.objects.filter(ancestro__in=id_item_busqueda, distancia=1).values_list('descendiente', flat=True)
            item_descendientes = Item.objects.filter(pk__in=id_descendientes).order_by('nombre')
            # Se valida que el item seleccionado tenga hijos
            if bool(item_descendientes):
                for item in item_descendientes:
                    items.append({
                        'id': item.id,
                        'nombre': item.nombre,
                        'precio': item.precio,
                        'id_cat': item.categoria.id
                        })
                data['items'] = items
                data['categoria'] = {'id_categoria': item_descendientes[0].categoria.id, 'planificable': item_descendientes[0].categoria.planificable}
            else:
                data['items'] = None
                data['categoria'] = None
            return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarDatosProyeccionView(View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial de este de los ultimos
    12 periodos. Esta informacion se utiliza para completar las tablas de proyeccion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            try:
                itemplan_obj = Itemplan.objects.get(plan=id_plan, id=id_itemplan)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': plan_obj.temporada.id,
                'nombre': plan_obj.temporada.nombre,
                'anio': plan_obj.anio
                }
            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            item = itemplan_obj.item
            lista_hijos = []
            lista_hijos.append(item)
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            controlventa = Controlventa.objects.filter(
                organizacion=self.request.user.get_profile().organizacion).latest('fecha_creacion')

            proyeccion = OrderedDict()

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
            # mas de una temporada.
            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by('-planificable', 'nombre').distinct()

            periodos = plan_obj.temporada.periodo.filter(
                tiempo__anio=plan_obj.anio-1,
                calendario__organizacion=self.request.user.get_profile().organizacion).order_by(
                'tiempo__anio', 'nombre').values('tiempo__anio', 'nombre').distinct()

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre'],
                        tipo__in=[0, 1]
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                            # Se valida si la venta debe ser proyectable o no
                            if venta['anio'] >= controlventa.anio and venta['periodo'] > controlventa.periodo.nombre:
                                # Venta por proyectar
                                venta['tipo'] = 1
                            else:
                                # Venta no proyectable
                                venta['tipo'] = 0

                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                        }
                        # Se valida si la venta debe ser proyectable o no
                        if venta_gap['anio'] >= controlventa.anio and venta_gap['periodo'] > controlventa.periodo.nombre:
                            # Venta por proyectar
                            venta_gap['tipo'] = 1
                        else:
                            # Venta no proyectable
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            itemplan_json = {}
            itemplan_json['id_item'] = itemplan_obj.item.id
            itemplan_json['id_itemplan'] = itemplan_obj.id
            itemplan_json['nombre'] = itemplan_obj.nombre
            itemplan_json['precio'] = itemplan_obj.item.precio
            itemplan_json['costo_unitario'] = itemplan_obj.item.calcular_costo_unitario(plan_obj.anio-1)

            resumen['itemplan'] = itemplan_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarDatosProyeccionCompView(View):
    '''
    Recibe un item y un plan, y busca toda la informacion comercial de este de los ultimos
    12 periodos. Esta informacion se utiliza para completar las tablas de comparacion en la vista
    de proyecccion.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            id_plan = request.GET['id_plan']
            id_item = request.GET['id_item']
            # Si viene un arreglo de IDs de Item, estos vendran separados por ,
            id_item_busqueda = map(int, id_item.split(','))
            item_obj_arr = Item.objects.filter(id__in=id_item_busqueda)
            if not item_obj_arr:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': plan_obj.temporada.id,
                'nombre': plan_obj.temporada.nombre,
                'anio': plan_obj.anio
            }

            # Se busca la lista de descendientes del objeto
            lista_hijos = Itemjerarquia.objects.filter(ancestro__in=item_obj_arr).values_list('descendiente', flat=True)

            # Se obtiene el ultimo año y periodo en que se cargaron ventas
            controlventa = Controlventa.objects.filter(organizacion=self.request.user.get_profile().organizacion).latest('fecha_creacion')

            proyeccion = OrderedDict()

            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by('-planificable', 'nombre').distinct()

            periodos = plan_obj.temporada.periodo.filter(
                tiempo__anio=plan_obj.anio-1,
                calendario__organizacion=self.request.user.get_profile().organizacion).order_by(
                'tiempo__anio', 'nombre').values('tiempo__anio', 'nombre').distinct()

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre'],
                        tipo__in=[0, 1]
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                            # Se valida si la venta debe ser proyectable o no
                            if venta['anio'] >= controlventa.anio and venta['periodo'] > controlventa.periodo.nombre:
                                # Venta por proyectar
                                venta['tipo'] = 1
                            else:
                                # Venta no proyectable
                                venta['tipo'] = 0

                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                        }
                        # Se valida si la venta debe ser proyectable o no
                        if venta_gap['anio'] >= controlventa.anio and venta_gap['periodo'] > controlventa.periodo.nombre:
                            # Venta por proyectar
                            venta_gap['tipo'] = 1
                        else:
                            # Venta no proyectable
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            item_json = {}
            item_json['id_item'] = item_obj_arr[0].id
            item_json['id_itemplan'] = item_obj_arr[0].id
            item_json['nombre'] = item_obj_arr[0].nombre
            if len(item_obj_arr) > 1:
                item_json['precio'] = 0
                item_json['costo_unitario'] = 0
            else:
                item_json['precio'] = item_obj_arr[0].precio
                item_json['costo_unitario'] = item_obj_arr[0].calcular_costo_unitario(plan_obj.anio-1)
            resumen['itemplan'] = item_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarDatosPlanificacionView(View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial de este de los ultimos 3 años
    de la temporada asociada al plan. Esta informacion se utiliza para completar las tablas de planificacion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            resumen = {}

            try:
                itemplan_obj = Itemplan.objects.get(plan=id_plan, id=id_itemplan)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': itemplan_obj.plan.temporada.id,
                'nombre': itemplan_obj.plan.temporada.nombre,
                'anio': itemplan_obj.plan.anio
            }

            # Año actual
            act_anio = plan_obj.anio
            # Año actual - 3 (limite inferior)
            ant_anio = plan_obj.anio - 3

            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            item = itemplan_obj.item
            lista_hijos = []
            lista_hijos.append(item)
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            proyeccion = OrderedDict()

            # Se buscan todas las temporadas
            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by('-planificable', 'nombre').distinct()

            # Se buscan los periodos considerados en la vista de planificacion
            periodos = plan_obj.temporada.periodo.filter(
                tiempo__anio__lte=act_anio,
                tiempo__anio__gte=ant_anio
                ).order_by('tiempo__anio', 'nombre').values(
                'tiempo__anio', 'nombre').distinct()

            # Se marcan los periodos que pertenecen efectivamente a la temporada por planificar
            # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la
            # temporada que esta siendo planificada.
            for periodo in periodos:
                if periodo['tiempo__anio'] == act_anio:
                    periodo['temporada'] = True
                else:
                    periodo['temporada'] = False

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre']
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                            # Se corrige el costo unitario para el caso de agrupaciones de items
                            if periodo['temporada']:
                                venta['costo_unitario'] = itemplan_obj.costo
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                        }
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = venta_gap

            itemplan_json = {}
            itemplan_json['id_item'] = itemplan_obj.item.id
            itemplan_json['id_itemplan'] = itemplan_obj.id
            itemplan_json['nombre'] = itemplan_obj.nombre
            itemplan_json['precio'] = itemplan_obj.precio
            itemplan_json['costo_unitario'] = itemplan_obj.costo

            resumen['itemplan'] = itemplan_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarDatosPlanificacionCompView(View):
    '''
    Recibe un item y un plan, y busca toda la informacion comercial de este de los ultimos 3 años
    de la temporada asociada al plan. Esta informacion se utiliza para completar las tablas de planificacion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            id_plan = request.GET['id_plan']
            id_item = request.GET['id_item']
            # Si viene un arreglo de IDs de Item, estos vendran separados por ,
            id_item_busqueda = map(int, id_item.split(','))
            item_obj_arr = Item.objects.filter(id__in=id_item_busqueda)
            if not item_obj_arr:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': plan_obj.temporada.id,
                'nombre': plan_obj.temporada.nombre,
                'anio': plan_obj.anio
            }

            # Año actual (por planificar)
            act_anio = plan_obj.anio
            # Año actual - 3 (limite inferior)
            ant_anio = plan_obj.anio - 3

            # Se busca la lista de descendientes del objeto
            lista_hijos = Itemjerarquia.objects.filter(ancestro__in=item_obj_arr).values_list('descendiente', flat=True)

            proyeccion = OrderedDict()

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
            # mas de una temporada.
            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by('-planificable', 'nombre').distinct()

            periodos = plan_obj.temporada.periodo.filter(
                tiempo__anio__lte=act_anio,
                tiempo__anio__gte=ant_anio
                ).order_by('tiempo__anio', 'nombre').values(
                'tiempo__anio', 'nombre').distinct()

            # Se marcan los periodos que pertenecen efectivamente a la temporada por planificar
            # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la
            # temporada que esta siendo planificada.
            for periodo in periodos:
                if periodo['tiempo__anio'] == act_anio:
                    periodo['temporada'] = True
                else:
                    periodo['temporada'] = False

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre']
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                        }
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = venta_gap
            item_json = {}
            item_json['id_item'] = item_obj_arr[0].id
            item_json['id_itemplan'] = item_obj_arr[0].id
            item_json['nombre'] = item_obj_arr[0].nombre
            item_json['costo_unitario'] = 0
            if len(item_obj_arr) > 1:
                item_json['precio'] = 0
            else:
                item_json['precio'] = item_obj_arr[0].precio
            resumen['itemplan'] = item_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class GuardarPrecioCostoView(View):
    '''
    Actualiza el campo costo o campo precio de un objeto itemplan. Esta vista
    es llamada a traves de la vista de trabajo de planificacion.
    '''
    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['datos_ajuste_pbcu'])

            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            valor_ajuste = int(data['valor_ajuste'])
            tipo_ajuste = data['tipo_ajuste']

            # Se busca si el item tiene hijos
            arreglo_items = []
            for item in itemplan_obj.item.hijos_recursivos():
                arreglo_items.append(item)

            if tipo_ajuste == "precio":
                itemplan_obj.precio = valor_ajuste
                # A continuacion se actualiza la informacion de ventas asociada al itemplan
                # Venta Neta
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    vta_n=(1 - F('dcto')) * F('vta_u') * valor_ajuste / 1.19)
                # Contribucion
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    ctb_n=F('vta_n') - F('costo'))
                # Margen
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    margen=F('ctb_n') / F('vta_n'))
                # Precio Real
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    precio_real=F('vta_n') / F('vta_u') * 1.19)
            else:
                itemplan_obj.costo = valor_ajuste
                # A continuacion se actualiza la informacion de ventas asociada al itemplan
                # Costo Unitario
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    costo_unitario=valor_ajuste)
                # Costo
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    costo=F('vta_u') * valor_ajuste)
                # Contribucion
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    ctb_n=F('vta_n') - F('costo'))
                # Margen
                Ventaperiodo.objects.filter(plan=plan_obj, tipo=2, item__in=arreglo_items).update(
                    margen=F('ctb_n') / F('vta_n'))
            itemplan_obj.save()
            mensaje_respuesta = "El " + tipo_ajuste + " ha sido modificado al valor "
            mensaje_respuesta += "{:,}".format(valor_ajuste) + "."
            datos = {'msg': mensaje_respuesta}
            respuesta = simplejson.dumps(datos, cls=DjangoJSONEncoder)
            return HttpResponse(respuesta, mimetype='application/json')


class GuardarPlanificacionView(View):
    """
    Guarda la planificacion asociada al item recibido como pararametro.
    """
    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['datos_tarea'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])

            # Se revisa si la categoria del item que esta siendo planificado tiene hijos
            # (si pertenece a una categoria hoja o no), en caso de tener hijos, se imputa
            # la planificacion al primero de ellos.
            if itemplan_obj.item.categoria.get_children():
                item_proyectado = itemplan_obj.item.get_children()[0]
            else:
                item_proyectado = itemplan_obj.item

            # Se itera por cada temporada, periodo del objeto de proyeccion
            for temporada, periodos in data['ventas'].iteritems():
                temporada_obj = Temporada.objects.get(nombre=temporada)
                # Se itera por cada venta de cada periodo
                for periodo, venta in periodos.iteritems():
                    # Se seleccionan las ventas que no son reales (proyectadas o por proyectar)
                    if venta['tipo'] == 3:
                        defaults = {
                            'vta_n': venta['vta_n'],
                            'ctb_n': venta['ctb_n'],
                            'costo': venta['costo'],
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen'],
                            'precio_real': venta['precio_real'],
                            'costo_unitario': venta['costo_unitario'],
                            'dcto': venta['dcto']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            plan=plan_obj,
                            item=item_proyectado,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj,
                            tipo=2,  # Tipo = 2 -> Planificada
                            defaults=defaults)
                        if created is False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = venta['dcto']
                            obj.margen = venta['margen']
                            obj.costo = venta['costo']
                            obj.costo_unitario = venta['costo_unitario']
                            obj.precio_real = venta['precio_real']
                            if venta['vta_u'] != 0:
                                # Tipo = 2 -> Planificada
                                obj.tipo = 2
                            obj.save()

            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            # Estado = 2 -> Planificado
            itemplan_obj.estado = 2
            itemplan_obj.save()
        data = {'msg': "Planificación guardada."}
        return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarSaldosAvancesView(LoginRequiredMixin, View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial
    de los 3 meses anteriores y posteriores a la temporada que se esta
    planificando.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            try:
                itemplan_obj = Itemplan.objects.get(
                    plan=id_plan, id=id_itemplan)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': plan_obj.temporada.id,
                'nombre': plan_obj.temporada.nombre,
                'anio': plan_obj.anio
                }
            # Se busca la lista de items del item a proyectar. Si el item
            # es un nivel agrupado se devuelven todos sus hijos hojas o
            # con venta, si el item es una hoja, se devuelve a si mismo.
            item = itemplan_obj.item
            lista_hijos = []
            lista_hijos.append(item)
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            proyeccion = OrderedDict()

            # Se busca el periodo inferior y superior de la temporada a proyectar
            limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[0]
            limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[1]

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
            # mas de una temporada.
            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by('-planificable', 'nombre').distinct()

            # Lista de los X periodos a considerar en la planificacion de saldos y avances
            periodos = Periodo.objects.filter(
                Q(tiempo__anio=limite_sup['anio'], nombre__lte=limite_sup['periodo__nombre']) |
                Q(tiempo__anio=limite_inf['anio'], nombre__gte=limite_inf['periodo__nombre'])
                ).order_by('tiempo__anio', 'nombre').values('tiempo__anio', 'nombre').distinct()

            # Se marcan los periodos que pertenecen efectivamente a la temporada en curso
            # Esto se utiliza en la vista para "pintar" de un color diferente los periodos
            # de la temporada que esta siendo planificada.
            for periodo in periodos:
                if plan_obj.temporada.comprobar_periodo(periodo['nombre']):
                    periodo['temporada'] = True
                else:
                    periodo['temporada'] = False

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre']
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        # Se agregan algunos calculos a las ventas
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                            # Se corrige el costo unitario para el caso de agrupaciones de items
                            if periodo['temporada']:
                                venta['costo_unitario'] = itemplan_obj.costo
                            if plan_obj.temporada.comprobar_periodo(venta['periodo']):
                                venta['tipo'] = 0
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                        }
                        if plan_obj.temporada.comprobar_periodo(venta_gap['periodo']):
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            itemplan_json = {}
            itemplan_json['id_item'] = itemplan_obj.item.id
            itemplan_json['id_itemplan'] = itemplan_obj.id
            itemplan_json['nombre'] = itemplan_obj.nombre
            itemplan_json['precio'] = itemplan_obj.precio
            itemplan_json['costo_unitario'] = itemplan_obj.costo

            resumen['itemplan'] = itemplan_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarSaldosAvancesCompView(LoginRequiredMixin, View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial
    de los 3 meses anteriores y posteriores a la temporada que se esta
    planificando.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}

            id_plan = request.GET['id_plan']
            id_item = request.GET['id_item']
            # Si viene un arreglo de IDs de Item, estos vendran separados por ,
            id_item_busqueda = map(int, id_item.split(','))
            item_obj_arr = Item.objects.filter(id__in=id_item_busqueda)
            if not item_obj_arr:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id': plan_obj.temporada.id,
                'nombre': plan_obj.temporada.nombre,
                'anio': plan_obj.anio
                }

            # Se busca la lista de descendientes del objeto
            lista_hijos = Itemjerarquia.objects.filter(ancestro__in=item_obj_arr).values_list('descendiente', flat=True)

            proyeccion = OrderedDict()

            # Se busca el periodo inferior y superior de la
            # temporada a proyectar
            limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[0]
            limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[1]

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una
            # agrupacion, puede que considere mas de una temporada.
            temporadas = Temporada.objects.all().values(
                'nombre', 'id').order_by(
                '-planificable', 'nombre').distinct()

            # Lista de los X periodos a considerar en la
            # planificacion de saldos y avances
            periodos = Periodo.objects.filter(
                Q(tiempo__anio=limite_sup['anio'], nombre__lte=limite_sup['periodo__nombre']) |
                Q(tiempo__anio=limite_inf['anio'], nombre__gte=limite_inf['periodo__nombre'])
                ).order_by('tiempo__anio', 'nombre').values('tiempo__anio', 'nombre').distinct()

            # Se marcan los periodos que pertenecen efectivamente
            # a la temporada en curso. Esto se utiliza en la vista
            # para "pintar" de un color diferente los periodos de
            # la temporada que esta siendo planificada
            for periodo in periodos:
                if plan_obj.temporada.comprobar_periodo(periodo['nombre']):
                    periodo['temporada'] = True
                else:
                    periodo['temporada'] = False

            # Se llena el diccionario proyeccion, temporada->periodo->venta
            for temporada in temporadas:
                proyeccion[temporada['nombre']] = OrderedDict()
                for periodo in periodos:
                    ventas = Ventaperiodo.objects.filter(
                        item__in=lista_hijos,
                        anio=periodo['tiempo__anio'],
                        periodo=periodo['nombre'],
                        temporada__nombre=temporada['nombre']
                        ).values('anio', 'periodo', 'temporada').annotate(
                        vta_n=Sum('vta_n'), vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'), costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo'),
                        dcto=Avg('dcto'), precio_real=Avg('precio_real'),
                        costo_unitario=Avg('costo_unitario')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada
                    # y periodo en curso
                    if ventas.exists():
                        for venta in ventas:
                            # Se corrige el margen en caso de agrupaciones
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(venta['ctb_n'] / venta['vta_n'], 3)
                            else:
                                venta['margen'] = 0
                            if plan_obj.temporada.comprobar_periodo(venta['periodo']):
                                venta['tipo'] = 0
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta,
                        # se llena el gap con una venta vacia
                        venta_gap = {
                            'anio': periodo['tiempo__anio'],
                            'tipo': 1,
                            'vta_n': Decimal('0.000'),
                            'ctb_n': Decimal('0.000'),
                            'costo': Decimal('0.000'),
                            'vta_u': Decimal('0.000'),
                            'temporada': temporada['id'],
                            'periodo': periodo['nombre'],
                            'margen': Decimal('0.000'),
                            'precio_real': Decimal('0.000'),
                            'dcto': Decimal('0.000'),
                            'costo_unitario': Decimal('0.000')
                            }
                        if plan_obj.temporada.comprobar_periodo(venta_gap['periodo']):
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            item_json = {}
            item_json['id_item'] = item_obj_arr[0].id
            item_json['id_itemplan'] = item_obj_arr[0].id
            item_json['nombre'] = item_obj_arr[0].nombre
            item_json['costo_unitario'] = 0
            if len(item_obj_arr) > 1:
                item_json['precio'] = 0
            else:
                item_json['precio'] = item_obj_arr[0].precio
            resumen['itemplan'] = item_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class GuardarSaldosAvancesView(LoginRequiredMixin, View):
    """
    Guarda la planificacion de avances y saldos asociada al item recibido como pararametro.
    """

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['datos_tarea'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])

            # Se revisa si la categoria del item que esta siendo planificado tiene hijos (si pertenece
            # a una categoria hoja o no), en caso de tener hijos, se imputa la planificacion al primero de ellos
            if itemplan_obj.item.categoria.get_children():
                item_planificado = itemplan_obj.item.get_children()[0]
            else:
                item_planificado = itemplan_obj.item

            # Se itera por cada temporada, periodo del objeto de la planificación
            for temporada, periodos in data['ventas'].iteritems():
                temporada_obj = Temporada.objects.get(nombre=temporada)
                # Se itera por cada venta de cada periodo
                for periodo, venta in periodos.iteritems():
                    # Se seleccionan las ventas que no son reales (planificadas o por planificar)
                    if venta['tipo'] == 3:
                        defaults = {
                            'vta_n': venta['vta_n'],
                            'ctb_n': venta['ctb_n'],
                            'costo': venta['costo'],
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen'],
                            'precio_real': venta['precio_real'],
                            'costo_unitario': venta['costo_unitario'],
                            'dcto': venta['dcto']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            plan=plan_obj,
                            item=item_planificado,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj,
                            tipo=2,  # Tipo = 2 -> Planificada
                            defaults=defaults)
                        if created is False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = float(venta['dcto'])
                            obj.margen = float(venta['margen'])
                            obj.costo = float(venta['costo'])
                            obj.costo_unitario = venta['costo_unitario']
                            obj.precio_real = venta['precio_real']
                            if venta['vta_n'] != 0:
                                # Tipo = 2 -> Planificado
                                obj.tipo = 2
                            obj.save()

            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            # Estado = 2 -> Planificado
            itemplan_obj.estado = 2
            itemplan_obj.save()
        data = {'msg': "Planificación guardada."}
        return HttpResponse(json.dumps(data), mimetype='application/json')


class ResumenPlanDataGraficosView(View):
    '''
    Devuelve un objeto JSON con toda la informacion necesaria para la construccion del resumen PDF de la planificacion. Esto
    incluye a todos los itemplan existentes para el plan.
    '''

    def get(self, request, *args, **kwargs):
        if request.GET:
            pp = pprint.PrettyPrinter(indent=4)
            response = defaultdict()
            data_json = {}
            data_jsonp = {}

            #color_texto_ingraph = "#777"
            color_texto_ingraph = "black"
            color_fondo_ingraph = "#f5f5ed"

            id_plan = request.GET['id_plan']
            plan_obj = Plan.objects.get(pk=id_plan)

            # Variables con los años de inicio y termino del resumen
            act_anio = plan_obj.anio
            ant_anio = plan_obj.anio - 3

            venta_planificacion = plan_obj.resumen_venta_planificacion()

            #pp.pprint(venta_planificacion)

            resumen_item = defaultdict()
            # Por cada itemplan de la planificacion almacena un arreglo con los itemplan padres
            padres_dict = defaultdict()
            itemplan_planificados = plan_obj.item_planificados.all()
            for itemplan in itemplan_planificados:
                lista_nombres_padres = [itemplan.nombre] + itemplan.get_padre_nombre()
                padres_dict[itemplan.item_id] = lista_nombres_padres[::-1]
                # Lista con los ID de todos los descendientes del Itemplan
                descendientes = Itemjerarquia.objects.filter(ancestro=itemplan.item).values_list('descendiente', flat=True)
                arr_venta_anual_item = []
                for anio_plan in range(ant_anio, act_anio + 1):
                    venta_anual_item = defaultdict(int)
                    venta_anual_item['anio'] = anio_plan
                    venta_anual_item['item_id'] = itemplan.item.id
                    # Se busca la venta de los Item descendientes
                    ventas_item = [venta_planificacion[x] for x in descendientes]
                    # Se eliminan de la lista los Item sin venta
                    ventas_item = [x for x in ventas_item if x]
                    # Se itera por cada item (cada item contiene un arreglo de ventas anuales)
                    for item in ventas_item:
                        # Se itera por cada año de venta de cada item
                        for anio in item:
                            if anio['anio'] == anio_plan:
                                venta_anual_item['vta_n'] += anio['vta_n']
                                venta_anual_item['vta_u'] += anio['vta_u']
                                venta_anual_item['ctb_n'] += anio['ctb_n']
                                venta_anual_item['costo'] += anio['costo']
                                venta_anual_item['precio_vta_u'] += anio['precio_vta_u']
                    if venta_anual_item['vta_u'] != 0:  # Se calcula el precio blanco promedio
                        venta_anual_item['precio_blanco'] = venta_anual_item['precio_vta_u'] / venta_anual_item['vta_u']
                    else:
                        venta_anual_item['precio_blanco'] = 0
                    arr_venta_anual_item.append(venta_anual_item)
                resumen_item[itemplan.item.id] = arr_venta_anual_item
            #
            # A continuacion se encuentra la logica que genera los datos de venta para el resumen por Categoria con jerarquia independiente
            #
            dict_item_ind = defaultdict(list)
            # Arreglo que contiene los nombres de los Item de Categoria con jerarquia independiente. Utilizado
            # para la construccion del indice respectivo.
            cat_independiente = Categoria.objects.get(
                organizacion=plan_obj.usuario_creador.get_profile().organizacion,
                jerarquia_independiente=True)
            nivel_cat_independiente = cat_independiente.get_nivel()
            itemplan_raiz = itemplan_planificados.filter(item_padre=None)
            for itemplan in itemplan_raiz:
                # Distancia para ser utilizada en la busqueda de los objetos Itemjerarquia
                distancia = nivel_cat_independiente - itemplan.item.categoria.get_nivel()
                # Lista de ID de los Item que son de categoria con jerarquia independiente
                id_item_independientes = Itemjerarquia.objects.filter(
                    ancestro=itemplan.item,
                    distancia=distancia).values_list('descendiente', flat=True)
                # Lista de objetos Item que son de categoria con jerarquia independiente
                item_independientes = Item.objects.filter(pk__in=id_item_independientes)
                # Se itera por cada objeto Item para buscar los nodos con venta
                for item in item_independientes:
                    dict_item_ind[item.nombre] += Itemjerarquia.objects.filter(
                        ancestro=item).values_list('descendiente', flat=True)
                #pp.pprint(dict_item_ind)
                for item, descendientes in dict_item_ind.items():
                    arr_venta_anual_item_ind = []
                    for anio_plan in range(ant_anio, act_anio + 1):
                        venta_anual_item_ind = defaultdict(int)
                        venta_anual_item_ind['anio'] = anio_plan
                        venta_anual_item_ind['item'] = item
                        # Se busca la venta de los Item descendientes
                        ventas_item_independientes = [venta_planificacion[x] for x in descendientes]
                        # Se eliminan de la lista los Item sin venta
                        ventas_item_independientes = [x for x in ventas_item_independientes if x]
                        # Se itera por cada item (cada item contiene un arreglo de ventas anuales)
                        for item_ventas in ventas_item_independientes: 
                            # Se itera por cada año de venta de cada item
                            for anio in item_ventas:
                                if anio['anio'] == anio_plan:
                                    venta_anual_item_ind['vta_n'] += anio['vta_n']
                                    venta_anual_item_ind['vta_u'] += anio['vta_u']
                                    venta_anual_item_ind['ctb_n'] += anio['ctb_n']
                                    venta_anual_item_ind['costo'] += anio['costo']
                                    venta_anual_item_ind['precio_vta_u'] += anio['precio_vta_u']
                        if venta_anual_item_ind['vta_u'] != 0:  # Se calcula el precio blanco promedio
                            venta_anual_item_ind['precio_blanco'] = venta_anual_item_ind['precio_vta_u'] / venta_anual_item_ind['vta_u']
                        else:
                            venta_anual_item_ind['precio_blanco'] = 0
                        arr_venta_anual_item_ind.append(venta_anual_item_ind)
                        #pp.pprint(arr_venta_anual_item_ind)
                    resumen_item[item] = arr_venta_anual_item_ind
                #pp.pprint(resumen_item)
            for item, estadisticas in resumen_item.iteritems():
                resumen = {}
                # Label para todos los graficos (años)
                rows_label = []

                rows_venta = []
                rows_crecimiento_venta = []

                rows_unidades = []
                rows_crecimiento_unidades = []

                rows_contribucion = []
                rows_crecimiento_contribucion = []

                rows_margen = []
                rows_margen_ingraph = []

                rows_dcto_precio_imp = []
                rows_dcto_precio_imp_label = []
                rows_dcto_precio_imp_label_aux = []
                rows_costo = []

                JSONVenta = OrderedDict()
                JSONUnidades = OrderedDict()
                JSONContribucion = OrderedDict()
                JSONMargen = OrderedDict()
                JSONDctoPrecio = OrderedDict()
                JSONCosto = OrderedDict()

                JSON = {}

                temp_vta_n, temp_vta_u, temp_ctb_n = 0, 0, 0

                # Se itera sobre el resultado de la busqueda para generar un objeto con el formato requerido
                # por los graficos
                for x in estadisticas:

                    row_venta = []
                    row_crecimiento_venta = []

                    row_unidades = []
                    row_crecimiento_unidades = []

                    row_contribucion = []
                    row_crecimiento_contribucion = []

                    row_margen = []

                    row_precio_dcto_imp = []

                    vta_n, vta_u, ctb_n, precio_blanco = int(x['vta_n']), int(x['vta_u']), int(x['ctb_n']), int(x['precio_blanco'])
                    costo = int(x['costo'])

                    anio = str(x['anio'])
                    # Calculo de margen
                    if vta_n != 0:
                        margen = float(ctb_n) / vta_n
                    else:
                        margen = 0

                    # Calculos para el grafico de precio blanco
                    if x['vta_u'] != 0:
                        precio_real_cimp = int(vta_n / vta_u * 1.19)
                        precio_real_simp = int(vta_n / vta_u)
                        impuesto = precio_real_cimp - precio_real_simp
                        costo_unitario = int(costo / vta_u)
                    else:
                        costo_unitario, precio_real_simp, precio_real_cimp, impuesto = 0, 0, 0, 0
                    #descuento = precio_real_cimp - precio_real_simp  # precio blanco promedio - precio real
                    descuento = precio_blanco - precio_real_cimp

                    # Se genera el arreglo que contiene las etiquetas de cada categoria (años)
                    rows_label.append(anio)

                    if x > 0 and temp_vta_n != 0 and temp_vta_u != 0 and temp_ctb_n != 0:
                        crecimiento_vta_n = float((vta_n - temp_vta_n)) / temp_vta_n
                        crecimiento_vta_u = float((vta_u - temp_vta_u)) / temp_vta_u
                        crecimiento_ctb_n = float((ctb_n - temp_ctb_n)) / temp_ctb_n

                    else:
                        crecimiento_vta_n, crecimiento_vta_u, crecimiento_ctb_n = 0, 0, 0

                    # Se agrega el crecimiento por año a la lista
                    if crecimiento_vta_n != 0:
                        row_crecimiento_venta.append('{:.1%}'.format(crecimiento_vta_n))
                        row_crecimiento_venta.append(color_texto_ingraph)
                        row_crecimiento_venta.append(color_fondo_ingraph)
                        row_crecimiento_venta.append(-1)
                        row_crecimiento_venta.append(-10)
                        rows_crecimiento_venta.append(row_crecimiento_venta)
                    else:
                        rows_crecimiento_venta.append(None)
                    if crecimiento_vta_u != 0:
                        row_crecimiento_unidades.append('{:.1%}'.format(crecimiento_vta_u))
                        row_crecimiento_unidades.append(color_texto_ingraph)
                        row_crecimiento_unidades.append(color_fondo_ingraph)
                        row_crecimiento_unidades.append(-1)
                        row_crecimiento_unidades.append(-10)
                        rows_crecimiento_unidades.append(row_crecimiento_unidades)
                    else:
                        rows_crecimiento_unidades.append(None)
                    if crecimiento_ctb_n != 0:
                        row_crecimiento_contribucion.append('{:.1%}'.format(crecimiento_ctb_n))
                        row_crecimiento_contribucion.append(color_texto_ingraph)
                        row_crecimiento_contribucion.append(color_fondo_ingraph)
                        row_crecimiento_contribucion.append(-1)
                        row_crecimiento_contribucion.append(-10)
                        rows_crecimiento_contribucion.append(row_crecimiento_contribucion)
                    else:
                        rows_crecimiento_contribucion.append(None)

                    row_margen.append('{:.1%}'.format(margen))
                    row_margen.append(color_texto_ingraph)
                    row_margen.append(color_fondo_ingraph)
                    row_margen.append(1)
                    row_margen.append(5)
                    rows_margen_ingraph.append(row_margen)

                    # Se genera el arreglo que contiene los valores de cada categoria (años)
                    row_venta.append(vta_n)
                    row_unidades.append(vta_u)
                    row_contribucion.append(ctb_n)
                    row_precio_dcto_imp.append(descuento)
                    row_precio_dcto_imp.append(impuesto)
                    row_precio_dcto_imp.append(precio_real_simp)
                    rows_dcto_precio_imp_label.append(impuesto+descuento+precio_real_simp)
                    rows_dcto_precio_imp_label_aux.append([precio_real_cimp, precio_real_simp])

                    # Se agregan los valores al arreglo que contiene todos los valores por año
                    rows_venta.append(row_venta)
                    rows_unidades.append(row_unidades)
                    rows_contribucion.append(row_contribucion)
                    rows_margen.append(round(margen, 2))
                    rows_dcto_precio_imp.append(row_precio_dcto_imp)
                    rows_costo.append(costo_unitario)

                    temp_vta_n = vta_n
                    temp_vta_u = vta_u
                    temp_ctb_n = ctb_n

                JSONVenta['cols'] = rows_label
                JSONVenta['rows'] = rows_venta
                JSONVenta['ingraph'] = rows_crecimiento_venta

                JSONUnidades['cols'] = rows_label
                JSONUnidades['rows'] = rows_unidades
                JSONUnidades['ingraph'] = rows_crecimiento_unidades

                JSONContribucion['cols'] = rows_label
                JSONContribucion['rows'] = rows_contribucion
                JSONContribucion['ingraph'] = rows_crecimiento_contribucion

                JSONMargen['cols'] = rows_label
                JSONMargen['rows'] = rows_margen
                JSONMargen['ingraph'] = rows_margen_ingraph

                JSONDctoPrecio['cols'] = rows_label
                JSONDctoPrecio['rows'] = rows_dcto_precio_imp
                JSONDctoPrecio['labels'] = rows_dcto_precio_imp_label
                JSONDctoPrecio['labels_aux'] = rows_dcto_precio_imp_label_aux

                JSONCosto['rows'] = rows_costo

                JSON['venta'] = JSONVenta
                JSON['unidades'] = JSONUnidades
                JSON['contribucion'] = JSONContribucion
                JSON['margen'] = JSONMargen
                JSON['dcto_precio'] = JSONDctoPrecio
                JSON['costo'] = JSONCosto

                resumen['estadisticas'] = JSON
                response[item] = resumen
            response['items'] = padres_dict
            data_json = simplejson.dumps(response, cls=DjangoJSONEncoder)
            data_jsonp = "generarContenedores(" + str(data_json) + ");"
            return HttpResponse(data_jsonp, mimetype='application/json')


class ResumenDataGraficosView(View):
    '''
    Recibe un ID de plan, un ID de temporada y un ID de item. Devuelve la venta total
    de los ultimos 3 años asociadas al plan, temporada e item.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            data_json = {}
            data_jsonp = {}

            #color_texto_ingraph = "#777"
            color_texto_ingraph = "black"
            color_fondo_ingraph = "#f5f5ed"

            # Label para todos los graficos (años)
            rows_label = []

            rows_venta = []
            rows_crecimiento_venta = []

            rows_unidades = []
            rows_crecimiento_unidades = []

            rows_contribucion = []
            rows_crecimiento_contribucion = []

            rows_margen = []
            rows_margen_ingraph = []

            rows_dcto_precio_imp = []
            rows_dcto_precio_imp_label = []
            rows_dcto_precio_imp_label_aux = []
            rows_costo = []

            JSONVenta = OrderedDict()
            JSONUnidades = OrderedDict()
            JSONContribucion = OrderedDict()
            JSONMargen = OrderedDict()
            JSONDctoPrecio = OrderedDict()
            JSONCosto = OrderedDict()

            JSON = {}

            tipo_response = request.GET['tipo_response']
            id_plan = request.GET['id_plan']
            id_temporada = request.GET['id_temporada']
            id_item = request.GET['id_item']
            tipo_obj_item = request.GET['tipo_obj_item']
            if tipo_obj_item == 'item':  # Se revisa si el ID corresponde a un Item o a un Itemplan
                item_obj = Item.objects.get(pk=id_item)
            elif tipo_obj_item == 'itemplan':
                itemplan_obj = Itemplan.objects.get(pk=id_item)
                item_obj = itemplan_obj.item
            else:  # tipo_obj_item == 'arr_item'
                item_obj = Item.objects.filter(pk__in=map(int, id_item.split(',')))

            plan_obj = Plan.objects.get(pk=id_plan)

            # Se verifica la existencia de la temporada, ya que la opcion temporada = TOTAL no existe
            # a nivel de base de datos.
            try:
                temporada_obj = Temporada.objects.get(pk=id_temporada)
                estadisticas = plan_obj.resumen_estadisticas_item(temporada_obj, item_obj)
            # Si la temporada no existe, se asume que se trata de la temporada TOTAL, y por lo tanto,
            # se llama al metodo resumen_estadisticas con el parametro TT
            except ObjectDoesNotExist:
                estadisticas = plan_obj.resumen_estadisticas_item("TT", item_obj)
            temp_vta_n, temp_vta_u, temp_ctb_n = 0, 0, 0

            # Se itera sobre el resultado de la busqueda para generar un objeto con el formato requerido
            # por los graficos
            for x in estadisticas:

                row_venta = []
                row_crecimiento_venta = []

                row_unidades = []
                row_crecimiento_unidades = []

                row_contribucion = []
                row_crecimiento_contribucion = []

                row_margen = []

                row_precio_dcto_imp = []

                vta_n, vta_u, ctb_n, precio_blanco = int(x['vta_n']), int(x['vta_u']), int(x['ctb_n']), int(x['precio_blanco'])
                costo = int(x['costo'])

                anio = str(x['anio'])
                # Calculo de margen
                if vta_n != 0:
                    margen = float(ctb_n) / vta_n
                else:
                    margen = 0

                # Calculos para el grafico de precio blanco
                if x['vta_u'] != 0:
                    precio_real_cimp = int(vta_n / vta_u * 1.19)
                    precio_real_simp = int(vta_n / vta_u)
                    impuesto = precio_real_cimp - precio_real_simp
                    costo_unitario = int(costo / vta_u)
                else:
                    costo_unitario, precio_real_simp, precio_real_cimp, impuesto = 0, 0, 0, 0
                #descuento = precio_real_cimp - precio_real_simp  # precio blanco promedio - precio real
                descuento = precio_blanco - precio_real_cimp

                # Se genera el arreglo que contiene las etiquetas de cada categoria (años)
                rows_label.append(anio)

                if x > 0 and temp_vta_n != 0 and temp_vta_u != 0 and temp_ctb_n != 0:
                    crecimiento_vta_n = float((vta_n - temp_vta_n)) / temp_vta_n
                    crecimiento_vta_u = float((vta_u - temp_vta_u)) / temp_vta_u
                    crecimiento_ctb_n = float((ctb_n - temp_ctb_n)) / temp_ctb_n

                else:
                    crecimiento_vta_n, crecimiento_vta_u, crecimiento_ctb_n = 0, 0, 0

                # Se agrega el crecimiento por año a la lista
                if crecimiento_vta_n != 0:
                    row_crecimiento_venta.append('{:.1%}'.format(crecimiento_vta_n))
                    row_crecimiento_venta.append(color_texto_ingraph)
                    row_crecimiento_venta.append(color_fondo_ingraph)
                    row_crecimiento_venta.append(-1)
                    row_crecimiento_venta.append(-10)
                    rows_crecimiento_venta.append(row_crecimiento_venta)
                else:
                    rows_crecimiento_venta.append(None)
                if crecimiento_vta_u != 0:
                    row_crecimiento_unidades.append('{:.1%}'.format(crecimiento_vta_u))
                    row_crecimiento_unidades.append(color_texto_ingraph)
                    row_crecimiento_unidades.append(color_fondo_ingraph)
                    row_crecimiento_unidades.append(-1)
                    row_crecimiento_unidades.append(-10)
                    rows_crecimiento_unidades.append(row_crecimiento_unidades)
                else:
                    rows_crecimiento_unidades.append(None)
                if crecimiento_ctb_n != 0:
                    row_crecimiento_contribucion.append('{:.1%}'.format(crecimiento_ctb_n))
                    row_crecimiento_contribucion.append(color_texto_ingraph)
                    row_crecimiento_contribucion.append(color_fondo_ingraph)
                    row_crecimiento_contribucion.append(-1)
                    row_crecimiento_contribucion.append(-10)
                    rows_crecimiento_contribucion.append(row_crecimiento_contribucion)
                else:
                    rows_crecimiento_contribucion.append(None)

                row_margen.append('{:.1%}'.format(margen))
                row_margen.append(color_texto_ingraph)
                row_margen.append(color_fondo_ingraph)
                row_margen.append(1)
                row_margen.append(5)
                rows_margen_ingraph.append(row_margen)

                # Se genera el arreglo que contiene los valores de cada categoria (años)
                row_venta.append(vta_n)
                row_unidades.append(vta_u)
                row_contribucion.append(ctb_n)
                row_precio_dcto_imp.append(descuento)
                row_precio_dcto_imp.append(impuesto)
                row_precio_dcto_imp.append(precio_real_simp)
                rows_dcto_precio_imp_label.append(impuesto+descuento+precio_real_simp)
                rows_dcto_precio_imp_label_aux.append([precio_real_cimp, precio_real_simp])

                # Se agregan los valores al arreglo que contiene todos los valores por año
                rows_venta.append(row_venta)
                rows_unidades.append(row_unidades)
                rows_contribucion.append(row_contribucion)
                rows_margen.append(round(margen, 2))
                rows_dcto_precio_imp.append(row_precio_dcto_imp)
                rows_costo.append(costo_unitario)

                temp_vta_n = vta_n
                temp_vta_u = vta_u
                temp_ctb_n = ctb_n

            JSONVenta['cols'] = rows_label
            JSONVenta['rows'] = rows_venta
            JSONVenta['ingraph'] = rows_crecimiento_venta

            JSONUnidades['cols'] = rows_label
            JSONUnidades['rows'] = rows_unidades
            JSONUnidades['ingraph'] = rows_crecimiento_unidades

            JSONContribucion['cols'] = rows_label
            JSONContribucion['rows'] = rows_contribucion
            JSONContribucion['ingraph'] = rows_crecimiento_contribucion

            JSONMargen['cols'] = rows_label
            JSONMargen['rows'] = rows_margen
            JSONMargen['ingraph'] = rows_margen_ingraph

            JSONDctoPrecio['cols'] = rows_label
            JSONDctoPrecio['rows'] = rows_dcto_precio_imp
            JSONDctoPrecio['labels'] = rows_dcto_precio_imp_label
            JSONDctoPrecio['labels_aux'] = rows_dcto_precio_imp_label_aux

            JSONCosto['rows'] = rows_costo

            JSON['venta'] = JSONVenta
            JSON['unidades'] = JSONUnidades
            JSON['contribucion'] = JSONContribucion
            JSON['margen'] = JSONMargen
            JSON['dcto_precio'] = JSONDctoPrecio
            JSON['costo'] = JSONCosto

            resumen['estadisticas'] = JSON
            data_json = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            if tipo_response == 'json':
                return HttpResponse(data_json, mimetype='application/json')
            else:
                data_jsonp = "busquedaResumen(" + str(data_json) + ");"
                return HttpResponse(data_jsonp, mimetype='application/json')


def ExportarPlanificacionExcelView(request, pk=None):
    """
    Devuelve un objeto response tipo xls con un resumen de las compras asociadas a la planificacion.
    La estructura de salida es la siguiente:
        Padre 1, Padre 2, Padre 3, Item, PB, Año, Periodo, Venta $, Venta U, Costo, Contribucion
    """

    plan_obj = get_object_or_404(Plan, pk=pk)
    nombre_archivo = 'planificacion_' + plan_obj.temporada.nombre + '_' + str(plan_obj.anio) + '.xlsx'

    # Reset queries
    db.reset_queries()

    itemplan_planificados = plan_obj.item_planificados.filter(
        planificable=True).prefetch_related('item__categoria').order_by('item__categoria', 'item_padre__nombre', 'nombre', 'precio')

    for itemplan in itemplan_planificados:
        # Se verifica si el item planificado tiene hijos, ya que la venta siempre esta asociada a
        # nodos hijos y nunca a nodos intermedios, es decir, siempre a la ultima categoria.
        if bool(itemplan.item.categoria.get_children()):
            arreglo_dict_desc_id = Itemjerarquia.objects.filter(ancestro=itemplan.item).values('descendiente')
            arreglo_desc_id = [x['descendiente'] for x in arreglo_dict_desc_id]
            itemplan.info_comercial = Ventaperiodo.objects.filter(item__in=arreglo_desc_id).values(
                'anio', 'periodo').annotate(
                Sum('vta_n'), Sum('vta_u'), Sum('costo'), Sum('ctb_n')).order_by('anio', 'periodo')

        # Si es de la ultima categoria, es decir, no es posible que tenga hijos.
        else:
            itemplan.info_comercial = Ventaperiodo.objects.filter(item=itemplan.item).values(
                'anio', 'periodo').annotate(
                Sum('vta_n'), Sum('vta_u'), Sum('costo'), Sum('ctb_n')).order_by('anio', 'periodo')
        itemplan.padres = itemplan.get_padre()

    print "QUERIES: " + str(len(db.connection.queries))

    # create a workbook in memory
    output = StringIO.StringIO()

    book = Workbook(output)
    sheet = book.add_worksheet('Planificacion')

    # Formato moneda
    # fmoney = book.add_format({'num_format': '$#,##0'})
    # Formato numerico
    fnumeros = book.add_format({'num_format': '#,##0'})
    # Formato negrita
    fbold = book.add_format({'bold': True})

    # Ajustar el tamaño de la columna A (nombre de items)
    # sheet.set_column(0, 0, 40)

    categoria_raiz = None
    # Se busca la lista de objectos itemplan que no tienen padre (raices del arbol).
    arr_itemplan_raiz = Itemplan.objects.filter(plan=plan_obj, item_padre=None)
    itemplan_raiz = arr_itemplan_raiz[0]
    categoria_raiz = itemplan_raiz.item.categoria
    # Se busca el que tiene la categoria con menor nivel (mas cercana a la raiz).
    for x in arr_itemplan_raiz:
        if x.item.categoria.get_nivel() < itemplan_raiz.item.categoria.get_nivel():
            itemplan_raiz = x
            # Se asigna la categoria de menor nivel, para ser usada como la primera columna
            # del archivo excel.
            categoria_raiz = x.item.categoria
    cabecera_excel = []
    categorias = Categoria.objects.filter(organizacion=request.user.get_profile().organizacion)
    numero_total_categorias = len(categorias)
    categorias = [x for x in categorias if x.get_nivel() >= categoria_raiz.get_nivel()]
    categorias = sorted(categorias, key=lambda t: t.get_nivel())
    numero_final_categorias = len(categorias)
    numero_categorias_consideradas = numero_total_categorias - numero_final_categorias

    # Se generan los valores dinamicos de la cabecera. El ultimo nivel siempre
    # se llamara ITEM.
    for categoria in categorias:
        if bool(categoria.get_children()):
            cabecera_excel.append(categoria.nombre)
        else:
            cabecera_excel.append('ITEM')

    # Escribir la cabecera del archivo
    cabecera_excel += ['PRECIO', 'TEMPORADA', 'ANIO', 'PERIODO', 'VENTA CLP', 'UNIDADES', 'COSTO CLP', 'CONTRIBUCION CLP']
    for columna, titulo_columna in enumerate(cabecera_excel):
        sheet.write(0, columna, titulo_columna, fbold)

    # Se obtiene el numero de columnas dinamicas (categorias del modelo)
    numero_col_dinamicas = len(categorias)
    numero_filas = 0

    # Se itera sobre el diccionario de items y se crean las filas del archivo
    for item in itemplan_planificados:
        for venta in item.info_comercial:
            # Se agrega la lista de padres del itemplan.
            for padre in item.get_padre():
                sheet.write(numero_filas+1, padre.item.categoria.get_nivel()-(1+numero_categorias_consideradas), padre.nombre)
            # Si revisa si el itemplan pertenece a la categoria hoja.
            if bool(item.item.categoria.get_children()) is False:
                sheet.write(numero_filas+1, item.item.categoria.get_nivel()-(1+numero_categorias_consideradas), item.nombre)
            # Si no es categoria hoja entonces se debe repetir su nombre en las categorias inferiores.
            else:
                contador_niveles = item.item.categoria.get_nivel()
                for i in range(contador_niveles, numero_total_categorias+1):
                    sheet.write(numero_filas+1, i - numero_categorias_consideradas - 1, item.nombre)
            if plan_obj.anio == venta['anio']:
                sheet.write(numero_filas+1, numero_col_dinamicas, item.precio, fnumeros)
            else:
                sheet.write(numero_filas+1, numero_col_dinamicas, item.item.precio, fnumeros)
            if item.item.temporada is not None:
                sheet.write(numero_filas+1, numero_col_dinamicas+1, item.item.temporada.nombre)
            else:
                sheet.write(numero_filas+1, numero_col_dinamicas+1, "")
            sheet.write(numero_filas+1, numero_col_dinamicas+2, venta['anio'], fnumeros)
            sheet.write(numero_filas+1, numero_col_dinamicas+3, venta['periodo'])
            sheet.write(numero_filas+1, numero_col_dinamicas+4, venta['vta_n__sum'], fnumeros)
            sheet.write(numero_filas+1, numero_col_dinamicas+5, venta['vta_u__sum'], fnumeros)
            sheet.write(numero_filas+1, numero_col_dinamicas+6, venta['costo__sum'], fnumeros)
            sheet.write(numero_filas+1, numero_col_dinamicas+7, venta['ctb_n__sum'], fnumeros)
            numero_filas = numero_filas + 1

    # Se construye la fila de totales. La asignacion de las letras para los totales deberia ser
    # dinamica tambien. Seria bueno utilizar una tabla de mapeo entre numeros y letras.
    # sheet.write(numero_filas+1, 0, 'Total', fbold)
    # sheet.write(numero_filas+1, numero_col_dinamicas+3, '=SUM(H2:H'+str(numero_filas+1)+')', fnumeros)
    # sheet.write(numero_filas+1, numero_col_dinamicas+4, '=AVG(I2:I'+str(numero_filas+1)+')', fnumeros)
    # sheet.write(numero_filas+1, numero_col_dinamicas+5, '=SUM(J2:J'+str(numero_filas+1)+')', fnumeros)
    # sheet.write(numero_filas+1, numero_col_dinamicas+6, '=SUM(K2:K'+str(numero_filas+1)+')', fnumeros)
    book.close()

    # construct response
    output.seek(0)
    response = HttpResponse(output.read(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=" + nombre_archivo

    return response


class ResumenPDFView(LoginRequiredMixin, DetailView):
    """
    Vista para generar el resumen PDF de un item en particular.
    """
    template_name = 'planes/plan_resumen_pdf.html'
    model = Plan
    context = {}

    def get(self, request, *args, **kwargs):
        self.context['server_name'] = request.META['SERVER_NAME']
        self.context['server_port'] = request.META['SERVER_PORT']
        self.context['plan'] = self.get_object()
        # slug1 contiene el ID del item o itemplan
        # slug2 indica si el ID de slug1 es de un item (valor 1) o itemplan (valor 2)
        if 'slug1' in self.kwargs and 'slug2' in self.kwargs:
            tipo_obj = self.kwargs['slug1']
            self.context['id_item'] = self.kwargs['slug2']
        else:
            self.context['id_item'] = 999
            tipo_obj = 1000
        if tipo_obj == "1":  # es un objeto Itemplan
            self.context['id_item'] = Itemplan.objects.get(plan=self.context['plan'], pk=self.context['id_item'])
            self.context['id_items'] = ""
        elif tipo_obj == "2":  # es un objeto Item
            self.context['id_item'] = Itemplan.objects.get(plan=self.context['plan'], item__id=self.context['id_item'])
            self.context['id_items'] = ""
        else:  # es un arreglo de objetos Item (tipo_obj == 3)
            self.context['id_items'] = Itemplan.objects.filter(plan=self.context['plan'], item__in=map(int, self.context['id_item'].split('x'))).values_list('item_id', flat=True)
            self.context['id_item'] = Itemplan.objects.filter(plan=self.context['plan'], item__in=map(int, self.context['id_item'].split('x')))[0]
        self.context['tipo_obj'] = tipo_obj
        cmd_options = {
            'quiet': True,
            'encoding': 'utf8',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'margin-right': '10mm',
            'margin-top': '10mm',
            'orientation': 'landscape',
            'page-size': 'Letter',
            'dpi': '300'
        }
        #return self.render_to_response(self.context)
        response = PDFTemplateResponse(
            request=request,
            template=self.template_name,
            filename=str(self.context['plan'].anio) + "-" + str(self.context['plan'].temporada.nombre) + ".pdf",
            context=self.context,
            show_content_in_browser=False,
            cmd_options=cmd_options
        )
        return response


class ResumenPlanificacionPDFView(LoginRequiredMixin, DetailView):
    """
    Vista para generar el resumen completo de la planificacion en formato PDF.
    """
    template_name = 'planes/plan_resumen_plan_pdf.html'
    model = Plan
    context = {}

    def get(self, request, *args, **kwargs):
        self.context['server_name'] = request.META['SERVER_NAME']
        self.context['server_port'] = request.META['SERVER_PORT']
        plan_obj = self.get_object()
        self.context['plan'] = plan_obj
        self.context['usuario'] = request.user
        # Lista de itemplan de la planificacion
        itemplan_planificados = plan_obj.item_planificados.all().order_by('item__categoria', 'item_padre__nombre', 'nombre', 'precio')
        padres_dict = defaultdict()
        # Arreglo que contiene los nombres de los Item de Categoria con jerarquia independiente. Utilizado para la construccion
        # del indice respectivo.
        items_jerarquia_independiente = []
        cat_independiente = Categoria.objects.get(
            organizacion=plan_obj.usuario_creador.get_profile().organizacion,
            jerarquia_independiente=True)
        nivel_cat_independiente = cat_independiente.get_nivel()
        itemplan_raiz = itemplan_planificados.filter(item_padre=None)
        for itemplan in itemplan_raiz:
            # Distancia para ser utilizada en la busqueda de los objetos Itemjerarquia
            distancia = nivel_cat_independiente - itemplan.item.categoria.get_nivel()
            # Lista de ID de los Item hijos del Item pasado como parametro y que son de categoria con jerarquia independiente
            id_item_independientes = Itemjerarquia.objects.filter(
                ancestro=itemplan.item,
                distancia=distancia).values_list('descendiente', flat=True)
            # Se agregan los nombres de los Item de la categoria con jerarquia independientes pertenecientes a la planificacion
            items_jerarquia_independiente += Item.objects.filter(id__in=id_item_independientes).values_list('nombre', flat=True)
        # Se eliminan los elementos duplicados
        items_jerarquia_independiente = set(items_jerarquia_independiente)
        #cant_paginas_indice_ji = int(math.ceil(len(items_jerarquia_independiente) / 30.0))
        # Variables para configurar el tamaño de los graficos
        height_mar = str(90)
        height_con = str(155)
        height = str(int(height_mar) + int(height_con))
        width = str(470)
        categoria_pivote = ""
        html = ""

        for contador, itemplan in enumerate(itemplan_planificados):
            key = itemplan.item_id
            lista_nombres_padres = [itemplan.nombre] + itemplan.get_padre_nombre()
            padres_dict[itemplan.item_id] = lista_nombres_padres[::-1]
            # Si el item pertenece a una categoria planificable entonces se agrupa con el nombre ITEM
            if itemplan.item.categoria.planificable:
                categoria_item = "ITEM"
            else:  # En caso contrario se agrupa con el nombre original de categoria a la que pertenece
                categoria_item = itemplan.item.categoria.nombre
            # Se evalua si se tiene que escribir un titulo porque comienza una nueva categoria
            if categoria_pivote != categoria_item:
                html += "<div class=\"accordion\">"
                html += "<div class=\"pagina-categoria\">"
                html += "<div class=\"texto-pagina-categoria\"><h1 >RESUMEN " + categoria_item + "</h1></div>"
                html += "</div>"
                html += "</div>"
                categoria_pivote = categoria_item
            # Aqui se genera el codigo HTML para los divs del item sobre el cual se esta iterando
            html += "<div id=\"" + str(key) + "\" class=\"accordion\">"
            if itemplan.precio != 0:
                html += "<h4 id=\"" + str(key) + "-titulo-item\">" + str(1 + contador) + ") " + " | ".join(reversed(lista_nombres_padres)) + " ( " + "{:,}".format(itemplan.precio) + " )</h4>"
            else:
                html += "<h4 id=\"" + str(key) + "-titulo-item\">" + str(1 + contador) + ") " + " | ".join(reversed(lista_nombres_padres)) + "</h4>"
            html += "<div class=\"pure-g\" style=\"text-align:center\">"
            for i in range(0, 4):
                html += "<div class=\"pure-u-1-2\">"
                html += "<div class=\"titulo-chart\"><h5>" + getTitulo(i) + "</h5></div>"
                if i != 1:
                    html += "<div><canvas id=\"" + str(key) + "-" + str(i) + "-chart\" width=\"" + width + "\" height=\"" + height + "\">[No canvas support]</canvas></div>"
                else:
                    html += "<div><canvas id=\"" + str(key) + "-1a-chart\" width=\"" + width + "\" height=\"" + height_mar + "\">[No canvas support]</canvas></div>"
                    html += "<div><canvas id=\"" + str(key) + "-1b-chart\" width=\"" + width + "\" height=\"" + height_con + "\">[No canvas support]</canvas></div>"
                html += "</div>"
            html += "</div>"
            # Se agrega el pie de pagina con el numero de pagina
            html += "<div style=\"width:100%;text-align: center;\"><div class=\"page\"></div></div>"
            html += "</div>"
        # Aqui comienza la construccion del indice por categoria con jerarquia independiente
        html += "<div class=\"accordion\">"
        html += "<div class=\"pagina-categoria\">"
        html += "<div class=\"texto-pagina-categoria\"><h1>RESUMEN TOTAL POR " + cat_independiente.nombre + "</h1></div>"
        html += "</div>"
        html += "</div>"
        for contador_ji, nombre in enumerate(sorted(items_jerarquia_independiente, key=lambda t: t[0])):
            # Aqui se generan los divs de los item que pertenecen a la categoria con jerarquia independiente
            html += "<div id=\"" + nombre + "\" class=\"accordion\">"
            html += "<h4 id=\"" + nombre + "-titulo-item\">" + str(1 + contador_ji) + ") " + nombre + "</h4>"
            html += "<div class=\"pure-g\" style=\"text-align:center\">"
            for i in range(0, 4):
                html += "<div class=\"pure-u-1-2\">"
                html += "<div class=\"titulo-chart\"><h5>" + getTitulo(i) + "</h5></div>"
                if i != 1:
                    html += "<div><canvas id=\"" + nombre + "-" + str(i) + "-chart\" width=\"" + width + "\" height=\"" + height + "\">[No canvas support]</canvas></div>"
                else:
                    html += "<div><canvas id=\"" + nombre + "-1a-chart\" width=\"" + width + "\" height=\"" + height_mar + "\">[No canvas support]</canvas></div>"
                    html += "<div><canvas id=\"" + nombre + "-1b-chart\" width=\"" + width + "\" height=\"" + height_con + "\">[No canvas support]</canvas></div>"
                html += "</div>"
            html += "</div>"
            # Se agrega el pie de pagina con el numero de pagina
            html += "<div style=\"width:100%;text-align: center;\"><div class=\"page\"></div></div>"
            html += "</div>"

        self.context['html'] = html

        cmd_options = {
            'quiet': True,
            'encoding': 'utf8',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'margin-right': '10mm',
            'margin-top': '10mm',
            'orientation': 'landscape',
            'page-size': 'Letter',
            'footer-right':  'P. [page] / [topage]',
            'footer-line': True,
            'toc': True,
            'toc-depth': 2,
            'toc-header-text': 'Tabla de Contenidos',
            'cover': request.build_absolute_uri(reverse('planes:plan_portada_pdf', args=(plan_obj.id,)))
        }
        #return self.render_to_response(self.context)

        response = PDFTemplateResponse(
            request=request,
            template=self.template_name,
            filename=str(self.context['plan'].anio) + "-" + str(self.context['plan'].temporada.nombre) + ".pdf",
            context=self.context,
            show_content_in_browser=False,
            cmd_options=cmd_options
        )
        return response


class PortadaPDFView(DetailView):
    """
    Vista utilizada para generar la portada del resumen de una planificacion en formato PDF.
    """
    model = Plan
    template_name = "planes/plan_portada_pdf.html"


def getTitulo(x):
    """
    Funcion utilizada definir el titulo de los graficos del resumen de la planificacion en PDF
    """
    if x == 0:
        return "Ingresos por Ventas"
    elif x == 1:
        return "Contribuci&oacute;n y Margen"
    elif x == 2:
        return "Unidades de Venta"
    else:
        return "Precio blanco, precio real, ingreso y costo unitario"


class BuscarItemIndependientesView(View):
    '''
    Recibe como parametro el ID de un Item y devuelve una lista de Items pertenecientes a la Categoria con jerarquia
    independiente.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            dict_item = defaultdict(list)
            dict_ordenado = OrderedDict()
            # Se almacena el ID del Item recibido como parametro
            id_item = json.loads(request.GET['id_item'])
            # Se busca el objeto Item asociado al ID
            item_seleccionado = Item.objects.get(pk=id_item)
            # Se busca el nivel de la Categoria con jerarquia independiente para encontrar
            # la distancia entre la Categoria del Item y la Categoria mencionada
            nivel_cat_independiente = Categoria.objects.get(
                organizacion=self.request.user.get_profile().organizacion,
                jerarquia_independiente=True).get_nivel()
            # Distancia para ser utilizada en la busqueda de los objetos Itemjerarquia
            distancia = nivel_cat_independiente - item_seleccionado.categoria.get_nivel()
            # Lista de ID de los Item hijos del Item pasado como parametro y que son de categoria con jerarquia independiente
            id_item_independientes = Itemjerarquia.objects.filter(
                ancestro=item_seleccionado,
                distancia=distancia).values_list('descendiente', flat=True)
            # Se buscan los objetos Item asociados a la lista de ID
            items = Item.objects.filter(id__in=id_item_independientes)
            # Se construye un diccionario con el nombre de cada Item como llave, y todos los ID que llevan ese nombre.
            # Por ejemplo, todas las instancias de la marca PIETROVANNI se asocian a una llave.
            for item in items:
                dict_item[item.nombre].append(item.id)
            # Se devuelve un diccionario ordenado por el nombre del item
            dict_ordenado = OrderedDict(sorted(dict_item.items(), key=lambda t: t[0]))
            return HttpResponse(json.dumps(dict_ordenado), mimetype='application/json')
