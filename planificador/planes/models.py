# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum, Max, Min, Avg

from datetime import datetime

from calendarios.models import Periodo, Tiempo
from categorias.models import Item
from organizaciones.models import Organizacion
from ventas.models import Ventaperiodo


class Temporada(models.Model):
    nombre = models.CharField(max_length=50)
    planificable = models.BooleanField(default=True)
    organizacion = models.ForeignKey(Organizacion)
    periodo = models.ManyToManyField(Periodo)
    periodo_final = models.ForeignKey(Periodo, related_name="+", help_text="Seleccione el último periodo de la temporada.")

    def __unicode__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('planes:temporada_detail', kwargs={'pk': self.pk})

    def periodos_proyeccion(self, anio, periodos=3):
        """
        Recibe como parametro la cantidad de periodos por sobre y bajo los periodos de una
        temporada que se quieren encontrar. Devuelve el periodo que esta bajo X periodos del periodo
        inferior de una temporada y el periodo superior por X periodos del periodo superior de una temporada
        """
        anio_pre = anio - 2
        anio_post = anio
        data = []
        # Se buscan todos los periodos asociados a la temporada
        periodos = self.periodo.all()
        # Se obtiene el periodo inferior
        periodo_inf = periodos[0]
        # Se obtiene el periodo superior
        periodo_sup = periodos[periodos.count()-1]
        # Se obtiene el periodo superior + X periodos
        periodos_sup_vta = Tiempo.objects.filter(Q(anio=anio-1,periodo__nombre__gt=periodo_sup.nombre) | Q(anio=anio_post,periodo__nombre__lt=periodo_inf.nombre)).values('periodo__nombre').annotate(anio=Max('anio'),semana=Max('semana')).order_by('anio','semana')[2]
        # Se obtiene el periodo inferior - X periodos
        periodos_inf_vta = Tiempo.objects.filter(Q(anio=anio-1,periodo__nombre__lt=periodo_inf.nombre) | Q(anio=anio_pre,periodo__nombre__gt=periodo_inf.nombre)).values('periodo__nombre').annotate(anio=Max('anio'),semana=Min('semana')).order_by('-anio','-semana')[2]
        data.append(periodos_inf_vta)
        data.append(periodos_sup_vta)
        return data

    def comprobar_periodo(self, periodo):
        """
        Devuelve True si el periodo pertenece a la lista de periodos de la temporada y False
        en caso contrario
        """
        # Se revisa si el valor de periodo es un string
        if (isinstance(periodo, basestring)):
            return bool(self.periodo.filter(nombre=periodo))
        # En caso contrario se entrega el nombre del objeto periodo
        else:
            return bool(self.periodo.filter(nombre=periodo.nombre))


class Plan(models.Model):
    ESTADOS = (
        (0, 'Nueva'),
        (1, 'Arbol de planificacion definido'),
        (2, 'Proyeccion finalizada'),
        (3, 'Plafinicacion finalizada'),
        )
    nombre = models.CharField(max_length=70)
    anio = models.PositiveSmallIntegerField(verbose_name="año", default=(datetime.now()).year + 1)
    temporada = models.ForeignKey(Temporada)
    usuario_creador = models.ForeignKey(User)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])

    def get_num_items_planificables(self):
        num_items = Itemplan.objects.filter(plan=self.id, planificable=True).count()
        return num_items

    def resumen_estadisticas(self, temporada=None, item=None):
        """
        Obtiene la venta asociada a todos los items de una planificacion entre los
        ultimos 3 años.
        """
        # Contiene la lista de items que seran consultados para buscar las ventas
        item_arr_definitivo = []
        # Año actual (por planificar)
        act_anio = self.anio
        # Año actual - 3 (limite inferior)
        ant_anio = self.anio - 3
        if item == None:
            # Arreglo de items con todos los items de la planificacion
            item_arr_definitivo = [itemplan.item for itemplan in self.item_planificados.all() if itemplan.item.categoria.planificable == True]
        else:
            # Arreglo de items con todos los items hijos del item entregado como parametro
            item_arr_definitivo = [x for x in item.get_hijos() if x.categoria.planificable == True]
        # Se define la temporada sobre la cual se calcularan las ventas
        if temporada == None:
            temporada = self.temporada
            estadisticas = Ventaperiodo.objects.filter(
            item__in=item_arr_definitivo,
            anio__gte=ant_anio,
            anio__lte=act_anio,
            temporada=temporada).values(
            'anio').annotate(
            vta_n=Sum('vta_n'),
            vta_u=Sum('vta_u'),
            ctb_n=Sum('ctb_n'),
            costo=Sum('costo'),
            precio_prom=Avg('item__precio')).order_by(
            'anio')
        elif temporada == "TT":
            estadisticas = Ventaperiodo.objects.filter(
            item__in=item_arr_definitivo,
            anio__gte=ant_anio,
            anio__lte=act_anio).values(
            'anio').annotate(
            vta_n=Sum('vta_n'),
            vta_u=Sum('vta_u'),
            ctb_n=Sum('ctb_n'),
            costo=Sum('costo'),
            precio_prom=Avg('item__precio')).order_by(
            'anio')
        else:
            estadisticas = Ventaperiodo.objects.filter(
            item__in=item_arr_definitivo,
            anio__gte=ant_anio,
            anio__lte=act_anio,
            temporada=temporada).values(
            'anio').annotate(
            vta_n=Sum('vta_n'),
            vta_u=Sum('vta_u'),
            ctb_n=Sum('ctb_n'),
            costo=Sum('costo'),
            precio_prom=Avg('item__precio')).order_by(
            'anio')
        return estadisticas

    def __unicode__(self):
        return str(self.anio) + " " + str(self.temporada)

    def get_absolute_url(self):
        return reverse('planes:plan_detail', kwargs={'pk': self.pk})


class Itemplan(models.Model):
    ESTADOS = (
        (0, 'Pendiente'),
        (1, 'Proyectado'),
        (2, 'Planificado'),
        )
    nombre = models.CharField(max_length=70)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])
    planificable = models.BooleanField(default=False)
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    item = models.ForeignKey(Item, related_name='item_proyectados')
    plan = models.ForeignKey(Plan, related_name='item_planificados')

    def as_tree(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.items_hijos.all())
        print bool(children)
        branch = bool(children)
        yield branch, self
        for child in children:
            for next in child.as_tree():
                yield next
        yield branch, None

    def __unicode__(self):
        return self.item.nombre