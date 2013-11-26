from django.conf.urls import patterns, include, url
from categorias import views

urlpatterns = patterns('',
	url(r'^cat/list/$', views.CategoriaListView.as_view(), name='categoria_list'),
	url(r'^cat/detail/(?P<pk>\d+)/$', views.CategoriaDetailView.as_view(), name='categoria_detail'),
    url(r'^cat/update/(?P<pk>\d+)/$', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    url(r'^cat/create/$', views.CategoriaCreateView.as_view(), name='categoria_create'),
	url(r'^cat/delete/(?P<pk>\d+)/$', views.CategoriaDeleteView.as_view(), name='categoria_delete'),

	url(r'^item/list/$', views.ItemListView.as_view(), name='item_list'),
	url(r'^item/detail/(?P<pk>\d+)/$', views.ItemDetailView.as_view(), name='item_detail'),
	url(r'^item/update/(?P<pk>\d+)/$', views.ItemUpdateView.as_view(), name='item_update'),
	url(r'^item/update_resp/(?P<pk>\d+)/$', views.ItemResponsableUpdateView.as_view(), name='item_responsable_update'),
	url(r'^item/create/$', views.ItemCreateView.as_view(), name='item_create'),
	url(r'^item/delete/(?P<pk>\d+)/$', views.ItemDeleteView.as_view(), name='item_delete'),
	url(r'^item/responsables/$', views.ItemResponsablesView.as_view(), name='item_responsables'),
)