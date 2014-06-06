# -*- coding: utf-8 -*-
from django import db
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from categorias.models import Item
from ventas.models import Ventaperiodo
import time


def buscar_hijos(item, arreglo_items):
    hijos = [itemplan for itemplan in arreglo_items if itemplan['item_padre_id'] == item['id']]
    yield item
    for hijo in hijos:
        for next in buscar_hijos(hijo, arreglo_items):
                yield next


def build_tree(nodes):
    """http://stackoverflow.com/questions/757244/converting-tree-list-to-hierarchy-dict"""
    # create empty tree to fill
    tree = {}

    # fill in tree starting with roots (those with no parent)
    build_tree_recursive(tree, None, nodes)

    return tree


def build_tree_recursive(tree, parent, nodes):
    # find children
    children = [n for n in nodes if n['item_padre_id'] == parent]
    children = sorted(children, key=lambda child: child['nombre'])

    # build a subtree for each child
    for child in children:
        # start new subtree
        tree[child['id']] = child

        # call recursively to build a subtree for current node
        build_tree_recursive(tree[child['id']], child['id'], nodes)


# http://www.quesucede.com/page/show/id/python-3-tree-implementation
(_ROOT, _DEPTH, _BREADTH) = range(3)


class Node:
    def __init__(self, identifier, title):
        self.__identifier = identifier
        self.__children = []
        self.__title = title

    @property
    def identifier(self):
        return self.__identifier

    @property
    def children(self):
        return self.__children

    @property
    def title(self):
        return self.__title

    def add_child(self, identifier):
        self.__children.append(identifier)


class Tree:

    def __init__(self):
        self.__nodes = {}

    @property
    def nodes(self):
        return self.__nodes

    def add_node(self, identifier, title, parent=None):
        node = Node(identifier, title)
        self[identifier] = node

        if parent is not None:
            self[parent].add_child(identifier)

        return node

    def display(self, identifier, depth=_ROOT):
        children = self[identifier].children
        if depth == _ROOT:
            print "{0}".format(identifier)
        else:
            print "\t"*depth, "{0}".format(identifier)

        depth += 1
        for child in children:
            self.display(child, depth)  # recursive call

    def traverse(self, identifier, mode=_DEPTH):
        # Python generator. Loosly based on an algorithm from
        # 'Essential LISP' by John R. Anderson, Albert T. Corbett,
        # and Brian J. Reiser, page 239-241
        yield identifier
        queue = self[identifier].children
        while queue:
            yield queue[0]
            expansion = self[queue[0]].children
            if mode is _DEPTH:
                queue = expansion + queue[1:]  # depth-first
            elif mode is _BREADTH:
                queue = queue[1:] + expansion  # width-first

    def __getitem__(self, key):
        return self.__nodes[key]

    def __setitem__(self, key, item):
        self.__nodes[key] = item


def get_venta_temporada(item_id=None, anio=None, temporada=None):
        """
        Devuelve un entero con la venta del item para el año y temporada (periodos) entregados
        como parametros.
        """

        try:
            item_obj = Item.objects.get(id=item_id)
        except ObjectDoesNotExist:
            return 0
        lista_hijos = []
        periodos = temporada.periodo.all().values('nombre')
        # Reset queries
        db.reset_queries()
        #start_time = time.time()
        for hijo in item_obj.hijos_recursivos():
            lista_hijos.append(hijo)
        #print time.time() - start_time, "seconds"
        #print "Cantidad de items hijos: " + str(len(lista_hijos))
        #print "QUERIES get_venta_temporada: " + str(len(db.connection.queries))
        venta_anual = Ventaperiodo.objects.filter(
            item__in=lista_hijos, anio=anio, periodo__in=periodos, tipo__in=[0, 1]).values('anio').annotate(vta_n=Sum('vta_n'))

        if venta_anual.count():
            return int(venta_anual[0]['vta_n'])
        else:
            return 0
