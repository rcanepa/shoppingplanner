# -*- coding: utf-8 -*-
from django.db import models
from organizaciones.models import Organizacion


class Calendario(models.Model):
    """docstring for Calendario"""
    nombre = models.CharField(max_length=20)
    organizacion = models.ForeignKey(Organizacion)

    def __unicode__(self):
        return self.nombre


class Periodo(models.Model):
    """docstring for Periodo"""
    nombre = models.CharField(max_length=20)
    calendario = models.ForeignKey(Calendario)
    #orden = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']


class Tiempo(models.Model):
    """docstring for ClassName"""
    
    codigo = models.CharField(max_length=6)
    anio = models.PositiveSmallIntegerField(verbose_name="año")
    semana = models.PositiveSmallIntegerField()
    periodo = models.ManyToManyField(Periodo)

    def __unicode__(self):
        return str(self.anio) + "-" + str(self.semana)