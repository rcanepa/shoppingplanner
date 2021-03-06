# -*- coding: utf-8 -*-
from datetime import datetime
from django import db
from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from organizaciones.models import Organizacion
from ventas.models import Ventaperiodo


class Categoria(models.Model):
    """
    Modelo Categoria
    """
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)
    categoria_padre = models.ForeignKey('self', blank=True, null=True, related_name='categorias_hijos')
    organizacion = models.ForeignKey(Organizacion)
    # Determina si el usuario puede planificar sobre un item que pertenece a esta categoria.
    planificable = models.BooleanField(default=False)
    # Determina si en el arbol de planificacion se mostrara la venta de itemes pertenecientes a esta categoria.
    venta_arbol = models.BooleanField(default=False, verbose_name=u'Venta en arbol')
    # Se utiliza para marcar una Categoria sobre la cual se pueden generar resumenes y busquedas independiente
    # de la estructura jerarquica a la que pertenece. Por ejemplo, para generar un resumen a nivel de Marca,
    # sin considerar al departamento al que pertenece.
    jerarquia_independiente = models.BooleanField(default=False)

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
        while hijo is not None:
            nivel += 1
            hijo = hijo.categoria_padre
        return nivel

    def hijos_recursivos(self):
        """
        Itera sobre los hijos del item. Se devuelve a si mismo inicialmente.
        """
        children = list(self.get_children())
        yield self
        for child in children:
            for next in child.hijos_recursivos():
                yield next

    def get_distancia_hojas(self):
        nivel_self = self.get_nivel()
        for categoria_hija in self.hijos_recursivos():
            nivel_hoja = categoria_hija.get_nivel()
        return nivel_hoja - nivel_self

    get_nivel.short_description = 'Nivel'
    get_nivel.admin_order_field = 'id'


class ItemQueryset(models.query.QuerySet):
    def responsable(self, usuario):
        return self.filter(usuario_responsable=usuario)

    def vigente(self):
        return self.filter(vigencia=True)


class ItemManager(models.Manager):
    """
    Managers para la clase Item.
    """
    def get_query_set(self):
        return ItemQueryset(self.model, using=self._db)

    def responsable(self, usuario):
        """
        Devuelve los Item en donde el parametro usuario == usuario_responsable
        """
        return self.get_query_set().responsable(usuario)

    def vigente(self):
        """
        Devuelve los Item en donde el campo vigente == True
        """
        return self.get_query_set().vigente()


class Item(models.Model):
    id_real = models.IntegerField(blank=True, null=True)
    nombre = models.CharField(max_length=70)
    vigencia = models.BooleanField(default=True)
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    usuario_responsable = models.ForeignKey(User, blank=True, null=True, related_name='items_responsable')
    categoria = models.ForeignKey('Categoria')
    temporada = models.ForeignKey('planes.Temporada', blank=True, null=True, related_name='items_temporada')
    precio = models.PositiveIntegerField(default=0)

    objects = ItemManager()

    def __unicode__(self):
        return self.nombre

    def get_children(self):
        """
        Devuelve la lista de items hijos vigente del item. Se utiliza para recorrer en forma inversa
        la relacion padre-hijo (item_padre) filtrando los items no vigentes.
        """
        return self.items_hijos.all()\
            .filter(vigencia=True)\
            .prefetch_related('item_padre', 'categoria')\
            .order_by('nombre', 'precio')

    def get_absolute_url(self):
        return reverse('categorias:item_detail', kwargs={'pk': self.pk})

    def as_tree(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol
        """
        children = list(self.get_children())
        branch = bool(children)
        yield branch, self
        for child in children:
            for next in child.as_tree():
                yield next
        yield branch, None

    def as_tree_min(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol.
        """
        children = list(self.get_children())
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
        Obtiene recursivamente la lista de hijos en forma de arbol.
        Devuelve unicamente objetos que pertenecen a la ultima categoria (hoja).
        !!NO DEVUELVE OBJECTOS DE CATEGORIAS INTERMEDIAS!!
        """
        children = list(self.get_children())
        if bool(self.categoria.get_children()) is False:
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
        children = list(self.get_children())
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
        while hijo is not None:
            nivel += 1
            hijo = hijo.item_padre
        return nivel

    def get_precio_promedio(self):
        return self.precio

    def calcular_costo_unitario(self, anio):
        """
            Devuelve el costo unitario de un item en base a la ultima venta real registrada
        """
        arreglo_dict_desc_id = Itemjerarquia.objects.filter(ancestro=self).values('descendiente')
        arreglo_desc_id = [x['descendiente'] for x in arreglo_dict_desc_id]
        # Se busca si el item tiene hijos
        """arreglo_items = []
                                for item in self.hijos_recursivos():
                                    arreglo_items.append(item)"""

        # Obtiene el costo promedio del año entregado como parametro
        venta = Ventaperiodo.objects.filter(
            item__in=arreglo_desc_id, anio=anio, tipo=0).exclude(
            vta_u=0).order_by('-anio', '-periodo').aggregate(Sum('vta_u'), Sum('costo'))

        if venta['costo__sum'] is not None and venta['vta_u__sum'] is not None:
            return round(float(venta['costo__sum'] / venta['vta_u__sum']), 0)
        else:
            return 0

    def hijos_recursivos(self):
        """
        Itera sobre los hijos del item. Se devuelve a si mismo inicialmente.
        """
        children = list(self.get_children())
        yield self
        for child in children:
            for next in child.hijos_recursivos():
                yield next

    def get_venta_anual(self, anio=None):
        """
        Devuelve un entero con la venta del item para el año entregado como parametro.
        """
        lista_hijos = []

        for hijo in self.hijos_recursivos():
            lista_hijos.append(hijo)
        venta_anual = Ventaperiodo.objects.filter(
            item__in=lista_hijos, anio=anio, tipo__in=[0, 1]).values('anio').annotate(vta_n=Sum('vta_n'))
        if venta_anual.count():
            return int(venta_anual[0]['vta_n'])
        else:
            return 0

    def get_venta_temporada(self, anio=None, temporada=None):
        """
        Devuelve un arreglo con la venta de los ultimos 3 años. La venta esta restringida a los
        periodos de la temporada entregada como parametro.
        """
        periodos = temporada.periodo.all().values('nombre')
        arreglo_dict_id = Itemjerarquia.objects.filter(ancestro=self).values('descendiente')
        arreglo_id = [x['descendiente'] for x in arreglo_dict_id]
        venta_por_anio = Ventaperiodo.objects.filter(
            item__in=arreglo_id,
            anio__in=range(anio-2, anio+1),
            periodo__in=periodos,
            tipo__in=[0, 1]).values('anio').annotate(vta_n=Sum('vta_n')).order_by('anio')
        venta_anual_arr = [0, 0, 0]
        for indice, anio in enumerate(range(anio-2, anio+1)):
            for venta in venta_por_anio:
                if venta['anio'] == anio:
                    venta_anual_arr[indice] = venta['vta_n']
        return venta_anual_arr

    def generar_relaciones(self, tipo=0):
        """
        Crea los registros de Itemjerarquia para si mismo. Se asume que el item ya cuenta con un
        padre definido, con excepción del item raiz.
        Tipo 0 implica que se eliminan las relaciones existentes para el nodo y se crean desde cero.
        Tipo 1 implica que se cuenta la cantidad de relaciones existentes. Si existe en número la cantidad
        correcta, entonces no se hace nada.
        """
        if tipo == 1:
            if self.categoria.get_nivel() == Itemjerarquia.objects.filter(descendiente=self.id).count():
                return False
        Itemjerarquia.objects.filter(descendiente=self.id).delete()
        arr_itemjerarquia = []
        nodo = self
        distancia = 0
        itemjerarquia = Itemjerarquia(ancestro=self, descendiente=self, distancia=distancia)
        arr_itemjerarquia.append(itemjerarquia)
        #print itemjerarquia
        while nodo.item_padre is not None:
            distancia += 1
            itemjerarquia = Itemjerarquia(ancestro=nodo.item_padre, descendiente=self, distancia=distancia)
            #print itemjerarquia
            nodo = nodo.item_padre
            arr_itemjerarquia.append(itemjerarquia)
        if bool(arr_itemjerarquia):
            Itemjerarquia.objects.bulk_create(arr_itemjerarquia)

    get_nivel.short_description = 'Nivel'
    get_nivel.admin_order_field = 'id'


class Itemjerarquia(models.Model):
    """
    Tabla de clausura para mantener las relaciones/caminos del arbol de items.
    Documentación al respecto: http://www.slideshare.net/billkarwin/models-for-hierarchical-data
    """
    ancestro = models.ForeignKey(Item, related_name='descendientes')
    descendiente = models.ForeignKey(Item, related_name='ancestros')
    distancia = models.PositiveIntegerField(default=0)

    def __unicode__(self):
        return str(self.ancestro.nombre) + " " + str(self.descendiente.nombre) + " " + str(self.distancia)


class Grupoitem(models.Model):
    """
    Esta clase guarda el registro de agrupaciones de items creadas por usuarios.
    """
    item_nuevo = models.ForeignKey(Item, related_name='items_agrupados')
    item_agrupado = models.ForeignKey(Item, related_name='+')
    fecha_creacion = models.DateTimeField(default=datetime.now, blank=True)

    def __unicode__(self):
        return self.item_nuevo.nombre
