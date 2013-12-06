# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import View, TemplateView, ListView, DetailView
from planes.models import Plan, Itemplan, Temporada
from ventas.models import Venta, Ventaperiodo
from calendarios.models import Periodo, Tiempo
from categorias.models import Categoria, Item
from forms import PlanForm, TemporadaForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy, reverse
from planificador.views import UserInfoMixin
from django.core import serializers
from django.contrib.auth.decorators import user_passes_test
from datetime import date
from django.db.models import Sum, Avg, Max
import json
import pprint
from django.utils import simplejson
from collections import defaultdict
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q


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
        context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1).count()
        context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0).count()
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
            context['items'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0).order_by('id')[1:3]
            context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1).count()
            context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0).count()
            context['num_items_tot'] = context['num_items_pro'] + context['num_items_nopro']
            
            # La variable categorias deberia desaparecer
            categorias = Categoria.objects.exclude(categoria_padre=None)
            context['categorias'] = sorted(categorias, key= lambda t: t.get_nivel())
            
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

        return context


class GuardarProyeccionView(UserInfoMixin, View):
    """
    Revise un objecto con la proyeccion realizada. Incluye el plan asociado, el item y las ventas
    divididas por temporada
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['proyeccion'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            
            # Se verifica si el item pertenece a una categoria hoja, en caso afirmativo,
            # se trata de un item no agrupado, por lo tanto, se imputan todas las ventas proyectadas a el
            if bool(itemplan_obj.item.categoria.get_children()) == False:
                for temporada, ventas in data['ventas'].iteritems():
                    for ventaperiodo in ventas:
                        if ventaperiodo['tipo'] != 0:
                            obj = Ventaperiodo.objects.get(item=itemplan_obj.item,anio=ventaperiodo['anio'],periodo=ventaperiodo['periodo'])
                            obj.vta_n = ventaperiodo['vta_n']
                            obj.vta_u = ventaperiodo['vta_u']
                            obj.ctb_n = ventaperiodo['ctb_n']
                            obj.dcto = float(ventaperiodo['dcto']) 
                            obj.margen = float(ventaperiodo['margen'])
                            obj.costo = float(ventaperiodo['costo'])
                            if ventaperiodo['vta_n'] != 0:
                                # Tipo = 2 -> Proyectada
                                obj.tipo = 2
                            obj.save()
            
            # El item pertenece a una categoria con hijos, por lo tanto, es una agrupacion. Esto implica
            # que la venta debe ser imputada a algun item hijo por cada temporada
            else:
                # Se itera sobre las ventas por cada temporada
                for temporada, ventas in data['ventas'].iteritems():
                    # Se obtiene el primer hijo de la temporada correspondiente
                    item = itemplan_obj.item.get_children().filter(temporada__nombre=temporada)[:1].get()
                    # Se itera por cada una de las ventas de la temporada
                    for ventaperiodo in ventas:
                        if ventaperiodo['tipo'] != 0:
                            obj = Ventaperiodo.objects.get(item=item,anio=ventaperiodo['anio'],periodo=ventaperiodo['periodo'])
                            obj.vta_n = ventaperiodo['vta_n']
                            obj.vta_u = ventaperiodo['vta_u']
                            obj.ctb_n = ventaperiodo['ctb_n']
                            obj.dcto = float(ventaperiodo['dcto']) 
                            obj.margen = float(ventaperiodo['margen'])
                            obj.costo = float(ventaperiodo['costo'])
                            if ventaperiodo['vta_n'] != 0:
                                # Tipo = 2 -> Proyectada
                                obj.tipo = 2
                            obj.save()
            # Estado = 0 -> Pendiente
            # Estado = 1 -> Proyectado
            itemplan_obj.estado = 1
            itemplan_obj.save()
        return HttpResponseRedirect(reverse('planes:plan_proyecciones_detail', args=(plan_obj.id,)))


class BuscarItemplanListProyeccionView(View):
    '''
    Revise como parametro una categoria y un plan, y busca todos los objetos itemplan
    que pertenecen a este conjunto de parametros. La respuesta es una lista de objetos
    itemplan usados para llenar un combobox.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_cat = json.loads(request.GET['id_cat'])
            queryset = Itemplan.objects.filter(plan=id_plan,item__categoria__id=id_cat).order_by('estado')
            list = []
            for itemplan in queryset: #populate list
                list.append({'id':itemplan.id, 'nombre': itemplan.nombre, 'estado': itemplan.get_estado_display(), 'precio': itemplan.item.precio})
            data = json.dumps(list) #dump list as JSON
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))


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
            items_temp = item.items_hijos.all().order_by('nombre')
            # Si la categoria del hijo no es planificable, entonces se debe generar otro combobox
            # Por el contrario, si es planificable, entonces se debe cargar el ultimo combobox con
            # todos los items a proyectar (agrupaciones y articulos)
            if items_temp[0].categoria.planificable == False:
                for item_validar in items_temp:
                    # Solo se devuelven los items que pueden ser vistos por el usuario
                    if self.request.user.get_profile().validar_visibles(item_validar):
                        items.append({'id':item_validar.id,'nombre':item_validar.nombre,'id_cat':item_validar.categoria.id})
            else:
                queryset = Itemplan.objects.filter(plan=id_plan).order_by('estado','item__categoria','nombre')
                for itemplan in queryset: #populate list
                    items.append({'id':itemplan.id, 'nombre': itemplan.nombre, 'estado': itemplan.get_estado_display(), 'precio': itemplan.item.precio, 'categoria_nombre': itemplan.item.categoria.nombre})
            data['items'] = items
            data['categoria'] = {'id_categoria':items_temp[0].categoria.id, 'planificable':items_temp[0].categoria.planificable}
            return HttpResponse(json.dumps(data), mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))


class BuscarItemplanProyeccionView(View):
    '''
    Recibe un itemplan y un plan, y busca el itemplan asociado. Se utiliza para presentar
    informacion general del objeto.

    *** !! Por el momento no se encuentra en uso !! ***
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            itemplan_obj = Itemplan.objects.filter(plan=id_plan,id=id_itemplan)
            data = serializers.serialize('json', itemplan_obj)
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))


class BuscarVentaItemplanProyeccionView(View):
    '''
    Recibe un itemplan y un plan, y busca toda la informacion comercial de este de los ultimos
    12 periodos. Esta informacion se utiliza para completar las tablas de proyeccion
    de unidades vendidas y descuentos.
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            act_anio = date.today().isocalendar()[0]
            ant_anio = date.today().isocalendar()[0] - 1
            semana = date.today().isocalendar()[1]
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            itemplan_obj = Itemplan.objects.get(plan=id_plan,id=id_itemplan)
            plan_obj = Plan.objects.get(pk=id_plan)
            temporada_vigente = {'id':itemplan_obj.plan.temporada.id, 'nombre':itemplan_obj.plan.temporada.nombre, 'anio':itemplan_obj.plan.anio}
            
            # Se busca la lista de items del item a proyectar. Si el item es un nivel agrupado
            # se devuelven todos sus hijos hojas (con venta), si el item es una hoja, se devuelve
            # a si mismo
            item = itemplan_obj.item
            lista_hijos = []
            for hijo in item.get_hijos():
                lista_hijos.append(hijo)

            # Se verifica que el item recibido exista
            if bool(itemplan_obj):
                
                # Se busca el periodo inferior y superior de la temporada a proyectar
                limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[0]
                limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio)[1]
                # Busca las ventas asociadas a los últimos 12 periodos
                ventas = Ventaperiodo.objects.filter(
                Q(item__in=lista_hijos),
                Q(anio=limite_sup['anio'], periodo__lte=limite_sup['periodo__nombre']) | Q(anio=limite_inf['anio'],periodo__gte=limite_inf['periodo__nombre'])
                ).values('anio','periodo','tipo','item__temporada__nombre').annotate(
                vta_n=Sum('vta_n'),vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),costo=Sum('costo'),
                margen=Avg('margen')).order_by('item__temporada__nombre','anio','periodo')

                # Se buscan las temporadas de los items a proyectar.
                # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
                # mas de una temporada.
                temporadas = ventas.order_by('item__temporada__id','item__temporada__nombre').values('item__temporada__id','item__temporada__nombre').distinct()
                periodos = ventas.order_by('anio','periodo').values('anio','periodo').distinct()
                
                # Se marcan los periodos que pertenecen efectivamente a la temporada en curso
                for periodo in periodos:
                    if plan_obj.temporada.comprobar_periodo(periodo['periodo']):
                        periodo['temporada'] = True
                    else:
                        periodo['temporada'] = False

                costo_unitario = 0
                precio_blanco_sin_iva = itemplan_obj.item.precio / 1.19

                for periodo in ventas:
                    
                    if periodo['vta_u'] != 0:
                        periodo['precio_real'] = float(periodo['vta_n'] / periodo['vta_u'])
                        costo_unitario = float(periodo['costo'] / periodo['vta_u'])

                    else:
                        periodo['precio_real'] = 0
                    periodo['dcto'] = round(float((precio_blanco_sin_iva - periodo['precio_real']) / precio_blanco_sin_iva), 4)
                    periodo['vta_u'] = round(float(periodo['vta_u']),0)
                    periodo['vta_n'] = round(float(periodo['vta_n']),0)
                    periodo['ctb_n'] = round(float(periodo['ctb_n']),0)
                    periodo['costo'] = round(float(periodo['costo']),0)
                    if periodo['ctb_n'] != 0:
                        periodo['margen'] = round(float(periodo['ctb_n'] / periodo['vta_n']),4)
                    else:
                        periodo['margen'] = 0
                
                ventas_por_temporada = defaultdict(list)
                for temporada in temporadas:
                    for venta in ventas:
                        if temporada['item__temporada__nombre'] == venta['item__temporada__nombre']:
                            ventas_por_temporada[temporada['item__temporada__nombre']].append(venta)

                itemplan_json = {}
                itemplan_json['id_item'] = itemplan_obj.item.id
                itemplan_json['id_itemplan'] = itemplan_obj.id
                itemplan_json['nombre'] = itemplan_obj.nombre
                itemplan_json['precio'] = itemplan_obj.item.precio
                itemplan_json['costo_unitario'] = costo_unitario
                itemplan_json['precio_blanco_sin_iva'] = precio_blanco_sin_iva

                #resumen['ventas'] = list(ventas)
                resumen['itemplan'] = itemplan_json
                resumen['temporadas'] = list(temporadas)
                resumen['temporada_vigente'] = temporada_vigente
                resumen['ventas'] = ventas_por_temporada
                resumen['periodos'] = list(periodos)
                
                data = simplejson.dumps(resumen,cls=DjangoJSONEncoder)
            else:
                data = {}
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))