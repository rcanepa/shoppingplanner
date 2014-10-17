from django.db import models
from django.contrib.auth.models import User
from organizaciones.models import Organizacion


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    organizacion = models.ForeignKey(Organizacion)

    def __unicode__(self):
        return "%s's profile" % self.user

    def items_visibles(self, categoria):
        """
        Funcion que devuelve todos los items que un usuario debiese ver dada una categoria.
        Parametros: una categoria
        Devuelve: una lista de items
        """
        items_categoria_raiz = []
        # Se verifica que el usuario sea responsable de algun item
        item_list = self.user.items_responsable.all()
        if bool(item_list):
            # Se itera sobre la lista de items de los cuales es responsable el usuario
            for item in item_list:
                # Es necesario validar si la categoria a consultar es mayor, menor o igual que el item del
                # cual es responsable. La categoria a consultar es del mismo nivel que el item
                # del cual soy responsable -> no buscar
                if item.categoria.get_nivel() == categoria.get_nivel():
                    items_categoria_raiz.append(item)
                # La categoria a consultar es menor a la categoria del item del cual es responsable -> buscar hijos
                elif item.categoria.get_nivel() < categoria.get_nivel():
                    for hijo in item.get_hijos_controlado(categoria.get_nivel()):
                        if hijo.categoria == categoria:
                            items_categoria_raiz.append(hijo)
                # La categoria a consultar es mayor a la categoria del item del cual es responsable -> buscar padres
                else:
                    for padre in item.get_padres():
                        if padre.categoria == categoria:
                            items_categoria_raiz.append(padre)
        return items_categoria_raiz