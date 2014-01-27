from django.contrib import admin
from django.contrib.sites.models import Site
from organizaciones.models import Organizacion

class OrganizacionAdmin(admin.ModelAdmin):
    fields = ['nombre', 'vigencia', 'usuario_creador']
    list_display = ['nombre', 'vigencia', 'usuario_creador']
    list_display_links = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']

admin.site.register(Organizacion, OrganizacionAdmin)