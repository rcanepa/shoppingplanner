from django.shortcuts import render_to_response
from categorias.models import Categoria, Item
from ventas.models import Venta
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from forms import CategoriaForm, ItemForm
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import DeleteView
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from planificador.views import UserInfoMixin
from collections import defaultdict

class CategoriaListView(UserInfoMixin, ListView):
    context_object_name = "categorias"
    template_name = "categorias/categoria_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CategoriaListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Categoria.objects.filter(categoria_padre=None)

    def get_context_data(self, **kwargs):
        context = super(CategoriaListView, self).get_context_data(**kwargs)
        return context

class CategoriaDetailView(UserInfoMixin, DetailView):
    model = Categoria
    template_name = "categorias/categoria_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CategoriaDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CategoriaDetailView, self).get_context_data(**kwargs)
        return context


class CategoriaUpdateView(UserInfoMixin, UpdateView):
    model = Categoria
    template_name = "categorias/categoria_update.html"
    form_class = CategoriaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(CategoriaUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CategoriaUpdateView, self).get_context_data(**kwargs)
        return context


class CategoriaCreateView(UserInfoMixin, CreateView):
    def __init__(self):
        super(CategoriaCreateView, self).__init__()

    model = Categoria
    template_name = "categorias/categoria_create.html"
    form_class = CategoriaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(CategoriaCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        return super(CategoriaCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CategoriaCreateView, self).get_context_data(**kwargs)
        return context


class CategoriaDeleteView(UserInfoMixin, DeleteView):
    model = Categoria
    template_name = "categorias/categoria_delete.html"
    success_url = reverse_lazy('categorias:categoria_list')

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(CategoriaDeleteView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CategoriaDeleteView, self).get_context_data(**kwargs)
        return context

"""
########################### Items ###########################
"""


class ItemListView(UserInfoMixin, ListView):
    context_object_name = "items"
    template_name = "categorias/item_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ItemListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Item.objects.filter(usuario_responsable=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        return context


class ItemDetailView(UserInfoMixin, DetailView):
    model = Item
    template_name = "categorias/item_detail.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ItemDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ItemDetailView, self).get_context_data(**kwargs)
        item = self.get_object()
        context['ventas'] = Venta.objects.values('anio').filter(item=item).annotate(vta_n=Sum('vta_n'), vta_u=Sum('vta_u')).order_by('-anio')
        
        ventas = Venta.objects.filter(item=item).order_by('anio','semana')
        summary = defaultdict( int )
        
        for venta in ventas:
            summary[venta.anio, venta.semana] = venta.vta_n, venta.vta_u
        
        context['summary'] = dict(summary)
        return context


class ItemUpdateView(UserInfoMixin, UpdateView):
    model = Item
    template_name = "categorias/item_update.html"
    form_class = ItemForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(ItemUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ItemUpdateView, self).get_context_data(**kwargs)
        return context


class ItemCreateView(UserInfoMixin, CreateView):
    model = Item
    template_name = "categorias/item_create.html"
    form_class = ItemForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(ItemCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.usuario_creador = self.request.user
        return super(ItemCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ItemCreateView, self).get_context_data(**kwargs)
        return context


class ItemDeleteView(UserInfoMixin, DeleteView):
    model = Item
    template_name = "categorias/item_delete.html"
    success_url = reverse_lazy('categorias:item_list')

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(ItemDeleteView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ItemDeleteView, self).get_context_data(**kwargs)
        return context
