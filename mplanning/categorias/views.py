from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.context_processors import csrf
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.views.generic import (View, CreateView, UpdateView, 
    ListView, DetailView, DeleteView)
from braces.views import LoginRequiredMixin, GroupRequiredMixin
from .models import Categoria, Item, Grupoitem
from .forms import CategoriaForm, ItemForm, ItemResponsableForm
from planes.models import Temporada
from planificador.views import UserInfoMixin
from ventas.models import Venta, Ventaperiodo

from collections import defaultdict
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
        return Categoria.objects.filter(categoria_padre=None,
            organizacion=self.request.user.get_profile().organizacion)

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
            id_cat = request.GET['key']
            item_obj = Item.vigente.get(pk=id_cat, 
                categoria__organizacion=self.request.user.get_profile().organizacion)
            items_obj = item_obj.get_children()
            for children in items_obj:
                nodo = {}
                if children.precio != 0:
                    nodo['title'] = children.nombre + " | " + "{:,}".format(children.precio)
                else:
                    nodo['title'] = children.nombre
                nodo['key'] = children.id
                if (children.get_children()):
                    nodo['folder'] = True
                    nodo['lazy'] = True
                if children.categoria.planificable:
                    nodo['extraClasses'] = "planificable"
                nodos.append(nodo)
            data = json.dumps(nodos,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')
        return HttpResponseRedirect(reverse('categorias:item_list'))


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
        context['ventas'] = Ventaperiodo.objects.values('anio').filter(item=item, tipo=0).annotate(vta_n=Sum('vta_n'), vta_u=Sum('vta_u')).order_by('-anio')
        ventas = Venta.objects.filter(item=item).order_by('anio','semana')
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
        if request.POST:
            solicitud = request.POST
            # Se busca la lista de objetos items que seran agrupados
            grupo_items = Item.objects.filter(pk__in=[int(x) for x in solicitud['grupo_items'].split(',')])
            # Se modifica su vigencia para que tome el valor False
            for item in grupo_items:
                item.vigencia = False
                item.save()
            # Se crea el nuevo item
            nuevo_item = Item(nombre=solicitud['nombre'].upper(), 
                precio=int(grupo_items[0].precio), 
                item_padre=grupo_items[0].item_padre, 
                categoria=grupo_items[0].categoria, 
                temporada=grupo_items[0].temporada)
            # Se guarda a la BD el nuevo item
            nuevo_item.save()
            print nuevo_item.id
            # Se verifica que el nuevo item haya sido creado (que exista su ID)
            if bool(nuevo_item.id):
                # Se crean los registros de Grupoitem para mantener la historia de la agrupacion
                # Se utiliza para hacer un rollback de la situacion
                grupo_item_list = list()
                grupo_item_list = [Grupoitem(item_nuevo=nuevo_item,item_agrupado=item) for item in grupo_items]
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
            data['msg'] = "El grupo ha sido creado exitosamente.";
            data['item_padre_id'] = nuevo_item.item_padre.id
            return HttpResponse(json.dumps(data), mimetype='application/json')