# -*- coding: utf-8 -*-
from django.db import models
from datetime import datetime
from categorias.models import Item
from calendarios.models import Temporada
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class Plan(models.Model):
    ESTADOS = (
        (0, 'Nueva'),
        (1, 'Arbol de planificacion definido'),
        (2, 'Proyeccion completada'),
        (3, 'Plafinicacion finalizada'),
        )
    nombre = models.CharField(max_length=70)
    anio = models.PositiveSmallIntegerField(verbose_name="año", default=(datetime.now()).year + 1)
    temporada = models.ForeignKey(Temporada)
    usuario_creador = models.ForeignKey(User)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])

    def get_num_items(self):
        num_items = len(Itemplan.objects.filter(plan=self.id))
        return num_items

    def __unicode__(self):
        return str(self.anio) + " " + str(self.temporada)

    def get_absolute_url(self):
        return reverse('planes:plan_detail', kwargs={'pk': self.pk})


class Itemplan(models.Model):
    ESTADOS = (
        (0, 'Sin Proyección'),
        (1, 'Proyectado'),
        )
    nombre = models.CharField(max_length=70)
    venta = models.FloatField(default=0)
    margen = models.FloatField(default=0)
    contribucion = models.FloatField(default=0)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    item = models.ForeignKey(Item)
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
