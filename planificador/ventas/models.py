# -*- coding: utf-8 -*-
from django.db import models
from categorias.models import Item
from calendarios.models import Tiempo, Periodo
from organizaciones.models import Organizacion
from django.core.urlresolvers import reverse
from datetime import datetime, date, time


class Venta(models.Model):
	item = models.ForeignKey(Item)
	tiempo = models.ForeignKey(Tiempo)
	vta_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta neta", default=0, blank=True, null=True)
	ctb_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="contribución neta", default=0, blank=True, null=True)
	costo = models.DecimalField(max_digits=15, decimal_places=3, default=0, blank=True, null=True)
	vta_u = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta en unidades", default=0, blank=True, null=True)
	stk_u = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="unidades en stock", default=0, blank=True, null=True)
	stk_v = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="costo del stock", default=0, blank=True, null=True)

	def __unicode__(self):
		return self.item.nombre


class Ventaperiodo(models.Model):
	item = models.ForeignKey(Item)
	periodo = models.CharField(max_length=20)
	anio = models.PositiveSmallIntegerField(verbose_name="año")
	"""
	Tipos:
		0: real
		1: proyectada (no real)
		2: planificada (no real)
	"""
	tipo = models.PositiveSmallIntegerField(default=0)
	temporada = models.ForeignKey('planes.Temporada')
	vta_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta neta", default=0, blank=True, null=True)
	ctb_n = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="contribución neta", default=0, blank=True, null=True)
	costo = models.DecimalField(max_digits=15, decimal_places=3, default=0, blank=True, null=True)
	vta_u = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="venta en unidades", default=0, blank=True, null=True)
	stk_u = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="unidades en stock", default=0, blank=True, null=True)
	stk_v = models.DecimalField(max_digits=15, decimal_places=3, verbose_name="costo del stock", default=0, blank=True, null=True)
	margen = models.DecimalField(max_digits=15, decimal_places=3, default=0, blank=True, null=True)

	def __unicode__(self):
		return self.item.nombre + " " + str(self.anio) + " " + self.periodo


class Controlventa(models.Model):
	anio = models.PositiveSmallIntegerField(verbose_name="año")
	periodo = models.ForeignKey(Periodo)
	organizacion = models.ForeignKey(Organizacion)
	fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)

	def __unicode__(self):
		return str(self.anio) + " " + self.periodo.nombre
	
	def get_absolute_url(self):
		return reverse('ventas:controlventa_detail', kwargs={'pk': self.pk})