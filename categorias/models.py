from django.db import models
from datetime import datetime, date, time
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

"""
Modelo Categoria
"""

class Categoria(models.Model):
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)
    categoria_padre = models.ForeignKey('self', blank=True, null=True, related_name='categorias_hijos')
    usuario_creador = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('categorias:categoria_detail', kwargs={'pk': self.pk})

    def as_tree(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.categorias_hijos.all())
        branch = bool(children)
        yield branch, self
        for child in children:
            for next in child.as_tree():
                yield next
        yield branch, None

    def as_tree_min(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.categorias_hijos.all())
        branch = bool(children)
        yield branch, self
        for child in children:
            for next in child.as_tree():
                yield next
        yield branch, None
    
    def get_nivel(self, nivel=1):
        """
        Devuelve el nivel en la estructural de arbol a la que pertenece
        """
        hijo = self.categoria_padre
        while hijo != None:
            nivel += 1
            hijo = hijo.categoria_padre
        return nivel

    get_nivel.short_description = 'Nivel'
    get_nivel.admin_order_field = 'id'

"""
Modelo Item
"""

class Item(models.Model):
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    usuario_creador = models.ForeignKey(User, related_name='items_creados')
    usuario_responsable = models.ForeignKey(User, blank=True, null=True, related_name='items_responsable')
    categoria = models.ForeignKey('Categoria')
    precio = models.PositiveIntegerField(default=0)
    
    def __unicode__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('categorias:item_detail', kwargs={'pk': self.pk})

    def as_tree(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.items_hijos.all())
        branch = bool(children)
        yield branch, self
        for child in children:
            for next in child.as_tree():
                yield next
        yield branch, None

    def as_tree_min(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.items_hijos.all())
        branch = bool(children)
        yield branch, self
        for child in children:
            if child.get_nivel() < 4:
                for next in child.as_tree_min():
                    yield next
            else:
                yield child
        yield branch, None

    def get_nivel(self, nivel=1):
        hijo = self.item_padre
        while hijo != None:
            nivel += 1
            hijo = hijo.item_padre
        return nivel

    get_nivel.short_description = 'Nivel'
    get_nivel.admin_order_field = 'id'

    def get_precio_promedio(self):
        return self.precio