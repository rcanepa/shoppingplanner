# -*- coding: utf-8 -*-
from django import forms
from models import Plan
from models import Temporada


class PlanForm(forms.ModelForm):

    temporada = forms.ModelChoiceField(queryset=Temporada.objects.filter(planificable=True), empty_label="...")

    class Meta:
        model = Plan
        fields = ('anio', 'temporada')

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs['initial']['usuario']
        super(PlanForm, self).__init__(*args, **kwargs)

    """def clean_anio(self):
        anio = self.cleaned_data.get('anio')
        if anio < 1900 or anio > 2100:
            raise forms.ValidationError("Ha escogido un año no válido.")
        else:
            return self.cleaned_data"""

    def clean(self):
        anio = self.cleaned_data.get('anio')
        temporada = self.cleaned_data.get('temporada')
        try:
                Plan.objects.get(anio=anio, temporada=temporada, usuario_creador=self.usuario)
        except Plan.DoesNotExist:
                return self.cleaned_data
        raise forms.ValidationError("Ya existe una planificación para el año y temporada escogida.")


class TemporadaForm(forms.ModelForm):

    class Meta:
        model = Temporada
        fields = ['nombre', 'periodo', 'periodo_final']
