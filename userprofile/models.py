from django.db import models
from django.contrib.auth.models import User
from organizaciones.models import Organizacion

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    organizacion = models.ForeignKey(Organizacion)
    
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])