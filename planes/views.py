# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic import View, TemplateView, ListView, DetailView
from planes.models import Plan, Itemplan
from categorias.models import Categoria, Item
from forms import PlanForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy, reverse
from planificador.views import UserInfoMixin
from django.core import serializers
import json

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
    model = Plan
    template_name = "planes/plan_delete.html"
    success_url = reverse_lazy('planes:plan_list')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlanDeleteView, self).dispatch(*args, **kwargs)


class PlanTreeDetailView(UserInfoMixin, DetailView):
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
            categorias = Categoria.objects.exclude(categoria_padre=None)
            context['categorias'] = sorted(categorias, key= lambda t: t.get_nivel())
        return context

class GuardarProyeccionView(UserInfoMixin, View):

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('planes:plan_list'))

    def post(self, request, *args, **kwargs):
        if request.POST:
            data = json.loads(request.POST['proyeccion'])
            plan_obj = Plan.objects.get(pk=data['plan'])
            itemplan_obj = Itemplan.objects.get(pk=data['itemplan'])
            itemplan_obj.estado = 1
            itemplan_obj.save()
        return HttpResponseRedirect(reverse('planes:plan_proyecciones_detail', args=(plan_obj.id,)))

class BuscarItemplanListProyeccionView(View):
    
    
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


class BuscarItemplanProyeccionView(View):


    def get(self, request, *args, **kwargs):
        if request.GET:
            id_plan = request.GET['id_plan']
            id_itemplan = request.GET['id_itemplan']
            itemplan_obj = Itemplan.objects.filter(plan=id_plan,id=id_itemplan)
            data = serializers.serialize('json', itemplan_obj)
            return HttpResponse(data, mimetype='application/json')
        #return HttpResponseRedirect(reverse('planes:plan_list'))