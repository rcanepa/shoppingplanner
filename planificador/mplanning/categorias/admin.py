from django.contrib import admin
from django.contrib.sites.models import Site
from categorias.models import Categoria
from categorias.models import Item

admin.site.unregister(Site)

class CategoriaAdmin(admin.ModelAdmin):
    fields = ['nombre', 'categoria_padre', 'vigencia']
    list_display = ('get_nivel', 'nombre', 'categoria_padre', 'vigencia')
    list_display_links = ['nombre']

admin.site.register(Categoria, CategoriaAdmin)

class ItemAdmin(admin.ModelAdmin):
    fields = ['categoria', 'nombre', 'item_padre', 'precio', 'usuario_responsable']
    list_display = ('get_nivel', 'categoria', 'nombre', 'item_padre', 'usuario_responsable', 'precio', 'vigencia')
    list_display_links = ['nombre']
    list_filter = ['categoria']
    search_fields = ['nombre']
    ordering = ('-categoria', 'nombre')

admin.site.register(Item, ItemAdmin)