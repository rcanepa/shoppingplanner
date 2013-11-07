from django.db import models
from organizaciones.models import Organizacion

class Temporada(models.Model):
	nombre = models.CharField(max_length=50)
                                      
	def __unicode__(self):
		return self.nombre

"""
A esta clase se le debe vincular con una nueva clase
Calendario, la cual contendra un campo de nombre y otro
asociado a una organizacion
"""
class Periodo(models.Model):
	MESES = (
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
    (8, '8'),
    (9, '9'),
    (10, '10'),
    (11, '11'),
    (12, '12'),
	)
	periodo = models.CharField(max_length=10)
	mes = models.PositiveSmallIntegerField(choices=MESES)
	temporada = models.ForeignKey(Temporada, related_name='periodos')
	def __unicode__(self):
		return self.periodo  