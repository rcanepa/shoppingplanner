from django.contrib import admin
from calendarios.models import Periodo
from calendarios.models import Temporada

class TemporadaAdmin(admin.ModelAdmin):
    fields = ['nombre']
    list_display = ['nombre']
    list_display_links = ['nombre']

admin.site.register(Temporada, TemporadaAdmin)

class PeriodoAdmin(admin.ModelAdmin):
    fields = ['periodo', 'mes', 'temporada']
    list_display = ('periodo', 'mes', 'temporada')
    list_display_links = ['periodo']
    list_filter = ['temporada','mes']
    search_fields = ['temporada']
    ordering = ['temporada', 'mes']

admin.site.register(Periodo, PeriodoAdmin)