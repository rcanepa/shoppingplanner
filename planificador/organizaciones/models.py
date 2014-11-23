from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

"""
Modelo Organizacion
"""

class Organizacion(models.Model):
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)
    usuario_creador = models.ForeignKey(User)

    def __unicode__(self):
        return self.nombre
