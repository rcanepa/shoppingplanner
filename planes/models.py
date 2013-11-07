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
    nombre = models.CharField(max_length=70, unique=True)
    anio = models.PositiveSmallIntegerField(default=(datetime.now()).year + 1)
    temporada = models.ForeignKey(Temporada)
    usuario_creador = models.ForeignKey(User)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])

    def __unicode__(self):
        return str(self.anio) + " " + str(self.temporada)

    def get_absolute_url(self):
        return reverse('planes:plan_detail', kwargs={'pk': self.pk})


class Itemplan(models.Model):
    nombre = models.CharField(max_length=70)
    venta = models.FloatField(default=0)
    margen = models.FloatField(default=0)
    contribucion = models.FloatField(default=0)
    item = models.ForeignKey(Item)
    plan = models.ForeignKey(Plan)

    def __unicode__(self):
        return self.item.nombre
