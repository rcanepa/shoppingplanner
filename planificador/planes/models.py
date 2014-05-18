# -*- coding: utf-8 -*-
from collections import defaultdict
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum, Max, Min, Avg
from calendarios.models import Periodo, Tiempo
from categorias.models import Item
from organizaciones.models import Organizacion
from ventas.models import Ventaperiodo
from datetime import datetime


class Temporada(models.Model):
    nombre = models.CharField(max_length=50)
    planificable = models.BooleanField(default=True)
    organizacion = models.ForeignKey(Organizacion)
    periodo = models.ManyToManyField(Periodo)
    periodo_final = models.ForeignKey(Periodo, related_name="+", help_text="Seleccione el último periodo de la temporada.")

    def __unicode__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('planes:temporada_detail', kwargs={'pk': self.pk})

    def periodos_proyeccion(self, anio, periodos=3):
        """
        Recibe como parametro la cantidad de periodos por sobre y bajo los periodos de una
        temporada que se quieren encontrar. Devuelve el periodo que esta bajo X periodos del periodo
        inferior de una temporada y el periodo superior por X periodos del periodo superior de una temporada
        """
        anio_pre = anio - 2
        anio_post = anio
        data = []
        # Se buscan todos los periodos asociados a la temporada
        periodos = self.periodo.all()
        # Se obtiene el periodo inferior
        periodo_inf = periodos[0]
        # Se obtiene el periodo superior
        periodo_sup = periodos[periodos.count()-1]
        # Se obtiene el periodo superior + X periodos
        periodos_sup_vta = Tiempo.objects.filter(
            Q(anio=anio-1, periodo__nombre__gt=periodo_sup.nombre) |
            Q(anio=anio_post, periodo__nombre__lt=periodo_inf.nombre)).values('periodo__nombre').annotate(
            anio=Max('anio'), semana=Max('semana')).order_by('anio', 'semana')[2]
        # Se obtiene el periodo inferior - X periodos
        periodos_inf_vta = Tiempo.objects.filter(
            Q(anio=anio-1, periodo__nombre__lt=periodo_inf.nombre) |
            Q(anio=anio_pre, periodo__nombre__gt=periodo_inf.nombre)).values('periodo__nombre').annotate(
            anio=Max('anio'), semana=Min('semana')).order_by('-anio', '-semana')[2]
        data.append(periodos_inf_vta)
        data.append(periodos_sup_vta)
        return data

    def comprobar_periodo(self, periodo):
        """
        Devuelve True si el periodo pertenece a la lista de periodos de la temporada y False
        en caso contrario
        """
        # Se revisa si el valor de periodo es un string
        if (isinstance(periodo, basestring)):
            return bool(self.periodo.filter(nombre=periodo))
        # En caso contrario se entrega el nombre del objeto periodo
        else:
            return bool(self.periodo.filter(nombre=periodo.nombre))


class Plan(models.Model):
    ESTADOS = (
        (0, 'Nueva'),
        (1, 'Arbol de planificacion definido'),
        (2, 'Proyeccion finalizada'),
        (3, 'Plafinicacion finalizada'),
        )
    nombre = models.CharField(max_length=70)
    anio = models.PositiveSmallIntegerField(verbose_name="año", default=(datetime.now()).year)
    temporada = models.ForeignKey(Temporada)
    usuario_creador = models.ForeignKey(User)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])

    def get_num_items_planificables(self):
        num_items = Itemplan.objects.filter(plan=self.id, planificable=True).count()
        return num_items

    def resumen_estadisticas(self, temporada=None, item=None):
        """
        Obtiene la venta asociada a todos los items de una planificacion entre los
        ultimos 3 años.
        """
        # Contiene la lista de items que seran consultados para buscar las ventas
        item_arr_definitivo = []
        # Año actual (por planificar)
        act_anio = self.anio
        # Año actual - 3 (limite inferior)
        ant_anio = self.anio - 3
        if item is None:
            # Arreglo de items con todos los items de la planificacion
            item_arr_definitivo = [itemplan.item for itemplan in self.item_planificados.all().prefetch_related(
                'item__categoria') if itemplan.item.categoria.planificable]
        else:
            # Arreglo de items con todos los items hijos del item entregado como parametro
            item_arr_definitivo = [x for x in item.get_hijos() if x.categoria.planificable]
        # Se define la temporada sobre la cual se calcularan las ventas
        if temporada is None:
            temporada = self.temporada
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio,
                temporada=temporada).values(
                'anio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo'),
                precio_prom=Avg('item__precio')).order_by(
                'anio')
        elif temporada == "TT":
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio).values(
                'anio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo'),
                precio_prom=Avg('item__precio')).order_by(
                'anio')
        else:
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio,
                temporada=temporada).values(
                'anio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo'),
                precio_prom=Avg('item__precio')).order_by(
                'anio')
        return estadisticas

    def obtener_arbol(self, user):
        # Se obtiene la lista de items sobre los cuales el usuario es resposanble
        # (las distintas raices que pueda tener su arbol)
        items_responsable = Item.objects.filter(usuario_responsable=user)
        # Se busca el itemplan asociado a cada raiz
        itemplan_raices = Itemplan.objects.filter(
            plan=self,
            item__in=items_responsable
            ).select_related('item__categoria')
        # Si existen itemplan asociados al plan, entonces el arbol ha sido definido y debe ser cargado inicialmente
        if bool(itemplan_raices):
            arbol_json = "["
            for itemplan in itemplan_raices:
                for branch, obj in itemplan.as_tree():
                    if obj:
                        if obj.item.categoria.planificable:
                            extraClasses = "\"extraClasses\":\"planificable\","
                        else:
                            extraClasses = ""
                        if branch:
                            if obj.item.precio != 0:
                                arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + " | " + "{:,}".format(obj.item.precio) + "\", \"folder\":\"True\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\", \"expanded\":\"True\", \"children\":["
                            else:
                                arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"True\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\", \"expanded\":\"True\", \"children\":["
                        else:
                            if obj.item.precio != 0:
                                if bool(obj.item.get_children()):
                                    arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + " | " + "{:,}".format(obj.item.precio) + "\", \"folder\":\"True\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\" }"
                                else:
                                    arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + " | " + "{:,}".format(obj.item.precio) + "\", \"key\":\"" + str(obj.item.id) + "\" }"
                            else:
                                if bool(obj.item.get_children()):
                                    arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"False\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\" }"
                                else:
                                    arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + "\", \"key\":\"" + str(obj.item.id) + "\" }"
                    else:
                        if branch:
                            arbol_json = arbol_json[:-1]
                            arbol_json += "]},"
                        else:
                            arbol_json += ","

            arbol_json = arbol_json[:-1]  # Se quita una ultima coma que esta demas
            arbol_json += "]"
        # En caso de que no existan itemplan asociados al plan, entonces el arbol no ha sido definido
        # y solo se debe cargar el primer nodo
        else:
            arbol_json = "["
            for obj in items_responsable:
                if obj.categoria.planificable:
                    extraClasses = "\"extraClasses\":\"planificable\","
                else:
                    extraClasses = ""
                arbol_json += "{" + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"False\", \"lazy\":\"True\", \"key\":\"" + str(obj.id) + "\" },"
            arbol_json = arbol_json[:-1]
            arbol_json += "]"
        return arbol_json

    def resumen_plan_item(self):
        """
        Devuelve un diccionario con todos los items de la planificacion, unidades de avance, saldo y temporada vigente,
        ademas del costo total asociado
        """
        periodo_inf = self.temporada.periodo.all().order_by('nombre')[:1].get()
        periodo_sup = self.temporada.periodo.all().order_by('-nombre')[:1].get()

        # Se obtiene toda la venta asociada a la planificacion
        venta_planificada = Ventaperiodo.objects.filter(
            plan=self, tipo=2).select_related('item').order_by(
            'item', 'anio', 'periodo')

        d_totales_venta = defaultdict()
        d_item = defaultdict(int)

        for venta in venta_planificada:
            d_item['nombre'] = venta.item.nombre
            d_item['vta_u_total'] += venta.vta_u
            d_item['costo_total'] += venta.costo
            if venta.anio == self.anio and (venta.periodo <= periodo_sup.nombre and venta.periodo >= periodo_inf):
                d_item['vta_u_vigente'] += venta.vta_u
            elif (venta.anio == self.anio and venta.periodo > periodo_sup.nombre) or (venta.anio > self.anio and venta.periodo < periodo_inf ):
                d_item['vta_u_saldo'] += venta.vta_u
            else:
                d_item['vta_u_avance'] += venta.vta_u
            d_totales_venta[venta.item.id] = d_item

        # Devuelve un diccionario con todos los itemplan de la planificacion, unidades y costos asociados
        return d_totales_venta

    def __unicode__(self):
        return str(self.anio) + " " + str(self.temporada)

    def get_absolute_url(self):
        return reverse('planes:plan_detail', kwargs={'pk': self.pk})


class Itemplan(models.Model):
    ESTADOS = (
        (0, 'Pendiente'),
        (1, 'Proyectado'),
        (2, 'Planificado'),
        )
    nombre = models.CharField(max_length=70)
    estado = models.PositiveSmallIntegerField(choices=ESTADOS, default=ESTADOS[0][0])
    planificable = models.BooleanField(default=False)
    item_padre = models.ForeignKey('self', blank=True, null=True, related_name='items_hijos')
    item = models.ForeignKey(Item, related_name='item_proyectados')
    plan = models.ForeignKey(Plan, related_name='item_planificados')
    precio = models.PositiveIntegerField(default=0)
    costo = models.PositiveIntegerField(default=0)

    def get_children(self):
        """
        Devuelve la lista de itemplan hijos del itemplan. Se utiliza para recorrer en forma inversa
        la relacion padre-hijo (item_padre).
        """
        return self.items_hijos.all().prefetch_related('item__categoria').order_by('nombre', 'precio')

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

    def get_hijos_planificables(self):
        """
        Obtiene recursivamente la lista de hijos en forma de arbol que pueden ser planificables segun su categoria,
        es decir, pertenecen a una categoria planificable (planificable == True) y que fueron escogidos en el arbol
        para ser planificados, es decir, self.planificable == True.
        """
        children = list(self.get_children())
        if self.item.categoria.planificable and self.planificable:
            yield self
        for child in children:
            for next in child.get_hijos_planificables():
                yield next

    def get_padre(self):
        """
        Devuelve un arreglo con todos los objetos itemplan padres de self.
        """
        arreglo_padres = []
        padre = self.item_padre
        while padre is not None:
            arreglo_padres.append(padre)
            padre = padre.item_padre
        return arreglo_padres

    def __unicode__(self):
        return self.item.nombre
