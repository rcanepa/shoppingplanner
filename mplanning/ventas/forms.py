from django import forms
from models import Controlventa

class ControlventaForm(forms.ModelForm):
    
    class Meta:
        model = Controlventa
        fields = ('anio','periodo')