# -*- coding: utf-8 -*-
#from django import db
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q, Sum, Max, Min
from calendarios.models import Periodo, Tiempo
from categorias.models import Item
from categorias.models import Itemjerarquia
from organizaciones.models import Organizacion
from ventas.models import Ventaperiodo
from collections import defaultdict
from datetime import datetime
import itertools
import operator


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

    def resumen_venta_planificacion(self):
        """
        Devuelve un diccionario con la venta de todos los items de una planificacion. Cada key corresponde
        al ID de un Item, y esta asociada a un arreglo de objetos que contiene la venta, contribucion, costos
        y otras metricas.
        Ejemplo:
        {
            185895:
                    [
                        {'anio': 2013, 'vta_n': Decimal('8127332.000'), 'ctb_n': Decimal('5210608.000'), 'costo': Decimal('2916723.000'), 
                        'vta_u': Decimal('227.000'), 'item__precio': 49990, 'item_id': 185895}, 
                        {'anio': 2014, 'vta_n': Decimal('2835566.000'), 'ctb_n': Decimal('1807646.000'), 'costo': Decimal('1027920.000'),
                        'vta_u': Decimal('80.000'), 'item__precio': 49990, 'item_id': 185895}
                    ]
        }
        """
        dict_venta = defaultdict(list)
        act_anio = self.anio
        ant_anio = self.anio - 3
        # Lista de ID de los posibles nodos raices del arbol de planificacion
        item_raices_id = Itemplan.objects.filter(plan=self, item_padre=None).values_list('item_id', flat=True)
        # Se buscan todos los descendientes de los nodos raiz
        descendientes = Itemjerarquia.objects.filter(ancestro__id=item_raices_id).values_list('descendiente', flat=True)
        # Se buscan los periodos asociados a la planificacion
        periodos_temporada = self.temporada.periodo.all().values('nombre')
        # Se busca la venta asociada a los descendientes (recordar que la venta solo existe en nodos hoja)
        venta_planificacion = Ventaperiodo.objects.filter(
            item__in=descendientes,
            anio__gte=ant_anio,
            anio__lte=act_anio,
            periodo__in=periodos_temporada,
            #temporada=self.temporada,
            vta_u__gt=0,
            vta_n__gt=0
            ).values(
            'anio', 'item_id', 'item__precio').annotate(
            vta_n=Sum('vta_n'),
            vta_u=Sum('vta_u'),
            ctb_n=Sum('ctb_n'),
            costo=Sum('costo')).order_by(
            'item__id', 'anio')
        # Diccionario con los ID como llave y un arreglo de ventas
        for venta in venta_planificacion:
            venta['precio_vta_u'] = 0
            if venta['anio'] == act_anio:
                try:
                    itemplan_obj = Itemplan.objects.get(item__id=venta['item_id'], plan=self)
                    venta['precio_vta_u'] += venta['vta_u'] * itemplan_obj.precio
                except ObjectDoesNotExist:
                    venta['precio_vta_u'] += venta['vta_u'] * venta['item__precio']
            else:
                venta['precio_vta_u'] += venta['vta_u'] * venta['item__precio']
            # Se calcula el precio blanco "promedio ponderado" para cada item
            # venta['precio_blanco'] = venta['precio_vta_u'] / venta['vta_u']
            # Se corrigen valores negativos de contribucion ya que no pueden ser representados
            # en un grafico de barras.
            #if venta['ctb_n'] < 0:
                #venta['ctb_n'] = 0
            dict_venta[venta['item_id']].append(venta)
        return dict_venta

    def resumen_estadisticas_item(self, temporada=None, item=None):
        """
        Obtiene la venta asociada a un item o grupo de items de una planificacion, de los periodos
        de la temporada planificada, de los ultimos 3 años. El parametro item puede ser un arreglo de objetos Item
        o un objeto Item.
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
            # Se revisa si la variable item contiene un objeto Item o un arreglo de objetos Item
            try:
                iter(item)
            except TypeError:
                # No es iterable, es decir, item solo contiene un objeto
                # Arreglo de items con todos los items hijos del item entregado como parametro
                item_arr_definitivo = Itemjerarquia.objects.filter(ancestro=item).values_list('descendiente', flat=True)
            else:
                # Es iterable, item contiene un arreglo de objetos
                # Arreglo de items con todos los items hijos del item entregado como parametro
                item_arr_definitivo = Itemjerarquia.objects.filter(ancestro__in=item).values_list('descendiente', flat=True)
        # Arreglo de periodos de la temporada de la planificacion.
        periodos_temporada = self.temporada.periodo.all().values('nombre')
        # Se define la temporada sobre la cual se calcularan las ventas
        if temporada is None:
            temporada = self.temporada
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio,
                periodo__in=periodos_temporada,
                #temporada=temporada,
                vta_u__gt=0,
                vta_n__gt=0).values(
                'anio', 'item_id', 'item__precio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo')).order_by(
                'anio')
        elif temporada == "TT":
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio,
                periodo__in=periodos_temporada,
                vta_u__gt=0,
                vta_n__gt=0).values(
                'anio', 'item_id', 'item__precio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo')).order_by(
                'anio')
        else:
            estadisticas = Ventaperiodo.objects.filter(
                item__in=item_arr_definitivo,
                anio__gte=ant_anio,
                anio__lte=act_anio,
                periodo__in=periodos_temporada,
                #temporada=temporada,
                vta_u__gt=0,
                vta_n__gt=0).values(
                'anio', 'item_id', 'item__precio').annotate(
                vta_n=Sum('vta_n'),
                vta_u=Sum('vta_u'),
                ctb_n=Sum('ctb_n'),
                costo=Sum('costo')).order_by(
                'anio')

        # Por cada año, se iteran los distintos items considerados en el resumen.
        lista_anual = []
        for anio, items in itertools.groupby(estadisticas, operator.itemgetter('anio')):
            resumen_anual = defaultdict(int)
            for item in items:
                resumen_anual['anio'] = item['anio']
                resumen_anual['vta_u'] += item['vta_u']
                resumen_anual['vta_n'] += item['vta_n']
                resumen_anual['ctb_n'] += item['ctb_n']
                resumen_anual['costo'] += item['costo']
                # Si corresponde al año de la planificacion, entonces se debe tomar el precio blanco
                # del itemplan.
                if item['anio'] == self.anio:
                    try:
                        itemplan_obj = Itemplan.objects.get(item__id=item['item_id'], plan=self)
                        resumen_anual['precio_vta_u'] += item['vta_u'] * itemplan_obj.precio
                    except ObjectDoesNotExist:
                        resumen_anual['precio_vta_u'] += item['vta_u'] * item['item__precio']
                else:
                    resumen_anual['precio_vta_u'] += item['vta_u'] * item['item__precio']
            resumen_anual['precio_blanco'] = resumen_anual['precio_vta_u'] / resumen_anual['vta_u']
            # Se corrigen valores negativos de contribucion ya que no pueden ser representados en un grafico
            # de barra.
            #if resumen_anual['ctb_n'] < 0:
                #resumen_anual['ctb_n'] = 0
            lista_anual.append(resumen_anual)
        return lista_anual

    def obtener_arbol(self, user):
        # Se obtiene la lista de items sobre los cuales el usuario es resposanble
        # (las distintas raices que pueda tener su arbol)
        items_responsable = Item.objects.filter(usuario_responsable=user)
        # Se busca el itemplan asociado a cada raiz
        itemplan_raices = Itemplan.objects.filter(
            plan=self,
            item__in=items_responsable
            ).prefetch_related('item__categoria')
        # Si existen itemplan asociados al plan, entonces el arbol ha sido definido y debe ser cargado inicialmente
        if bool(itemplan_raices):
            arbol_json = "["
            for itemplan in itemplan_raices:
                for branch, obj in itemplan.as_tree():
                    if obj:
                        if obj.item.categoria.venta_arbol:
                            venta = obj.item.get_venta_temporada(self.anio-1, self.temporada)
                            data = "\"data\":{\"estado\":" + str(obj.estado) + ", \"precio\":" + str(obj.item.precio) + ", \"venta_t\": " + str(venta[2]) + ", \"venta_t1\": " + str(venta[1]) + ", \"venta_t2\": " + str(venta[0]) + "}, "
                        else:
                            data = "\"data\":{\"estado\": 0, \"precio\":" + str(obj.item.precio) + "}, "
                        if obj.item.categoria.planificable:
                            extraClasses = "\"extraClasses\":\"planificable\","
                        else:
                            extraClasses = ""
                        if branch:
                            arbol_json += "{" + data + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"True\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\", \"expanded\":\"True\", \"children\":["
                        else:
                            if bool(obj.item.get_children()):
                                arbol_json += "{" + data + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"True\", \"lazy\":\"True\", \"key\":\"" + str(obj.item.id) + "\" }"
                            else:
                                arbol_json += "{" + data + extraClasses + "\"title\":\"" + obj.nombre + "\", \"key\":\"" + str(obj.item.id) + "\" }"
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
                if obj.categoria.venta_arbol:
                    venta = obj.get_venta_temporada(self.anio-1, self.temporada)
                    data = "\"data\":{\"estado\": 0, \"precio\":" + str(obj.precio) + ", \"venta_t\": " + str(venta[2]) + " \"venta_t1\": " + str(venta[1]) + " \"venta_t2\": " + str(venta[0]) + "}, "
                else:
                    data = "\"data\":{\"estado\": 0, \"precio\":" + str(obj.precio) + "}, "
                if obj.categoria.planificable:
                    extraClasses = "\"extraClasses\":\"planificable\","
                else:
                    extraClasses = ""
                arbol_json += "{" + data + extraClasses + "\"title\":\"" + obj.nombre + "\", \"folder\":\"False\", \"lazy\":\"True\", \"key\":\"" + str(obj.id) + "\" },"
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

    def get_num_pendientes(self):
        """
            Devuelve la cantidad de Items que no han sido planificados.
        """
        return Itemplan.objects.filter(plan=self, planificable=True).exclude(estado=2).count()

    def get_num_planificados(self):
        """
            Devuelve la cantidad de Items que han sido planificados.
        """
        return Itemplan.objects.filter(plan=self, estado=2, planificable=True).count()

    def get_num_total(self):
        """
            Devuelve la cantidad total de Items que contiene el plan.
        """
        return Itemplan.objects.filter(plan=self, planificable=True).count()

    def get_progreso(self):
        """
        Devuelve el porcentaje de avance de un plan en formato string. Se obtiene
        a partir del cuociente entre los Items planificados y el total de Items de la
        planificacion.
        """
        if self.get_num_total() != 0:
            return str(round(float(self.get_num_planificados() / float(self.get_num_total())), 2)) + "%"
        else:
            return "0.0" + "%"

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

    def get_padre_nombre(self):
        """
        Devuelve un arreglo con todos los nombres itemplan padres de self.
        """
        arreglo_padres = []
        padre = self.item_padre
        while padre is not None:
            arreglo_padres.append(padre.nombre)
            padre = padre.item_padre
        return arreglo_padres

    def iterar_hijos(self):
        """
        Itera sobre los hijos del item. Se devuelve a si mismo inicialmente.
        """
        children = list(self.get_children())
        yield self
        for child in children:
            for next in child.iterar_hijos():
                yield next

    def __unicode__(self):
        return self.item.nombre
