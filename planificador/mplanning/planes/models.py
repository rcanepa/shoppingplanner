# -*- coding: utf-8 -*-
from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from categorias.models import Item
from organizaciones.models import Organizacion
from calendarios.models import Periodo, Tiempo
from django.db.models import Q
from django.db.models import Max, Min


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
        anio_pre = anio - 1
        anio_post = anio + 1
        data = []
        # Se buscan todos los periodos asociados a la temporada
        periodos = self.periodo.all()
        # Se obtiene el periodo inferior
        periodo_inf = periodos[0]
        # Se obtiene el periodo superior
        periodo_sup = periodos[periodos.count()-1]
        # Se obtiene el periodo superior + X periodos
        periodo_sup_vta = Tiempo.objects.filter(Q(anio=anio,periodo__nombre__gt=periodo_sup.nombre) | Q(anio=anio_post,periodo__nombre__lt=periodo_inf.nombre)).values('periodo__nombre').annotate(anio=Max('anio'),semana=Max('semana')).order_by('anio','semana')[2]
        # Se obtiene el periodo inferior - X periodos
        periodos_inf_vta = Tiempo.objects.filter(Q(anio=anio,periodo__nombre__lt=periodo_inf.nombre) | Q(anio=anio_pre,periodo__nombre__gt=periodo_inf.nombre)).values('periodo__nombre').annotate(anio=Max('anio'),semana=Min('semana')).order_by('-anio','-semana')[2]
        data.append(periodos_inf_vta)
        data.append(periodo_sup_vta)
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
    plan = models.ForeignKey(Plan)

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


class Itemplandet(models.Model):
    """
    Clase encapsula el detalle por periodo de cada item que pertenece a la planificacion. Se gestionan
    en la seccion de planificacion (paso posterior a la proyeccion)
    """
    periodo = models.ForeignKey(Periodo)
    itemplan = models.ForeignKey(Itemplan, related_name='item_planificacion')
    vta_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta neta", default=0, blank=True, null=True)
    ctb_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="contribución neta", default=0, blank=True, null=True)
    dcto = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="descuento", default=0, blank=True, null=True)
    costo_u = models.DecimalField(max_digits=15, decimal_places=3, default=0, blank=True, null=True)
    vta_u = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta en unidades", default=0, blank=True, null=True)
    margen = models.DecimalField(max_digits=15, decimal_places=3, default=0, blank=True, null=True)

    def __unicode__(self):
        return self.itemplan.item.nombre