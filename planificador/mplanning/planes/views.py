# -*- coding: utf-8 -*-
from collections import defaultdict, OrderedDict
from decimal import Decimal
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import Q, Sum, Avg, Max, Min
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import View, TemplateView, ListView, DetailView
from .models import Plan, Itemplan, Temporada
from ventas.models import Venta, Ventaperiodo, Controlventa
from calendarios.models import Periodo, Tiempo
from categorias.models import Categoria, Item
from forms import PlanForm, TemporadaForm
from planificador.views import UserInfoMixin
import json
import pprint


class TemporadaListView(UserInfoMixin, ListView):
    context_object_name = "temporadas"
    template_name = "planes/temporada_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TemporadaListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Temporada.objects.filter(organizacion=self.request.user.get_profile().organizacion)


class TemporadaCreateView(UserInfoMixin, CreateView):
    model = Temporada
    template_name = "planes/temporada_create.html"
    form_class = TemporadaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(TemporadaCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
        return super(TemporadaCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(TemporadaCreateView, self).get_context_data(**kwargs)
        return context


class TemporadaDetailView(UserInfoMixin, DetailView):
    model = Temporada
    template_name = "planes/temporada_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(TemporadaDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemporadaDetailView, self).get_context_data(**kwargs)
        return context


class TemporadaUpdateView(UserInfoMixin, UpdateView):
    model = Temporada
    template_name = "planes/temporada_update.html"
    form_class = TemporadaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(TemporadaUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TemporadaUpdateView, self).get_context_data(**kwargs)
        return context


class TemporadaDeleteView(UserInfoMixin, DeleteView):
    model = Temporada
    template_name = "planes/temporada_delete.html"
    success_url = reverse_lazy('planes:temporada_list')

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(TemporadaDeleteView, self).dispatch(*args, **kwargs)


class IndexView(UserInfoMixin, TemplateView):
    template_name = "planes/index.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IndexView, self).dispatch(*args, **kwargs)


class PlanListView(UserInfoMixin, ListView):
    context_object_name = "planes"
    template_name = "planes/plan_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Plan.objects.filter(usuario_creador=self.request.user)


class PlanCreateView(UserInfoMixin, CreateView):
    model = Plan
    template_name = "planes/plan_create.html"
    form_class = PlanForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        form.instance.nombre = str(form.instance.anio) + " - " + form.instance.temporada.nombre
        return super(PlanCreateView, self).form_valid(form)


class PlanDetailView(UserInfoMixin, DetailView):
    '''
    Vista para visualizar la ficha de una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PlanDetailView, self).get_context_data(**kwargs)
        context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1, planificable=True).count()
        context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0, planificable=True).count()
        return context

        
class PlanDeleteView(UserInfoMixin, DeleteView):
    '''
    Vista para eliminar una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_delete.html"
    success_url = reverse_lazy('planes:plan_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanDeleteView, self).dispatch(*args, **kwargs)


class PlanTreeDetailView(UserInfoMixin, DetailView):
    '''
    1era fase del proceso de planificacion.
    Vista principal para la seleccion del arbol de planificacion.
    '''
    model = Plan
    template_name = "planes/plan_tree_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanTreeDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PlanTreeDetailView, self).get_context_data(**kwargs)
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto, se presenta la estructura completa cerrada
            context['items'] = Item.objects.filter(usuario_responsable=self.request.user)
        else:
            """
            El arbol se debe generar abierto segun la planificacion
            El problema radica en como asignar el itemplan padre correctamente ya que los IDs de Item
            no son los mismos que los IDS de itemplan
            """
            context['items'] = Item.objects.filter(usuario_responsable=self.request.user)
            #context['items'] = Itemplan.objects.filter(plan=context['plan'].id, item_padre=None)
        return context


class GuardarArbolView(UserInfoMixin, View):
    '''
    Vista que revise como parametros el plan y un arreglo de ID con todos los
    items que deben ser planificados. 
    '''
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['plan'])
            # Si el arbol existe, debe ser eliminado
            if Itemplan.objects.filter(plan=data['plan']):
                Itemplan.objects.filter(plan=data['plan']).delete()
            plan_obj = Plan.objects.get(pk=data['plan'])
            items_obj_arr = [Item.objects.get(pk=val) for val in data['items']]
            itemplan_obj_arr = [Itemplan(nombre=x.nombre, plan=plan_obj, item=x, item_padre=None) for x in items_obj_arr]
            # Se marcan los itemplan que pueden ser planificados
            for itemplan_obj in itemplan_obj_arr:
                if itemplan_obj.item.id in data['items_planificables']:
                    itemplan_obj.planificable = True
            plan_obj.estado = 1
            plan_obj.save()
            Itemplan.objects.bulk_create(itemplan_obj_arr)

        return HttpResponseRedirect(reverse('planes:plan_detail', args=(plan_obj.id,)))


class ProyeccionesView(UserInfoMixin, DetailView):
    '''
    2da fase del proceso de planificacion.
    Vista principal para la proyeccion de datos historicos de items.
    '''
    model = Plan
    template_name = "planes/plan_proyecciones_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProyeccionesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProyeccionesView, self).get_context_data(**kwargs)
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto, no se puede proyectar informacion
            context['msg'] = "Primero debe definir el árbol de planificación."
        else:
            # Se deben presentar uno a uno los items a proyectar
            # context['items'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0).order_by('id')[1:3]
            context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1, planificable=True).count()
            context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0, planificable=True).count()
            context['num_items_tot'] = context['num_items_pro'] + context['num_items_nopro']
            
            # La variable categorias deberia desaparecer
            categorias = Categoria.objects.exclude(categoria_padre=None)
            # context['categorias'] = sorted(categorias, key= lambda t: t.get_nivel())
            
            # 
            items_categoria_raiz = []
            
            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a proyectar
            # Las categorias no pueden ser planificables ni ser la ultima (organizacion)
            combo_categorias = Categoria.objects.exclude(Q(categoria_padre=None) | Q(planificable=True))

            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a comparar
            combo_categorias_comp = Categoria.objects.exclude(categoria_padre=None)
            
            # Se obtiene la categoria mas alta que cumple con estos requisitos (sera el primer combobox)
            categoria_raiz = sorted(categorias, key= lambda t: t.get_nivel())[0]

            # Luego se busca la lista de items que pertenecen a la categoria_raiz y que el usuario
            # debiese poder ver, es decir, es el item padre del item sobre el cual es responsable
            # Ejemplo: si el usuario es responsable del rubro Adulto Masculino, entonces debiese
            # poder ver como division a Hombre

            items_categoria_raiz = self.request.user.get_profile().items_visibles(categoria_raiz)
            
            context['combo_categorias'] = combo_categorias
            context['combo_categorias_comp'] = sorted(combo_categorias_comp, key= lambda t: t.get_nivel())
            context['items_categoria_raiz'] = items_categoria_raiz

        return context


class GuardarProyeccionView(UserInfoMixin, View):
    """
    Guarda la proyección asociada al item recibido como pararametro.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['proyeccion'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            
            # Se itera por cada temporada, periodo del objeto de proyeccion
            for temporada, periodos in data['ventas'].iteritems():
                temporada_obj = Temporada.objects.get(nombre=temporada)
                # Se itera por cada venta de cada periodo
                for periodo, venta in periodos.iteritems():
                    # Se seleccionan las ventas que no son reales (proyectadas o por proyectar)
                    if venta['tipo'] == 3:
                        defaults = {
                            'tipo': 1, # Tipo = 1 -> Proyectada
                            'vta_n': venta['vta_n'],
                            'ctb_n': venta['ctb_n'],
                            'costo': venta['costo'],
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            item=itemplan_obj.item,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj, 
                            defaults=defaults)
                        if created == False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = float(venta['dcto']) 
                            obj.margen = float(venta['margen'])
                            obj.costo = float(venta['costo'])
                            if venta['vta_n'] != 0:
                                # Tipo = 2 -> Proyectada
                                obj.tipo = 1
                            obj.save()

            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            itemplan_obj.estado = 1
            itemplan_obj.save()
        data = {'msg':"Proyección guardada."}
        return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarCategoriaListProyeccionView(View):
    '''
    Revise como parametro un ID de item y devuelve la lista de items hijos del item, y que el usuario
    puede ver, es decir, pertenecen a una rama sobre la cual tiene visibilidad
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            data = {}
            items = []
            id_item = json.loads(request.GET['id_item'])
            id_plan = request.GET['id_plan']
            # Se busca el objeto de item asociado al parametro id_item
            item = Item.objects.get(pk=id_item)
            # Se buscan todos los hijos del item pasado por parametro
            items_temp = item.items_hijos.all().order_by('nombre','precio')

            if bool(items_temp):
                # Si la categoria del hijo no es planificable, entonces se debe generar otro combobox
                # Por el contrario, si es planificable, entonces se debe cargar el ultimo combobox con
                # todos los items a proyectar (agrupaciones y articulos)
                if items_temp[0].categoria.planificable == False:
                    for item_validar in items_temp:
                        # Solo se devuelven los items que pueden ser vistos por el usuario
                        #if self.request.user.get_profile().validar_visibles(item_validar):
                        if bool(Itemplan.objects.filter(item=item_validar,plan__id=id_plan)):
                                items.append({'id':item_validar.id,'nombre':item_validar.nombre,'id_cat':item_validar.categoria.id})
                else:
                    # Se obtienen todos los items de la planificacion
                    queryset = Itemplan.objects.filter(plan=id_plan, planificable=True).order_by('item__categoria','nombre','item__precio')
                    # Se itera por todos los itemplan que son hijos del item que fue recibido como parametro
                    for itemplan in [itemplan for itemplan in queryset if itemplan.item.es_padre(item)]: #populate list
                        items.append({'id':itemplan.id, 'nombre': itemplan.nombre, 'estado': itemplan.get_estado_display(), 'precio': itemplan.item.precio, 'categoria_nombre': itemplan.item.categoria.nombre})
                data['items'] = items
                data['categoria'] = {'id_categoria':items_temp[0].categoria.id, 'planificable':items_temp[0].categoria.planificable}
            return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarCategoriaListCompProyeccionView(View):
    '''
    Revise como parametro un ID de item y devuelve la lista de items hijos del item, y que el usuario
    puede ver, es decir, pertenecen a una rama sobre la cual tiene visibilidad
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            data = {}
            items = []
            id_item = json.loads(request.GET['id_item'])
            id_plan = request.GET['id_plan']
            # Se busca el objeto de item asociado al parametro id_item
            item = Item.objects.get(pk=id_item)
            # Se buscan todos los hijos del item pasado por parametro
            items_temp = item.items_hijos.all().order_by('nombre','precio')
            # Se valida que el item seleccionado tenga hijos
            if bool(items_temp):
                for item_validar in items_temp:
                    # Solo se devuelven los items que pueden ser vistos por el usuario
                    #if self.request.user.get_profile().validar_visibles(item_validar):
                    if bool(Itemplan.objects.filter(item=item_validar,plan__id=id_plan)):
                        items.append({
                            'id':item_validar.id,
                            'nombre':item_validar.nombre,
                            'precio':item_validar.precio,
                            'id_cat':item_validar.categoria.id
                            })
                data['items'] = items
                data['categoria'] = {'id_categoria':items_temp[0].categoria.id, 'planificable':items_temp[0].categoria.planificable}
            else:
                data['items'] = None
                data['categoria'] = None
            return HttpResponse(json.dumps(data), mimetype='application/json')


class BuscarVentaItemplanProyeccionView(View):
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
                itemplan_obj = Itemplan.objects.get(plan=id_plan,id=id_itemplan)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id':plan_obj.temporada.id,
                'nombre':plan_obj.temporada.nombre,
                'anio':plan_obj.anio
                }
            act_anio = plan_obj.anio
            ant_anio = plan_obj.anio - 1            
            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            item = itemplan_obj.item
            lista_hijos = []
            lista_hijos.append(item)
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            # Se verifica que el item recibido exista
            if bool(itemplan_obj):
                controlventa = Controlventa.objects.filter(organizacion=self.request.user.get_profile().organizacion).latest('fecha_creacion')

                proyeccion = OrderedDict()
                total_vta_u = 0
                total_costo = 0
                costo_unitario = 0

                # Se busca el periodo inferior y superior de la temporada a proyectar
                limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[0]
                limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[1]

                # Se buscan las temporadas de los items a proyectar.
                # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
                # mas de una temporada.
                #temporadas = ventas.order_by('item__temporada__id','item__temporada__nombre').values('item__temporada__id','item__temporada__nombre').distinct()
                #temporadas = Temporada.objects.all().order_by('-planificable','nombre')
                temporadas = Temporada.objects.all().values('nombre','id'
                    ).order_by('-planificable','nombre').distinct()
                
                # Lista de los X periodos a considerar en la proyeccion
                #periodos = ventas.order_by('anio','periodo').values('anio','periodo').distinct()
                periodos = Periodo.objects.filter(
                    Q(tiempo__anio=limite_sup['anio'],nombre__lte=limite_sup['periodo__nombre']) | 
                    Q(tiempo__anio=limite_inf['anio'],nombre__gte=limite_inf['periodo__nombre'])
                    ).order_by('tiempo__anio','nombre').values('tiempo__anio','nombre').distinct()
                
                # Se marcan los periodos que pertenecen efectivamente a la temporada en curso
                # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la temporada que esta siendo planificada
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
                            temporada__nombre=temporada['nombre'],
                            tipo__in=[0,1]
                            ).values('anio','periodo','temporada').annotate(
                            vta_n=Sum('vta_n'),vta_u=Sum('vta_u'),
                            ctb_n=Sum('ctb_n'),costo=Sum('costo'),
                            margen=Avg('margen'), tipo=Min('tipo')
                            ).order_by('anio','periodo','temporada')
                        # Se revisa si existe una venta asociada a la temporada y periodo en curso
                        if ventas.exists():
                            if ventas.count() > 1:
                                print "MAS DE UNA VENTA!!!!"
                            # Se agregan algunos calculos a las ventas
                            for venta in ventas:
                                if venta['vta_u'] != 0:
                                    total_vta_u += venta['vta_u']
                                    total_costo += venta['costo']
                                    venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                    costo_unitario = float(venta['costo'] / venta['vta_u'])

                                else:
                                    venta['precio_real'] = 0
                                venta['dcto'] = round(float(1 - (venta['precio_real'] / itemplan_obj.item.precio)), 4)
                                venta['vta_u'] = round(float(venta['vta_u']),0)
                                venta['vta_n'] = round(float(venta['vta_n']),0)
                                venta['ctb_n'] = round(float(venta['ctb_n']),0)
                                venta['costo'] = round(float(venta['costo']),0)
                                if venta['ctb_n'] != 0:
                                    venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']),4)
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
                                    'anio':periodo['tiempo__anio'],
                                    'tipo':1,
                                    'vta_n':Decimal('0.000'),
                                    'ctb_n':Decimal('0.000'),
                                    'costo':Decimal('0.000'),
                                    'vta_u':Decimal('0.000'),
                                    'temporada':temporada['id'],
                                    'periodo':periodo['nombre'],
                                    'margen':Decimal('0.000'),
                                    'precio_real':Decimal('0.000'),
                                    'dcto':Decimal('1.000')
                                }
                            # Se valida si la venta debe ser proyectable o no
                            if venta_gap['anio'] >= controlventa.anio and venta_gap['periodo'] > controlventa.periodo.nombre:
                                # Venta por proyectar
                                venta_gap['tipo'] = 1
                            else:
                                # Venta no proyectable
                                venta_gap['tipo'] = 0
                            proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
                # Se previenen errores provocados por dividir por cero
                if total_vta_u > 0:
                    costo_unitario = round(float(total_costo / total_vta_u),0)
                itemplan_json = {}
                itemplan_json['id_item'] = itemplan_obj.item.id
                itemplan_json['id_itemplan'] = itemplan_obj.id
                itemplan_json['nombre'] = itemplan_obj.nombre
                itemplan_json['precio'] = itemplan_obj.item.precio
                itemplan_json['costo_unitario'] = costo_unitario

                resumen['itemplan'] = itemplan_json
                resumen['temporadas'] = list(temporadas)
                resumen['temporada_vigente'] = temporada_vigente
                resumen['periodos'] = list(periodos)
                resumen['ventas'] = proyeccion
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)

            else:
                data = {}
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))


class BuscarVentaItemplanCompProyeccionView(View):
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
            try:
                item_obj = Item.objects.get(id=id_item)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id':plan_obj.temporada.id,
                'nombre':plan_obj.temporada.nombre,
                'anio':plan_obj.anio
                }
            act_anio = plan_obj.anio
            ant_anio = plan_obj.anio - 1
            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            lista_hijos = []
            lista_hijos.append(item_obj)
            for hijo in item_obj.get_hijos():
                lista_hijos.append(hijo)

            # Se obtiene el ultimo año y periodo en que se cargaron ventas
            controlventa = Controlventa.objects.filter(organizacion=self.request.user.get_profile().organizacion).latest('fecha_creacion')

            proyeccion = OrderedDict()
            total_vta_u = 0
            total_costo = 0
            costo_unitario = 0

            # Se busca el periodo inferior y superior de la temporada a proyectar
            limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[0]
            limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[1]

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
            # mas de una temporada.
            #temporadas = ventas.order_by('item__temporada__id','item__temporada__nombre').values('item__temporada__id','item__temporada__nombre').distinct()
            #temporadas = Temporada.objects.all().order_by('-planificable','nombre')
            temporadas = Temporada.objects.all().values('nombre','id'
                ).order_by('-planificable','nombre').distinct()
            
            # Lista de los X periodos a considerar en la proyeccion
            #periodos = ventas.order_by('anio','periodo').values('anio','periodo').distinct()
            periodos = Periodo.objects.filter(
                Q(tiempo__anio=limite_sup['anio'],nombre__lte=limite_sup['periodo__nombre']) | 
                Q(tiempo__anio=limite_inf['anio'],nombre__gte=limite_inf['periodo__nombre'])
                ).order_by('tiempo__anio','nombre').values('tiempo__anio','nombre').distinct()
            
            # Se marcan los periodos que pertenecen efectivamente a la temporada en curso
            # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la temporada que esta siendo planificada
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
                        temporada__nombre=temporada['nombre'],
                        tipo__in=[0,1]
                        ).values('anio','periodo','temporada').annotate(
                        vta_n=Sum('vta_n'),vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'),costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo')
                        ).order_by('anio','periodo','temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        if ventas.count() > 1:
                            print "MAS DE UNA VENTA!!!!"
                        # Se agregan algunos calculos a las ventas
                        for venta in ventas:
                            if venta['vta_u'] != 0:
                                total_vta_u += venta['vta_u']
                                total_costo += venta['costo']
                                venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                costo_unitario = float(venta['costo'] / venta['vta_u'])

                            else:
                                venta['precio_real'] = 0
                            if item_obj.precio != 0:
                                venta['dcto'] = round(float(1 - (venta['precio_real'] / item_obj.precio)), 4)
                            else:
                                venta['dcto'] = 0
                            venta['vta_u'] = round(float(venta['vta_u']),0)
                            venta['vta_n'] = round(float(venta['vta_n']),0)
                            venta['ctb_n'] = round(float(venta['ctb_n']),0)
                            venta['costo'] = round(float(venta['costo']),0)
                            if venta['vta_n'] != 0:
                                venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']),4)
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
                                'anio':periodo['tiempo__anio'],
                                'tipo':1,
                                'vta_n':Decimal('0.000'),
                                'ctb_n':Decimal('0.000'),
                                'costo':Decimal('0.000'),
                                'vta_u':Decimal('0.000'),
                                'temporada':temporada['id'],
                                'periodo':periodo['nombre'],
                                'margen':Decimal('0.000'),
                                'precio_real':Decimal('0.000'),
                                'dcto':Decimal('1.000')
                            }
                        # Se valida si la venta debe ser proyectable o no
                        if venta_gap['anio'] >= controlventa.anio and venta_gap['periodo'] > controlventa.periodo.nombre:
                            # Venta por proyectar
                            venta_gap['tipo'] = 1
                        else:
                            # Venta no proyectable
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            # Se previenen errores provocados por dividir por cero
            if total_vta_u > 0:
                costo_unitario = round(float(total_costo / total_vta_u),0)
            item_json = {}
            item_json['id_item'] = item_obj.id
            item_json['id_itemplan'] = item_obj.id
            item_json['nombre'] = item_obj.nombre
            item_json['precio'] = item_obj.precio
            item_json['costo_unitario'] = costo_unitario

            resumen['itemplan'] = item_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarStatsProyeccionView(View):
    '''
    Recibe un ID de plan y devuelve un objeto con las estadisticas generales
    de proyeccion
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            #id_plan = 17
            plan_obj = Plan.objects.get(pk=id_plan)
            data = {}
            stats = {}
            stats['num_items_pro'] = Itemplan.objects.filter(plan=plan_obj, estado=1, planificable=True).count()
            stats['num_items_nopro'] = Itemplan.objects.filter(plan=plan_obj, estado=0, planificable=True).count()
            stats['num_items_tot'] = stats['num_items_pro'] + stats['num_items_nopro']

            data = simplejson.dumps(stats,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')
        return HttpResponseRedirect(reverse('planes:plan_list'))


class PlanificacionView(UserInfoMixin, DetailView):
    '''
    3era fase del proceso de planificacion.
    Vista principal para la planificacion de items.
    '''
    model = Plan
    template_name = "planes/plan_planificacion_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanificacionView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PlanificacionView, self).get_context_data(**kwargs)
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto, no se puede proyectar informacion
            context['msg'] = "Primero debe definir el árbol de planificación."
        else:
            # La variable categorias deberia desaparecer
            categorias = Categoria.objects.exclude(categoria_padre=None)

            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a comparar
            combo_categorias_comp = Categoria.objects.exclude(categoria_padre=None)

            # 
            items_categoria_raiz = []
            
            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a proyectar
            # Las categorias no pueden ser planificables ni ser la ultima (organizacion)
            combo_categorias = Categoria.objects.exclude(Q(categoria_padre=None) | Q(planificable=True))
            
            # Se obtiene la categoria mas alta que cumple con estos requisitos (sera el primer combobox)
            categoria_raiz = sorted(categorias, key= lambda t: t.get_nivel())[0]

            # Luego se busca la lista de items que pertenecen a la categoria_raiz y que el usuario
            # debiese poder ver, es decir, es el item padre del item sobre el cual es responsable
            # Ejemplo: si el usuario es responsable del rubro Adulto Masculino, entonces debiese
            # poder ver como division a Hombre
            items_categoria_raiz = self.request.user.get_profile().items_visibles(categoria_raiz)
            
            context['combo_categorias'] = combo_categorias
            context['items_categoria_raiz'] = items_categoria_raiz
            context['combo_categorias_comp'] = sorted(combo_categorias_comp, key= lambda t: t.get_nivel())

        return context


class BuscarVentaTemporadaItemplanView(View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial de este de los ultimos 3 años
    de la temporada asociada al plan. Esta informacion se utiliza para completar las tablas de planificacion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            #id_plan = 14
            #id_itemplan = 2772 # Marca MLN 16990
            #resumen = OrderedDict()
            resumen = {}
            
            itemplan_obj = Itemplan.objects.get(plan=id_plan,id=id_itemplan)
            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id':itemplan_obj.plan.temporada.id,
                'nombre':itemplan_obj.plan.temporada.nombre,
                'anio':itemplan_obj.plan.anio
                }
            
            # Año actual + 1 (por planificar)
            act_anio = plan_obj.anio + 1
            # Año actual - 2 (limite inferior)
            ant_anio = plan_obj.anio - 2

            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            item = itemplan_obj.item
            lista_hijos = []
            lista_hijos.append(item)
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            # Se verifica que el item recibido exista
            if bool(itemplan_obj):
                
                proyeccion = OrderedDict()
                costo_unitario = 0            

                # Se buscan las temporadas de los items a proyectar.
                # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
                # mas de una temporada.
                #temporadas = ventas.order_by('item__temporada__id','item__temporada__nombre').values('item__temporada__id','item__temporada__nombre').distinct()
                #temporadas = Temporada.objects.all().order_by('-planificable','nombre')
                temporadas = Temporada.objects.all().values('nombre','id'
                    ).order_by('-planificable','nombre').distinct()
                
                # Lista de los X periodos a considerar en la proyeccion
                """
                periodos = Periodo.objects.filter(
                    Q(tiempo__anio=limite_sup['anio'],nombre__lte=limite_sup['periodo__nombre']) | 
                    Q(tiempo__anio=limite_inf['anio'],nombre__gte=limite_inf['periodo__nombre'])
                    ).order_by('tiempo__anio','nombre').values('tiempo__anio','nombre').distinct()
                """
                periodos = plan_obj.temporada.periodo.filter(
                    tiempo__anio__lte=act_anio,
                    tiempo__anio__gte=ant_anio
                    ).order_by('tiempo__anio','nombre'
                    ).values('tiempo__anio','nombre').distinct()
                
                # Se marcan los periodos que pertenecen efectivamente a la temporada por planificar
                # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la temporada que esta siendo planificada
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
                            ).values('anio','periodo','temporada').annotate(
                            vta_n=Sum('vta_n'),vta_u=Sum('vta_u'),
                            ctb_n=Sum('ctb_n'),costo=Sum('costo'),
                            margen=Avg('margen'), tipo=Min('tipo')
                            ).order_by('anio','periodo','temporada')
                        # Se revisa si existe una venta asociada a la temporada y periodo en curso
                        if ventas.exists():
                            if ventas.count() > 1:
                                print "MAS DE UNA VENTA!!!!"
                            # Se agregan algunos calculos a las ventas
                            for venta in ventas:
                                if venta['vta_u'] != 0:
                                    venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                    venta['costo_u'] = float(venta['costo'] / venta['vta_u'])
                                    costo_unitario = float(venta['costo'] / venta['vta_u'])

                                else:
                                    venta['precio_real'] = 0
                                venta['dcto'] = round(float(1 - (venta['precio_real'] / itemplan_obj.item.precio)), 4)
                                venta['vta_u'] = round(float(venta['vta_u']),0)
                                venta['vta_n'] = round(float(venta['vta_n']),0)
                                venta['ctb_n'] = round(float(venta['ctb_n']),0)
                                venta['costo'] = round(float(venta['costo']),0)
                                if venta['ctb_n'] != 0:
                                    venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']),4)
                                else:
                                    venta['margen'] = 0
                            # Se guarda la venta en el diccionario proyeccion
                            proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = ventas[0]
                        else:
                            # Si no existe venta, se llena el gap con una venta vacia
                            venta_gap = {
                                    'anio':periodo['tiempo__anio'],
                                    'tipo':1,
                                    'vta_n':Decimal('0.000'),
                                    'ctb_n':Decimal('0.000'),
                                    'costo':Decimal('0.000'),
                                    'vta_u':Decimal('0.000'),
                                    'temporada':temporada['id'],
                                    'periodo':periodo['nombre'],
                                    'margen':Decimal('0.000'),
                                    'precio_real':Decimal('0.000'),
                                    'dcto':Decimal('1.000'),
                                    'costo_u':Decimal('0.000')
                                }
                            # Se guarda la venta en el diccionario proyeccion
                            proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = venta_gap

                itemplan_json = {}
                itemplan_json['id_item'] = itemplan_obj.item.id
                itemplan_json['id_itemplan'] = itemplan_obj.id
                itemplan_json['nombre'] = itemplan_obj.nombre
                itemplan_json['precio'] = itemplan_obj.item.precio
                itemplan_json['costo_unitario'] = costo_unitario

                resumen['itemplan'] = itemplan_json
                resumen['temporadas'] = list(temporadas)
                resumen['temporada_vigente'] = temporada_vigente
                resumen['periodos'] = list(periodos)
                resumen['ventas'] = proyeccion
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)

            else:
                data = {}
            return HttpResponse(data, mimetype='application/json')
        return HttpResponseRedirect(reverse('planes:plan_list'))


class BuscarVentaTemporadaItemplanCompView(View):
    '''
    Recibe un item y un plan, y busca toda la informacion comercial de este de los ultimos 3 años
    de la temporada asociada al plan. Esta informacion se utiliza para completar las tablas de planificacion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_item = request.GET['id_item']
            #id_plan = 14
            #id_itemplan = 2772 # Marca MLN 16990
            #resumen = OrderedDict()
            resumen = {}

            try:
                item_obj = Item.objects.get(id=id_item)
            except ObjectDoesNotExist:
                resumen['itemplan'] = None
                resumen['temporadas'] = None
                resumen['temporada_vigente'] = None
                resumen['periodos'] = None
                resumen['ventas'] = None
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
                return HttpResponse(data, mimetype='application/json')

            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {
                'id':plan_obj.temporada.id,
                'nombre':plan_obj.temporada.nombre,
                'anio':plan_obj.anio
                }
            
            # Año actual + 1 (por planificar)
            act_anio = plan_obj.anio + 1
            # Año actual - 2 (limite inferior)
            ant_anio = plan_obj.anio - 2

            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            lista_hijos = []
            lista_hijos.append(item_obj)
            for hijo in item_obj.get_hijos():
                lista_hijos.append(hijo)
                
            proyeccion = OrderedDict()
            costo_unitario = 0            

            # Se buscan las temporadas de los items a proyectar.
            # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
            # mas de una temporada.
            #temporadas = ventas.order_by('item__temporada__id','item__temporada__nombre').values('item__temporada__id','item__temporada__nombre').distinct()
            #temporadas = Temporada.objects.all().order_by('-planificable','nombre')
            temporadas = Temporada.objects.all().values('nombre','id'
                ).order_by('-planificable','nombre').distinct()
            
            periodos = plan_obj.temporada.periodo.filter(
                tiempo__anio__lte=act_anio,
                tiempo__anio__gte=ant_anio
                ).order_by('tiempo__anio','nombre'
                ).values('tiempo__anio','nombre').distinct()
            
            # Se marcan los periodos que pertenecen efectivamente a la temporada por planificar
            # Esto se utiliza en la vista para "pintar" de un color diferente los periodos de la temporada que esta siendo planificada
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
                        ).values('anio','periodo','temporada').annotate(
                        vta_n=Sum('vta_n'),vta_u=Sum('vta_u'),
                        ctb_n=Sum('ctb_n'),costo=Sum('costo'),
                        margen=Avg('margen'), tipo=Min('tipo')
                        ).order_by('anio','periodo','temporada')
                    # Se revisa si existe una venta asociada a la temporada y periodo en curso
                    if ventas.exists():
                        if ventas.count() > 1:
                            print "MAS DE UNA VENTA!!!!"
                        # Se agregan algunos calculos a las ventas
                        for venta in ventas:
                            if venta['vta_u'] != 0:
                                venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                venta['costo_u'] = float(venta['costo'] / venta['vta_u'])
                                costo_unitario = float(venta['costo'] / venta['vta_u'])

                            else:
                                venta['precio_real'] = 0
                            if item_obj.precio != 0:
                                venta['dcto'] = round(float(1 - (venta['precio_real'] / item_obj.precio)), 4)
                            else:
                                venta['dcto'] = 0
                            venta['vta_u'] = round(float(venta['vta_u']),0)
                            venta['vta_n'] = round(float(venta['vta_n']),0)
                            venta['ctb_n'] = round(float(venta['ctb_n']),0)
                            venta['costo'] = round(float(venta['costo']),0)
                            if venta['ctb_n'] != 0:
                                venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']),4)
                            else:
                                venta['margen'] = 0
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = ventas[0]
                    else:
                        # Si no existe venta, se llena el gap con una venta vacia
                        venta_gap = {
                                'anio':periodo['tiempo__anio'],
                                'tipo':1,
                                'vta_n':Decimal('0.000'),
                                'ctb_n':Decimal('0.000'),
                                'costo':Decimal('0.000'),
                                'vta_u':Decimal('0.000'),
                                'temporada':temporada['id'],
                                'periodo':periodo['nombre'],
                                'margen':Decimal('0.000'),
                                'precio_real':Decimal('0.000'),
                                'dcto':Decimal('1.000'),
                                'costo_u':Decimal('0.000')
                            }
                        # Se guarda la venta en el diccionario proyeccion
                        proyeccion[temporada['nombre']][str(periodo['tiempo__anio']) + " " + periodo['nombre']] = venta_gap

            itemplan_json = {}
            itemplan_json['id_item'] = item_obj.id
            itemplan_json['id_itemplan'] = item_obj.id
            itemplan_json['nombre'] = item_obj.nombre
            itemplan_json['precio'] = item_obj.precio
            itemplan_json['costo_unitario'] = costo_unitario

            resumen['itemplan'] = itemplan_json
            resumen['temporadas'] = list(temporadas)
            resumen['temporada_vigente'] = temporada_vigente
            resumen['periodos'] = list(periodos)
            resumen['ventas'] = proyeccion
            data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class BuscarStatsPlanView(View):
    '''
    Recibe un ID de plan y devuelve un objeto con las estadisticas generales
    de planificacion
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            #id_plan = 17
            plan_obj = Plan.objects.get(pk=id_plan)
            data = {}
            stats = {}
            stats['num_items_pro'] = Itemplan.objects.filter(plan=plan_obj, estado=2, planificable=True).count()
            stats['num_items_nopro'] = Itemplan.objects.filter(plan=plan_obj, estado__in=[0,1], planificable=True).count()
            stats['num_items_tot'] = stats['num_items_pro'] + stats['num_items_nopro']

            data = simplejson.dumps(stats,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')
        return HttpResponseRedirect(reverse('planes:plan_list'))


class GuardarPlanificacionView(UserInfoMixin, View):
    """
    Guarda la planificacion asociada al item recibido como pararametro.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['proyeccion'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            
            # Se itera por cada temporada, periodo del objeto de proyeccion
            for temporada, periodos in data['ventas'].iteritems():
                temporada_obj = Temporada.objects.get(nombre=temporada)
                # Se itera por cada venta de cada periodo
                for periodo, venta in periodos.iteritems():
                    # Se seleccionan las ventas que no son reales (proyectadas o por proyectar)
                    if venta['tipo'] == 3:
                        defaults = {
                            'tipo': 2, # Tipo = 2 -> Planificada
                            'vta_n': venta['vta_n'],
                            'ctb_n': venta['ctb_n'],
                            'costo': venta['costo'],
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            item=itemplan_obj.item,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj, 
                            defaults=defaults)
                        if created == False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = float(venta['dcto']) 
                            obj.margen = float(venta['margen'])
                            obj.costo = float(venta['costo'])
                            if venta['vta_n'] != 0:
                                # Tipo = 2 -> Planificada
                                obj.tipo = 2
                            obj.save()

            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            # Estado = 2 -> Planificado
            itemplan_obj.estado = 2
            itemplan_obj.save()
        data = {'msg':"Planificación guardada."}
        return HttpResponse(json.dumps(data), mimetype='application/json')


class ResumenPlanView(UserInfoMixin, DetailView):
    '''
    Vista para visualizar el resultado de una planificacion.
    '''
    model = Plan
    template_name = "planes/resumen_plan_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ResumenPlanView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResumenPlanView, self).get_context_data(**kwargs)
        context['temporadas'] = Temporada.objects.all()
        return context