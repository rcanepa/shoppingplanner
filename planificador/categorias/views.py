# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.db.models import Sum
from django.http import HttpResponse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View
from braces.views import LoginRequiredMixin
from braces.views import GroupRequiredMixin
from .models import Categoria, Item, Grupoitem
from .forms import CategoriaForm, ItemForm, ItemResponsableForm
from planes.models import Itemplan
from planes.models import Plan
from planificador.views import UserInfoMixin
from ventas.models import Ventaperiodo
import json

"""
Sobreescribir el metodo unicode del modelo User para que muestre
el nombre completo y no solo el username.
"""


def user_unicode_patch(self):
    return '%s %s (%s)' % (self.first_name, self.last_name, self.username)

User.__unicode__ = user_unicode_patch


class CategoriaListView(LoginRequiredMixin, UserInfoMixin, ListView):
    context_object_name = "categorias"
    template_name = "categorias/categoria_list.html"

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Categoria.objects.filter(categoria_padre=None, organizacion=self.request.user.get_profile().organizacion)

    def get_context_data(self, **kwargs):
        context = super(CategoriaListView, self).get_context_data(**kwargs)
        return context


class CategoriaDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    model = Categoria
    template_name = "categorias/categoria_detail.html"

    def get_context_data(self, **kwargs):
        context = super(CategoriaDetailView, self).get_context_data(**kwargs)
        return context


class CategoriaUpdateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, UpdateView):
    model = Categoria
    template_name = "categorias/categoria_update.html"
    form_class = CategoriaForm
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(CategoriaUpdateView, self).get_context_data(**kwargs)
        return context


class CategoriaCreateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, CreateView):
    model = Categoria
    template_name = "categorias/categoria_create.html"
    form_class = CategoriaForm
    group_required = u'Administrador'

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
        return super(CategoriaCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CategoriaCreateView, self).get_context_data(**kwargs)
        return context


class CategoriaDeleteView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, DeleteView):
    model = Categoria
    template_name = "categorias/categoria_delete.html"
    success_url = reverse_lazy('categorias:categoria_list')
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(CategoriaDeleteView, self).get_context_data(**kwargs)
        return context

"""
########################### Items ###########################
"""


class ItemAjaxNodeView(LoginRequiredMixin, View):
    '''
    Recibe el ID de un item y entrega una lista de nodos hijos
    los cuales seran agregados a un FancyTree
    '''
    def get(self, request, *args, **kwargs):
        if request.GET:
            nodos = []
            id_item_seleccionado = request.GET['key']
            id_plan = request.GET['plan']
            item_obj = Item.vigente.get(pk=id_item_seleccionado, categoria__organizacion=self.request.user.get_profile().organizacion)
            plan_obj = Plan.objects.get(pk=id_plan)
            items_obj = item_obj.get_children()
            for children in items_obj:
                nodo = {}
                data = {}
                if children.categoria.planificable:
                    # Se busca si existe un itemplan asociado al item. La idea es verificar si el item fue planificado o no.
                    try:
                        itemplan_obj = Itemplan.objects.get(item=children, plan=plan_obj)
                        data['estado'] = itemplan_obj.estado
                    except ObjectDoesNotExist:
                        data['estado'] = 0
                if children.categoria.venta_arbol:
                    venta_temporada_anual = children.get_venta_temporada(plan_obj.anio-1, plan_obj.temporada)
                else:
                    venta_temporada_anual = [0, 0, 0]
                nodo['title'] = children.nombre
                data['precio'] = str(children.precio)
                data['venta_t'] = venta_temporada_anual[2]
                data['venta_t1'] = venta_temporada_anual[1]
                data['venta_t2'] = venta_temporada_anual[0]
                nodo['key'] = children.id
                nodo['data'] = data
                if (children.get_children()):
                    nodo['folder'] = True
                    nodo['lazy'] = True
                if children.categoria.planificable:
                    nodo['extraClasses'] = "planificable"
                nodos.append(nodo)
            data = json.dumps(nodos, cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')


class ItemListView(LoginRequiredMixin, UserInfoMixin, ListView):
    context_object_name = "items"
    template_name = "categorias/item_list.html"

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Item.vigente.filter(usuario_responsable=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        return context


class ItemDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    model = Item
    template_name = "categorias/item_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        item = self.get_object()
        context['ventas'] = Ventaperiodo.objects.values('anio').filter(item=item, tipo=0).annotate(
            vta_n=Sum('vta_n'), vta_u=Sum('vta_u')).order_by('-anio')
        return context


class ItemUpdateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, UpdateView):
    model = Item
    template_name = "categorias/item_update.html"
    form_class = ItemForm
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(ItemUpdateView, self).get_context_data(**kwargs)
        return context


class ItemCreateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, CreateView):
    model = Item
    template_name = "categorias/item_create.html"
    form_class = ItemForm
    group_required = u'Administrador'

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        return super(ItemCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ItemCreateView, self).get_context_data(**kwargs)
        return context


class ItemDeleteView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, DeleteView):
    model = Item
    template_name = "categorias/item_delete.html"
    success_url = reverse_lazy('categorias:item_list')
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(ItemDeleteView, self).get_context_data(**kwargs)
        return context


class ItemResponsablesView(LoginRequiredMixin, UserInfoMixin, ListView):
    context_object_name = "items"
    template_name = "categorias/item_responsables.html"

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Item.vigente.filter(usuario_responsable=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ItemResponsablesView, self).get_context_data(**kwargs)
        return context


class ItemResponsableUpdateView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, UpdateView):
    model = Item
    template_name = "categorias/item_responsable_update.html"
    form_class = ItemResponsableForm
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(ItemResponsableUpdateView, self).get_context_data(**kwargs)
        return context


class GrupoitemCreateAJAXView(LoginRequiredMixin, View):
    '''
    Recibe como parametros una lista de IDs de items y los datos basicos para la creacion del nuevo item.
    Crea tantos objetos Grupoitem como objetos Item esten siendo agrupados.

    El request tiene los siguientes atributos:
        solicitud['temporada']: ID de la temporada escogida
        solicitud['nombre']: nombre del nuevo item
        solicitud['precio']: precio del nuevo item
        solicitud['grupo_items']: string con una lista de ID separados con "," con todos los items agrupados
    '''

    def post(self, request, *args, **kwargs):
        """
        Flujo del proceso:
            1.- Se marcan los items agrupados como NO vigentes (vigencia=False)
            2.- Se crea y almacena el nuevo item utilizando las caracteristicas de los items agrupados
            3.- Se crean los registros grupoitem que mantienen la relacion entre los items agrupados y el nuevo item 
            4.- Se crean los registros de ventaperiodo asociados al nuevo item. Basicamente se copia la informacion de ventaperiodo
                de los items agrupados y se imputan al nuevo item. No se borra informacion de ventaperiodo de los items agrupados
            5.- Se eliminan todos los itemplan que puedan existir asociados a los items agrupados y se crea uno nuevo para el nuevo item (agrupado)
        """
        if request.POST:
            solicitud = request.POST

            # Se busca la lista de objetos items que seran agrupados y se marcan como NO vigentes
            grupo_items = Item.objects.filter(pk__in=[int(x) for x in solicitud['grupo_items'].split(',')])
            # Se actualiza la vigencia de los items agrupados a False
            for item in grupo_items:
                item.vigencia = False
                item.save()
            # Se crea el nuevo item
            nuevo_item = Item(nombre=solicitud['nombre'].upper(), precio=int(grupo_items[0].precio), 
                item_padre=grupo_items[0].item_padre, categoria=grupo_items[0].categoria,
                temporada=grupo_items[0].temporada)
            # Se guarda a la BD el nuevo item
            nuevo_item.save()
            # Se verifica que el nuevo item haya sido creado (que exista su ID)
            if bool(nuevo_item.id):
                # Se crean los registros de Grupoitem para mantener la historia de la agrupacion
                # Se utiliza para hacer un rollback de la situacion
                grupo_item_list = list()
                grupo_item_list = [Grupoitem(item_nuevo=nuevo_item, item_agrupado=item) for item in grupo_items]
                Grupoitem.objects.bulk_create(grupo_item_list)
                # Se buscan todas las ventas asociadas a los items agrupados
                venta_items = Ventaperiodo.objects.filter(item__in=grupo_items)
                # Se crear nuevas ventas asociadas al nuevo item creado
                venta_items_list = list()
                for venta in venta_items:
                    venta.pk = None
                    venta.item = nuevo_item
                    venta_items_list.append(venta)
                Ventaperiodo.objects.bulk_create(venta_items_list)

            data = {}
            data['msg'] = "El grupo ha sido creado exitosamente."
            data['item_padre_id'] = nuevo_item.item_padre.id
            return HttpResponse(json.dumps(data), mimetype='application/json')


class ItemCreateAjaxView(LoginRequiredMixin, View):
    """
    Crea un nuevo objeto Item a partir de un nodo item_padre
    del arbol de seleccion. Recibe como parametro el ID del item padre,
    nombre y precio del nuevo Item.
    """
    def post(self, request, *args, **kwargs):
        data = {}
        id_item_padre = request.POST['item_padre_id']
        nombre_nuevo_item = request.POST['nombre']
        precio_nuevo_item = request.POST['precio']
        try:
            item_padre = Item.objects.get(id=id_item_padre)
        except ObjectDoesNotExist:
            data['msg'] = "El item NO pudo ser creado, por favor intentelo nuevamente."
            return HttpResponse(json.dumps(data), mimetype='application/json')
        nuevo_item = Item(
            nombre=nombre_nuevo_item, item_padre=item_padre,
            categoria=item_padre.categoria.get_children()[0], temporada=item_padre.temporada, precio=precio_nuevo_item)
        nuevo_item.save()
        data['msg'] = "El item ha sido creado exitosamente."
        data['id_item_padre'] = id_item_padre
        return HttpResponse(json.dumps(data), mimetype='application/json')


class ItemQuitarVigenciaView(LoginRequiredMixin, View):
    """
    Quita la vigencia a un item, y por lo tanto, ya no aparece
    en el árbol de planificación.
    """
    def post(self, request, *args, **kwargs):
        data = {}
        id_item = request.POST['item_id']
        try:
            item = Item.objects.get(id=id_item)
        except ObjectDoesNotExist:
            data['msg'] = "El item NO pudo ser actualizado, por favor intentelo nuevamente."
            data['tipo_msg'] = "msg_error"
            return HttpResponse(json.dumps(data), mimetype='application/json')
        # Se quita la vigencia al item y a sus posibles hijos.
        for i in item.hijos_recursivos():
            i.vigencia = False
            i.save()
        data['msg'] = "El item ha sido removido exitosamente."
        data['tipo_msg'] = "msg_success"
        data['id_item'] = item.id
        return HttpResponse(json.dumps(data), mimetype='application/json')
