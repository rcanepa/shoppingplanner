from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from datetime import datetime, date, time
from organizaciones.models import Organizacion


"""
Modelo Categoria
"""

class Categoria(models.Model):
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)
    categoria_padre = models.ForeignKey('self', blank=True, null=True, related_name='categorias_hijos')
    organizacion = models.ForeignKey(Organizacion)
    planificable = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('categorias:categoria_detail', kwargs={'pk': self.pk})

    def get_children(self):
        return self.categorias_hijos.all().order_by('nombre')

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
    id_real = models.IntegerField(blank=True, null=True)
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    usuario_responsable = models.ForeignKey(User, blank=True, null=True, related_name='items_responsable')
    categoria = models.ForeignKey('Categoria')
    temporada = models.ForeignKey('planes.Temporada', blank=True, null=True, related_name='items_temporada')
    precio = models.PositiveIntegerField(default=0)
    
    def __unicode__(self):
        return self.nombre

    def get_children(self):
        return self.items_hijos.all().order_by('nombre','precio')

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

    def get_hijos(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.items_hijos.all())
        #branch = bool(children)
        # Se revisa si el item pertenece a la categoria sin hijos (articulos),
        # en ese caso, se devuelve el nodo
        if bool(self.categoria.get_children()) == False:
            yield self
        for child in children:
            for next in child.get_hijos():
                yield next

    def get_hijos_controlado(self, nivel=1):
        """
        Generador que itera recursivamente sobre los hijos de un item. Esta acotado por un parametro
        nivel el cual permite especificar hasta que profundidad del arbol se buscaran hijos.
        Parametro: nivel de profundidad
        """
        children = list(self.items_hijos.all())        
        yield self
        for child in children:
            if child.get_nivel() <= nivel:
                for next in child.get_hijos_controlado(nivel):
                    yield next

    def get_padres(self):
        """
        Devuelve el padre de un item
        """
        padre = self.item_padre
        while padre is not None:
            yield padre
            padre = padre.item_padre

    def es_padre(self, item):
        """
        Comprueba si el item pasado como parametro es padre de self
        """
        # Se comprueba primero que la categoria del item sea menor que la de self,
        # ya que en caso contrario jamas sera padre
        padre = self.item_padre
        while item.categoria.get_nivel() <= padre.categoria.get_nivel():
            if item == padre:
                return True
            else:
                padre = padre.item_padre
        else:
            return False


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