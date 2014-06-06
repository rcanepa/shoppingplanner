# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Itemjerarquia'
        db.create_table(u'categorias_itemjerarquia', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ancestro', self.gf('django.db.models.fields.related.ForeignKey')(related_name='descendientes', to=orm['categorias.Item'])),
            ('descendiente', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ancestros', to=orm['categorias.Item'])),
            ('distancia', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'categorias', ['Itemjerarquia'])


    def backwards(self, orm):
        # Deleting model 'Itemjerarquia'
        db.delete_table(u'categorias_itemjerarquia')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'calendarios.calendario': {
            'Meta': {'object_name': 'Calendario'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'organizacion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizaciones.Organizacion']"})
        },
        u'calendarios.periodo': {
            'Meta': {'ordering': "['nombre']", 'object_name': 'Periodo'},
            'calendario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['calendarios.Calendario']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'categorias.categoria': {
            'Meta': {'object_name': 'Categoria'},
            'categoria_padre': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'categorias_hijos'", 'null': 'True', 'to': u"orm['categorias.Categoria']"}),
            'fecha_creacion': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'organizacion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizaciones.Organizacion']"}),
            'planificable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'venta_arbol': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vigencia': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'categorias.grupoitem': {
            'Meta': {'object_name': 'Grupoitem'},
            'fecha_creacion': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_agrupado': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['categorias.Item']"}),
            'item_nuevo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items_agrupados'", 'to': u"orm['categorias.Item']"})
        },
        u'categorias.item': {
            'Meta': {'object_name': 'Item'},
            'categoria': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['categorias.Categoria']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_real': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'item_padre': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'items_hijos'", 'null': 'True', 'to': u"orm['categorias.Item']"}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'precio': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'temporada': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'items_temporada'", 'null': 'True', 'to': u"orm['planes.Temporada']"}),
            'usuario_responsable': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'items_responsable'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'vigencia': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'categorias.itemjerarquia': {
            'Meta': {'object_name': 'Itemjerarquia'},
            'ancestro': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'descendientes'", 'to': u"orm['categorias.Item']"}),
            'descendiente': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ancestros'", 'to': u"orm['categorias.Item']"}),
            'distancia': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'organizaciones.organizacion': {
            'Meta': {'object_name': 'Organizacion'},
            'fecha_creacion': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'usuario_creador': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'vigencia': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'planes.temporada': {
            'Meta': {'object_name': 'Temporada'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'organizacion': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organizaciones.Organizacion']"}),
            'periodo': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['calendarios.Periodo']", 'symmetrical': 'False'}),
            'periodo_final': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['calendarios.Periodo']"}),
            'planificable': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['categorias']