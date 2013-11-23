from django import forms
from models import Plan
from models import Temporada


class PlanForm(forms.ModelForm):

    class Meta:
        model = Plan
        fields = ('anio', 'temporada')


class TemporadaForm(forms.ModelForm):

    class Meta:
        model = Temporada
        fields = ['nombre']