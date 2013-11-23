from django.db import models
from django.contrib.auth.models import User
from organizaciones.models import Organizacion

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    organizacion = models.ForeignKey(Organizacion)

    def __unicode__(self):
    	return "%s's profile" % self.user   