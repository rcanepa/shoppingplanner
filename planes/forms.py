from django import forms
from models import Plan
from models import Temporada


class PlanForm(forms.ModelForm):

    class Meta:
        model = Plan
        fields = ('anio', 'temporada')

    def clean(self):
        anio = self.cleaned_data.get('anio')
        temporada = self.cleaned_data.get('temporada')
        try:
                Plan.objects.get(anio=anio, temporada__nombre=temporada, usuario_creador=self.instance)
        except Plan.DoesNotExist:
                return self.cleaned_data
        raise forms.ValidationError("La planificacion ya ha sido creada.")


class TemporadaForm(forms.ModelForm):

    class Meta:
        model = Temporada
        fields = ['nombre']