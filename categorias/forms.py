from django import forms
from models import Categoria, Item

class CategoriaForm(forms.ModelForm):
	
	class Meta:
		model = Categoria
		fields = ('nombre', 'vigencia', 'categoria_padre')

class ItemForm(forms.ModelForm):
	
	class Meta:
		model = Item
		fields = ('nombre', 'item_padre', 'categoria', 'vigencia', 'usuario_responsable', 'precio')

class ItemResponsableForm(forms.ModelForm):
	
	class Meta:
		model = Item
		fields = ('usuario_responsable',)