from django.contrib import admin
from .models import Ventaperiodo
from .models import Controlventa


class VentaperiodoAdmin(admin.ModelAdmin):
    #fields = ['nombre', 'categoria_padre', 'vigencia']
    #list_display = ('get_nivel', 'nombre', 'categoria_padre', 'vigencia')
    #list_display_links = ['nombre']
    pass

admin.site.register(Ventaperiodo, VentaperiodoAdmin)

class ControlventaAdmin(admin.ModelAdmin):
    #fields = ['categoria', 'nombre', 'item_padre', 'precio', 'usuario_responsable']
    #list_display = ('get_nivel', 'categoria', 'nombre', 'item_padre', 'usuario_responsable', 'precio', 'vigencia')
    #list_display_links = ['nombre']
    #list_filter = ['categoria']
    #search_fields = ['nombre']
    #ordering = ('-categoria', 'nombre')
    pass

admin.site.register(Controlventa, ControlventaAdmin)