# -*- coding: utf-8 -*-
from collections import OrderedDict
from decimal import Decimal
from django import db
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy, reverse
from django.db.models import Q, F, Sum, Avg, Max, Min
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import View, TemplateView, ListView, DetailView
from braces.views import LoginRequiredMixin, GroupRequiredMixin
from xlsxwriter.workbook import Workbook
from .models import Plan, Itemplan, Temporada
from ventas.models import Venta, Ventaperiodo, Controlventa
from calendarios.models import Periodo, Tiempo
from categorias.models import Categoria, Item
from forms import PlanForm, TemporadaForm
from planes.models import generateUUID
from planificador.views import UserInfoMixin
import json
import pprint
import cStringIO as StringIO


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
        return Plan.objects.filter(usuario_creador=self.request.user).order_by('-anio','temporada__nombre')


class PlanCreateView(LoginRequiredMixin, UserInfoMixin, CreateView):
    model = Plan
    template_name = "planes/plan_create.html"
    form_class = PlanForm

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        form.instance.nombre = str(form.instance.anio) + " - " + form.instance.temporada.nombre
        return super(PlanCreateView, self).form_valid(form)


class PlanDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    Vista para visualizar la ficha de una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_detail.html"

    def get_context_data(self, **kwargs):
        context = super(PlanDetailView, self).get_context_data(**kwargs)
        context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1, planificable=True).count()
        context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0, planificable=True).count()
        return context

        
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
    Vista que revise como parametros el plan y un arreglo de ID con todos los
    items que deben ser planificados. 
    '''
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['plan'])
            # Campo obtenido para guardar la relacion padre-hijo entre nodos
            obj_arr_item_padres = data['items_padres']
            #print obj_arr_item_padres
            # Reset queries
            db.reset_queries()
            # Si el arbol existe, debe ser eliminado
            if bool(Itemplan.objects.filter(plan=data['plan'])):
                Itemplan.objects.filter(plan=data['plan']).delete()
            plan_obj = Plan.objects.get(pk=data['plan'])
            #items_obj_arr = [Item.objects.get(pk=val) for val in data['items']]
            items_obj_arr = Item.objects.filter(pk__in=data['items']).prefetch_related('item_padre')
            itemplan_obj_arr = [Itemplan(nombre=x.nombre, plan=plan_obj, item=x, item_padre=None) for x in items_obj_arr]
            # Se marcan los itemplan que pueden ser planificados
            for itemplan_obj in itemplan_obj_arr:
                #print itemplan_obj.itemplan_uuid
                #print itemplan_obj.item.id
                #obj_uuid = [x for x in obj_arr_item_padres if x['id'] == itemplan_obj.item.id][0]
                #itemplan_obj.itemplan_uuid = obj_uuid['uuid']
                #itemplan_obj.itemplan_padre_uuid_id = obj_uuid['padre_uuid']
                if itemplan_obj.item.id in data['items_planificables']:
                    itemplan_obj.planificable = True
            plan_obj.estado = 1
            plan_obj.save()

            # Se guardar los itemplan que componen el arbol de planificacion
            Itemplan.objects.bulk_create(itemplan_obj_arr)
            print "QUERIES: " + str(len(db.connection.queries))

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
            print "QUERIES: " + str(len(db.connection.queries))
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
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto, no se puede proyectar informacion
            context['msg'] = "Primero debe definir el árbol de planificación."
        else:
            # Se deben presentar uno a uno los items a proyectar
            # context['items'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0).order_by('id')[1:3]
            context['num_items_pro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=1, planificable=True).count()
            context['num_items_nopro'] = Itemplan.objects.filter(plan=context['plan'].id, estado=0, planificable=True).count()
            context['num_items_tot'] = context['num_items_pro'] + context['num_items_nopro']
            
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
            categoria_raiz = sorted(items_responsable, key= lambda t: t.categoria.get_nivel())[0]

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
            context['combo_categorias_comp'] = sorted(combo_categorias_comp, key= lambda t: t.get_nivel())
            context['items_categoria_raiz'] = items_categoria_raiz

        return context


class ProyeccionesView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    2da fase del proceso de planificacion.
    Vista principal para la proyeccion de datos historicos de items.
    '''
    model = Plan
    template_name = "planes/plan_proyecciones_detail.html"

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
            categoria_raiz = sorted(items_responsable, key= lambda t: t.categoria.get_nivel())[0]

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
            data = json.loads(request.POST['datos_tarea'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'],plan=plan_obj)
            
            # Se revisa si la categoria del item que esta siendo proyectado tiene hijos (si pertenece a una categoria hoja o no), 
            # en caso de tener hijos, se imputa la proyeccion al primero de ellos
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
                            'margen': venta['margen']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            plan=plan_obj,
                            item=item_proyectado,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj,
                            tipo=1, # Tipo = 1 -> Proyectada
                            defaults=defaults)
                        if created == False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = float(venta['dcto']) 
                            obj.margen = float(venta['margen'])
                            obj.costo = float(venta['costo'])
                            if venta['vta_n'] != 0:
                                # Tipo = 1 -> Proyectada
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
            # Se busca el objeto de plan
            plan_obj = Plan.objects.get(pk=id_plan)
            # Se busca el objeto de item asociado al parametro id_item
            item_seleccionado = Item.objects.get(pk=id_item)
            # Se busca el objecto de itemplan asociado al item escogido
            itemplan_seleccionado = Itemplan.objects.get(plan=plan_obj,item=item_seleccionado)
            # Se buscan todos los hijos del item pasado por parametro
            items_temp = item_seleccionado.get_children()

            if bool(items_temp):
                # Si la categoria del hijo no es planificable, entonces se debe generar otro combobox
                # Por el contrario, si es planificable, entonces se debe cargar el ultimo combobox con
                # todos los items a proyectar (agrupaciones y articulos)
                if items_temp[0].categoria.planificable == False:
                    for item_validar in items_temp:
                        # Solo se devuelven los items que pueden ser vistos por el usuario
                        #if self.request.user.get_profile().validar_visibles(item_validar):
                        if bool(Itemplan.objects.filter(item=item_validar,plan=plan_obj)):
                                items.append({'id':item_validar.id,'nombre':item_validar.nombre,'id_cat':item_validar.categoria.id})
                else:
                    # Se itera sobre la lista de hijos planificables del item seleccionado en el combobox
                    for itemplan in itemplan_seleccionado.get_hijos_planificables():
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
            # Se busca el objeto de plan
            plan_obj = Plan.objects.get(pk=id_plan)
            # Se busca el objeto de item asociado al parametro id_item
            item_seleccionado = Item.objects.get(pk=id_item)
            # Se buscan todos los hijos del item pasado por parametro
            items_temp = item_seleccionado.get_children()
            # Se valida que el item seleccionado tenga hijos
            if bool(items_temp):
                for item_validar in items_temp:
                    # Solo se devuelven los items que pueden ser vistos por el usuario
                    #if bool(Itemplan.objects.filter(item=item_validar,plan=plan_obj)):
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
                temporadas = Temporada.objects.all().values('nombre','id'
                    ).order_by('-planificable','nombre').distinct()
                
                # Lista de los X periodos a considerar en la proyeccion
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
                                    venta['dcto'] = round(float(1 - (venta['precio_real'] / itemplan_obj.item.precio)), 4)

                                else:
                                    venta['precio_real'] = 0
                                    venta['dcto'] = 0                                
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
                                    'dcto':Decimal('0.000')
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
                                'dcto':Decimal('0.000')
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
                costo_unitario = round(float(total_costo / total_vta_u), 0)
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
            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class PlanificacionView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    3era fase del proceso de planificacion.
    Vista principal para la planificacion de items.
    '''
    model = Plan
    template_name = "planes/plan_planificacion_detail.html"

    def get_context_data(self, **kwargs):
        context = super(PlanificacionView, self).get_context_data(**kwargs)
        if context['plan'].estado == 0:
            # El arbol no ha sido generado, por lo tanto,
            # no se puede proyectar informacion
            context['msg'] = "Primero debe definir el árbol de planificación."
        else:
            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a comparar
            combo_categorias_comp = Categoria.objects.filter(organizacion=self.request.user.get_profile().organizacion).exclude(categoria_padre=None)

            # 
            items_categoria_raiz = []
            
            # Lista de items sobre los cuales el usuario es responsable
            items_responsable = Item.objects.filter(usuario_responsable=self.request.user)

            # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a proyectar
            # Las categorias no pueden ser planificables ni ser la ultima (organizacion)
            combo_categorias = Categoria.objects.filter(organizacion=self.request.user.get_profile().organizacion).exclude(Q(categoria_padre=None) | Q(planificable=True))
            
            # Se obtiene la categoria mas alta que cumple con estos requisitos (sera el primer combobox)
            categoria_raiz = sorted(items_responsable, key= lambda t: t.categoria.get_nivel())[0]

            # Se eliminan las categorias que estan por sobre la categoria de la categoria raiz
            combo_categorias = [x for x in combo_categorias if x.get_nivel() >= categoria_raiz.get_nivel()]
            combo_categorias_comp = [x for x in combo_categorias_comp if x.get_nivel() >= categoria_raiz.get_nivel()]

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

            # Se verifica que el item recibido exista
            if bool(itemplan_obj):
                
                proyeccion = OrderedDict()
                costo_unitario = 0            

                # Se buscan todas las temporadas
                temporadas = Temporada.objects.all().values('nombre','id'
                    ).order_by('-planificable','nombre').distinct()
                
                # Se buscan los periodos considerados en la vista de planificacion
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
                                    if venta['costo_u'] != 0:
                                        costo_unitario = venta['costo_u']
                                    #costo_unitario = float(venta['costo'] / venta['vta_u'])
                                    venta['dcto'] = round(float(1 - (venta['precio_real'] / itemplan_obj.item.precio)), 4)
                                else:
                                    venta['precio_real'] = 0
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
                                    'dcto':Decimal('0.000'),
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
            
            # Año actual (por planificar)
            act_anio = plan_obj.anio
            # Año actual - 3 (limite inferior)
            ant_anio = plan_obj.anio - 3

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


class GuardarPlanificacionView(View):
    """
    Guarda la planificacion asociada al item recibido como pararametro.
    """
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['datos_tarea'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            
            # Se revisa si la categoria del item que esta siendo planificado tiene hijos (si pertenece a una categoria hoja o no), 
            # en caso de tener hijos, se imputa la planificacion al primero de ellos
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
                            'costo': float(venta['costo_u'] * venta['vta_u']),
                            'vta_u': venta['vta_u'],
                            'stk_u': Decimal('0.000'),
                            'stk_v': Decimal('0.000'),
                            'margen': venta['margen']
                        }
                        obj, created = Ventaperiodo.objects.get_or_create(
                            plan=plan_obj,
                            item=item_proyectado,
                            anio=venta['anio'],
                            periodo=venta['periodo'],
                            temporada=temporada_obj, 
                            tipo=2, # Tipo = 2 -> Planificada
                            defaults=defaults)
                        if created == False:
                            obj.vta_n = venta['vta_n']
                            obj.vta_u = venta['vta_u']
                            obj.ctb_n = venta['ctb_n']
                            obj.dcto = float(venta['dcto']) 
                            obj.margen = float(venta['margen'])
                            obj.costo = float(venta['costo_u'] * venta['vta_u'])
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


class SaldosAvancesView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    4ta fase del proceso de planificacion.
    Vista principal para la planificacion de saldos y avances
    '''
    model = Plan
    template_name = "planes/plan_saldosavances_detail.html"

    def get_context_data(self, **kwargs):
        context = super(SaldosAvancesView, self).get_context_data(**kwargs)
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
            categoria_raiz = sorted(items_responsable, key= lambda t: t.categoria.get_nivel())[0]

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
            context['combo_categorias_comp'] = sorted(combo_categorias_comp, key= lambda t: t.get_nivel())
            context['items_categoria_raiz'] = items_categoria_raiz

        return context


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

            # Se verifica que el item recibido exista
            if bool(itemplan_obj):

                proyeccion = OrderedDict()
                total_vta_u = 0
                total_costo = 0
                costo_unitario = 0

                # Se busca el periodo inferior y superior de la temporada a proyectar
                limite_inf = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[0] 
                limite_sup = plan_obj.temporada.periodos_proyeccion(plan_obj.anio + 1)[1]

                # Se buscan las temporadas de los items a proyectar.
                # Siempre es una si el item es una hoja, pero si es una agrupacion, puede que considere
                # mas de una temporada.
                temporadas = Temporada.objects.all().values('nombre','id'
                    ).order_by('-planificable','nombre').distinct()
                
                # Lista de los X periodos a considerar en la planificacion de saldos y avances
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
                                    total_vta_u += venta['vta_u']
                                    total_costo += venta['costo']
                                    venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                    costo_unitario = float(venta['costo'] / venta['vta_u'])
                                    venta['dcto'] = round(float(1 - (venta['precio_real'] / itemplan_obj.item.precio)), 4)

                                else:
                                    venta['precio_real'] = 0
                                    venta['dcto'] = 0
                                venta['vta_u'] = round(float(venta['vta_u']), 0)
                                venta['vta_n'] = round(float(venta['vta_n']), 0)
                                venta['ctb_n'] = round(float(venta['ctb_n']), 0)
                                venta['costo'] = round(float(venta['costo']), 0)
                                if venta['ctb_n'] != 0:
                                    venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']), 4)
                                else:
                                    venta['margen'] = 0
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
                                'dcto': Decimal('0.000')
                            }
                            if plan_obj.temporada.comprobar_periodo(venta_gap['periodo']):
                                venta_gap['tipo'] = 0
                            proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
                # Se previenen errores provocados por dividir por cero
                #if total_vta_u > 0:
                    #costo_unitario = round(float(total_costo / total_vta_u),0)
                itemplan_json = {}
                itemplan_json['id_item'] = itemplan_obj.item.id
                itemplan_json['id_itemplan'] = itemplan_obj.id
                itemplan_json['nombre'] = itemplan_obj.nombre
                itemplan_json['precio'] = itemplan_obj.item.precio
                #itemplan_json['costo_unitario'] = costo_unitario
                itemplan_json['costo_unitario'] = itemplan_obj.item.calcularCostoUnitario()

                resumen['itemplan'] = itemplan_json
                resumen['temporadas'] = list(temporadas)
                resumen['temporada_vigente'] = temporada_vigente
                resumen['periodos'] = list(periodos)
                resumen['ventas'] = proyeccion
                data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)

            else:
                data = {}
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))


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
            try:
                item_obj = Item.objects.get(id=id_item)
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
            lista_hijos = []
            lista_hijos.append(item_obj)
            for hijo in item_obj.get_hijos():
                lista_hijos.append(hijo)

            proyeccion = OrderedDict()
            total_vta_u = 0
            total_costo = 0

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
                        margen=Avg('margen'), tipo=Min('tipo')
                        ).order_by('anio', 'periodo', 'temporada')
                    # Se revisa si existe una venta asociada a la temporada
                    # y periodo en curso
                    if ventas.exists():
                        if ventas.count() > 1:
                            print "MAS DE UNA VENTA!!!!"
                        # Se agregan algunos calculos a las ventas
                        for venta in ventas:
                            if venta['vta_u'] != 0:
                                total_vta_u += venta['vta_u']
                                total_costo += venta['costo']
                                venta['precio_real'] = float(venta['vta_n'] / venta['vta_u']) * 1.19
                                if item_obj.precio != 0:
                                    venta['dcto'] = round(float(1 - (venta['precio_real'] / item_obj.precio)), 4)
                                else:
                                    venta['dcto'] = 0

                            else:
                                venta['precio_real'] = 0
                                venta['dcto'] = 0
                            venta['vta_u'] = round(float(venta['vta_u']), 0)
                            venta['vta_n'] = round(float(venta['vta_n']), 0)
                            venta['ctb_n'] = round(float(venta['ctb_n']), 0)
                            venta['costo'] = round(float(venta['costo']), 0)
                            if venta['ctb_n'] != 0:
                                venta['margen'] = round(float(venta['ctb_n'] / venta['vta_n']), 4)
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
                            'dcto': Decimal('0.000')
                            }
                        if plan_obj.temporada.comprobar_periodo(venta_gap['periodo']):
                            venta_gap['tipo'] = 0
                        proyeccion[temporada['nombre']][periodo['nombre']] = venta_gap
            itemplan_json = {}
            itemplan_json['id_item'] = item_obj.id
            itemplan_json['id_itemplan'] = item_obj.id
            itemplan_json['nombre'] = item_obj.nombre
            itemplan_json['precio'] = item_obj.precio
            itemplan_json['costo_unitario'] = item_obj.calcularCostoUnitario()
            resumen['itemplan'] = itemplan_json
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
    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

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
                            'margen': venta['margen']
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


class ResumenPlanView(LoginRequiredMixin, UserInfoMixin, DetailView):
    '''
    Vista para visualizar el resultado de una planificacion.
    '''
    model = Plan
    template_name = "planes/plan_resumen_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ResumenPlanView, self).get_context_data(**kwargs)
        context['temporadas'] = Temporada.objects.all()

        items_categoria_raiz = []

        # Se busca la lista de categorias que se usaran como combobox para la busqueda de items a comparar
        combo_categorias_comp = Categoria.objects.filter(organizacion=self.request.user.get_profile().organizacion).exclude(categoria_padre=None)
        # Se busca la lista de items sobre los cuales el usuario es responsable
        items_responsable = Item.objects.filter(usuario_responsable=self.request.user)

        # Se obtiene la categoria mas alta que cumple con estos requisitos (sera el primer combobox)
        #categoria_raiz = sorted(combo_categorias_comp, key= lambda t: t.get_nivel())[0]
        categoria_raiz = sorted(items_responsable, key=lambda t: t.categoria.get_nivel())[0]

        # Luego se busca la lista de items que pertenecen a la categoria_raiz y que el usuario
        # debiese poder ver, es decir, es el item padre del item sobre el cual es responsable
        # Ejemplo: si el usuario es responsable del rubro Adulto Masculino, entonces debiese
        # poder ver como division a Hombre

        # Se obtiene una lista de items que el usuario puede ver de la categoria raiz
        items_categoria_raiz = self.request.user.get_profile().items_visibles(categoria_raiz)

        # Se eliminan las categorias que esten por sobre la categoria del item responsable
        combo_categorias_comp = [x for x in combo_categorias_comp if x.get_nivel() >= categoria_raiz.get_nivel()]

        context['combo_categorias_comp'] = sorted(combo_categorias_comp, key=lambda t: t.get_nivel())
        context['items_categoria_raiz'] = items_categoria_raiz
        return context


class ResumenDataGraficosView(View):
    '''
    Recibe un ID de plan, un ID de temporada y un ID de item. Devuelve la venta total
    de los ultimos 3 años asociadas al plan, temporada e item.
    '''
    # PRECIO REAL: venta.vta_n / venta.vta_u * 1.19
    # COSTO: venta.costo / venta.vta_u
    # DESCUENTO: precio_blanco - precio_real
    def get(self, request, *args, **kwargs):
        if request.GET:
            resumen = {}
            data = {}

            # Label para todos los graficos (años)
            rows_label = []

            rows_venta = []
            rows_crecimiento_venta = []
            rows_venta_label = []

            rows_unidades = []
            rows_crecimiento_unidades = []
            rows_unidades_label = []

            rows_contribucion = []
            rows_crecimiento_contribucion = []
            rows_contribucion_label = []
            rows_contribucion_tooltip = []

            rows_margen = []
            rows_margen_label = []
            rows_margen_tooltip = []

            rows_dcto_precio_imp = []
            rows_dcto_precio_imp_label = []
            rows_dcto_precio_imp_tooltip = []
            rows_costo = []

            JSONVenta = OrderedDict()
            JSONUnidades = OrderedDict()
            JSONContribucion = OrderedDict()
            JSONMargen = OrderedDict()
            JSONDctoPrecio = OrderedDict()
            JSONCosto = OrderedDict()

            JSON = {}

            id_plan = request.GET['id_plan']
            id_temporada = request.GET['id_temporada']
            id_item = request.GET['id_item']
            tipo_obj_item = request.GET['tipo_obj_item']
            if tipo_obj_item == 'item':  # Se revisa si el ID corresponde a un Item o a un Itemplan
                item_obj = Item.objects.get(pk=id_item)
            else:
                itemplan_obj = Itemplan.objects.get(pk=id_item)
                item_obj = itemplan_obj.item
            plan_obj = Plan.objects.get(pk=id_plan)

            # Se verifica la existencia de la temporada, ya que la opcion temporada = TOTAL no existe
            # a nivel de base de datos.
            try:
                temporada_obj = Temporada.objects.get(pk=id_temporada)
                estadisticas = plan_obj.resumen_estadisticas(temporada_obj, item_obj)
            # Si la temporada no existe, se asume que se trata de la temporada TOTAL, y por lo tanto,
            # se llama al metodo resumen_estadisticas con el parametro TT
            except ObjectDoesNotExist:
                estadisticas = plan_obj.resumen_estadisticas("TT", item_obj)

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

                vta_n, vta_u, ctb_n = int(x['vta_n']), int(x['vta_u']), int(x['ctb_n'])
                costo, precio_prom = int(x['costo']), int(x['precio_prom'])
                anio = str(x['anio'])
                # Calculo de margen
                if vta_n != 0:
                    margen = float(ctb_n) / vta_n
                else:
                    margen = 0

                # Calculos para el grafico de precio blanco
                if x['vta_u'] != 0:
                    precio_real_cimp = int(vta_n / vta_u)
                    precio_real_simp = int(precio_real_cimp * 0.81)
                    impuesto = precio_real_cimp - precio_real_simp
                    costo_unitario = int(costo / vta_u)
                else:
                    precio_real, costo_unitario, precio_real_simp, precio_real_cimp, impuesto = 0, 0, 0, 0, 0
                descuento = precio_prom - precio_real_cimp  # precio blanco promedio - precio real

                # Se genera el arreglo que contiene las etiquetas de cada categoria (años)
                rows_label.append(anio)

                if x > 0 and temp_vta_n != 0 and temp_vta_u != 0 and temp_ctb_n != 0:
                    crecimiento_vta_n = float((vta_n - temp_vta_n)) / temp_vta_n
                    crecimiento_vta_u = float((vta_u - temp_vta_u)) / temp_vta_u
                    crecimiento_ctb_n = float((ctb_n - temp_ctb_n)) / temp_ctb_n

                else:
                    crecimiento_vta_n, crecimiento_vta_u, crecimiento_ctb_n = 0, 0, 0

                # Se agrega el crecimiento por año a la lista
                row_crecimiento_venta.append('{:.1%}'.format(crecimiento_vta_n))
                row_crecimiento_venta.append("#777")
                row_crecimiento_venta.append("white")
                row_crecimiento_venta.append(-1)
                row_crecimiento_venta.append(-10)
                row_crecimiento_unidades.append('{:.1%}'.format(crecimiento_vta_u))
                row_crecimiento_unidades.append("#777")
                row_crecimiento_unidades.append("white")
                row_crecimiento_unidades.append(-1)
                row_crecimiento_unidades.append(-10)
                row_crecimiento_contribucion.append('{:.1%}'.format(crecimiento_ctb_n))
                row_crecimiento_contribucion.append("#777")
                row_crecimiento_contribucion.append("white")
                row_crecimiento_contribucion.append(-1)
                row_crecimiento_contribucion.append(-10)

                # Se genera el arreglo que contiene los valores de cada categoria (años)
                row_venta.append(vta_n)
                row_unidades.append(vta_u)
                row_contribucion.append(ctb_n)
                row_precio_dcto_imp.append(descuento)
                row_precio_dcto_imp.append(impuesto)
                row_precio_dcto_imp.append(precio_real_simp)

                # Se agregan los valores al arreglo que contiene todos los valores por año
                rows_venta.append(row_venta)
                rows_unidades.append(row_unidades)
                rows_contribucion.append(row_contribucion)
                rows_margen.append(round(margen, 2))
                rows_dcto_precio_imp.append(row_precio_dcto_imp)
                rows_costo.append(costo_unitario)

                # Se agrega el crecimiento por año a la lista de crecimientos
                rows_crecimiento_venta.append(row_crecimiento_venta)
                rows_crecimiento_unidades.append(row_crecimiento_unidades)
                rows_crecimiento_contribucion.append(row_crecimiento_contribucion)

                contribucion_tooltip_msg = (
                    "<p><b>Año: </b>" + anio
                    + "</p><p><b>Contribución: </b>" + '{:,}'.format(ctb_n)
                    + "</p><p><b>Margen: </b>" + '{:.1%}'.format(margen)
                    + "</p><p><b>Crecimiento: </b>" + '{:.1%}'.format(crecimiento_ctb_n)
                    + "</p>")

                margen_tooltip_msg = contribucion_tooltip_msg

                dcto_precio_tooltip_msg = ("<p><b>Año: </b>" + anio +
                    "</p><p><b>Precio Blanco: </b>" + '{:,}'.format(precio_prom)  +
                    "</p><p><b>Precio Real: </b>" + '{:,}'.format(precio_real_simp) +
                    "</p><p><b>Impuesto (19%): </b>" + '{:,}'.format(impuesto) +
                    "</p><p><b>Descuento: </b>" + '{:,}'.format(descuento) +
                    "</p><p><b>Costo: </b>" + '{:,}'.format(costo_unitario) +
                    "</p>")

                rows_margen_tooltip.append(margen_tooltip_msg)
                rows_contribucion_tooltip.append(contribucion_tooltip_msg)
                rows_dcto_precio_imp_tooltip.append(dcto_precio_tooltip_msg)

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
            JSONContribucion['tooltips'] = rows_contribucion_tooltip

            JSONMargen['cols'] = rows_label
            JSONMargen['rows'] = rows_margen
            JSONMargen['tooltips'] = rows_margen_tooltip

            JSONDctoPrecio['cols'] = rows_label
            JSONDctoPrecio['rows'] = rows_dcto_precio_imp
            JSONDctoPrecio['tooltips'] = rows_dcto_precio_imp_tooltip

            JSONCosto['rows'] = rows_costo

            JSON['venta'] = JSONVenta
            JSON['unidades'] = JSONUnidades
            JSON['contribucion'] = JSONContribucion
            JSON['margen'] = JSONMargen
            JSON['dcto_precio'] = JSONDctoPrecio
            JSON['costo'] = JSONCosto

            resumen['estadisticas'] = JSON

            data = simplejson.dumps(resumen, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


def ExportarExcelView(request, pk=None):
    """
    Devuelve un objeto response tipo xls con un resumen de las compras asociadas a la planificacion.
    """

    plan_obj = get_object_or_404(Plan, pk=pk)
    nombre_archivo = 'planificacion_' + plan_obj.temporada.nombre + '_' + str(plan_obj.anio) + '.xlsx'
    
    # create a workbook in memory
    output = StringIO.StringIO()

    book = Workbook(output)
    sheet = book.add_worksheet('Planificacion')
    
    # Formato moneda
    fmoney = book.add_format({'num_format': '$#,##0'})
    # Formato numerico
    fnumeros = book.add_format({'num_format': '#,##0'})
    # Formato negrita
    fbold = book.add_format({'bold': True})

    # Ajustar el tamaño de la columna A (nombre de items)
    sheet.set_column(0, 0, 40)

    # Escribir la cabecera del archivo
    cabecera = ['Item', 'Unidades Temporada Vigente', 'Unidades Avance', 'Unidades Saldo', 'Unidades Totales', 'Costo Unitario', 'Costo Total']
    for ccol, ccol_data in enumerate(cabecera):
        sheet.write(0, ccol, ccol_data, fbold) 

    d_plan = plan_obj.resumen_plan_item()
    numero_filas = len(d_plan.keys())
    # Se itera sobre el diccionario de items y se crean las filas del archivo
    for fila, tupla in enumerate(d_plan.iteritems()):
        id, item = tupla
        sheet.write(fila+1, 0, item['nombre'])
        sheet.write(fila+1, 1, item['vta_u_vigente'], fnumeros)
        sheet.write(fila+1, 2, item['vta_u_avance'], fnumeros)
        sheet.write(fila+1, 3, item['vta_u_saldo'], fnumeros)
        sheet.write(fila+1, 4, item['vta_u_total'], fnumeros)
        sheet.write(fila+1, 5, item['costo_total'] / item['vta_u_total'], fmoney)
        sheet.write(fila+1, 6, item['costo_total'], fmoney)
    # Se construye la fila de totales
    sheet.write(numero_filas+1, 0, 'Total', fbold)
    sheet.write(numero_filas+1, 1, '=SUM(B2:B'+str(numero_filas+1)+')', fnumeros)
    sheet.write(numero_filas+1, 2, '=SUM(C2:C'+str(numero_filas+1)+')', fnumeros)
    sheet.write(numero_filas+1, 3, '=SUM(D2:D'+str(numero_filas+1)+')', fnumeros)
    sheet.write(numero_filas+1, 4, '=SUM(E2:E'+str(numero_filas+1)+')', fnumeros)
    sheet.write(numero_filas+1, 5, '=AVG(F2:F'+str(numero_filas+1)+')', fmoney)
    sheet.write(numero_filas+1, 6, '=SUM(G2:G'+str(numero_filas+1)+')', fmoney)
    book.close()

    # construct response
    output.seek(0)
    response = HttpResponse(output.read(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=" + nombre_archivo

    return response