from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from categorias.models import Categoria, Item
from ventas.models import Venta, Ventaperiodo
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from forms import CategoriaForm, ItemForm, ItemResponsableForm
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import DeleteView
from django.views.generic import View
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from planificador.views import UserInfoMixin
from collections import defaultdict
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder


"""
Sobreescribir el metodo unicode del modelo User para que muestre
el nombre completo y no solo el username.
"""
def user_unicode_patch(self):
    return '%s %s (%s)' % (self.first_name, self.last_name, self.username)

User.__unicode__ = user_unicode_patch


class CategoriaListView(UserInfoMixin, ListView):
    context_object_name = "categorias"
    template_name = "categorias/categoria_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CategoriaListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Categoria.objects.filter(categoria_padre=None,
            organizacion=self.request.user.get_profile().organizacion)

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
    model = Categoria
    template_name = "categorias/categoria_create.html"
    form_class = CategoriaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(CategoriaCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
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


class ItemAjaxNodeView(View):
    '''
    Recibe el ID de un item y entrega una lista de nodos hijos
    los cuales seran agregados a un FancyTree
    '''
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        if request.GET:
            nodos = []
            id_cat = request.GET['key']
            item_obj = Item.objects.get(pk=id_cat, 
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
            data = simplejson.dumps(nodos,cls=DjangoJSONEncoder)
            return HttpResponse(data, mimetype='application/json')
        return HttpResponseRedirect(reverse('categorias:item_list'))


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
        context['ventas'] = Ventaperiodo.objects.values('anio').filter(item=item, tipo=0).annotate(vta_n=Sum('vta_n'), vta_u=Sum('vta_u')).order_by('-anio')
        ventas = Venta.objects.filter(item=item).order_by('anio','semana')

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


class ItemResponsablesView(UserInfoMixin, ListView):
    context_object_name = "items"
    template_name = "categorias/item_responsables.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ItemResponsablesView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Item.objects.filter(usuario_responsable=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(ItemResponsablesView, self).get_context_data(**kwargs)
        return context

class ItemResponsableUpdateView(UserInfoMixin, UpdateView):
    model = Item
    template_name = "categorias/item_responsable_update.html"
    form_class = ItemResponsableForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(ItemResponsableUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ItemResponsableUpdateView, self).get_context_data(**kwargs)
        return context