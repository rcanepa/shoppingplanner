# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from models import Categoria, Item


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ('nombre', 'vigencia', 'categoria_padre', 'planificable', 'venta_arbol', 'jerarquia_independiente')

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs['initial']['usuario']
        super(CategoriaForm, self).__init__(*args, **kwargs)

    # Valida que no haya otra categoria con jerarquia independiente. Solo se admite una sola con esta caracteristica.
    def clean_jerarquia_independiente(self):
        jerarquia_independiente = self.cleaned_data['jerarquia_independiente']
        if jerarquia_independiente:
            try:
                categoria_independiente = Categoria.objects.get(
                    organizacion=self.usuario.get_profile().organizacion,
                    jerarquia_independiente=True)
                raise forms.ValidationError("Solo puede existir una categoria con jerarquia independiente. Actualmente " + categoria_independiente.nombre + " tiene jerarquia independiente.")
            except ObjectDoesNotExist:
                return jerarquia_independiente
        else:
            return jerarquia_independiente


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ('nombre', 'item_padre', 'categoria', 'vigencia', 'usuario_responsable', 'precio')


class ItemResponsableForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ('usuario_responsable',)
