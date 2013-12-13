# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calendario'
        db.create_table(u'calendarios_calendario', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('organizacion', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organizaciones.Organizacion'])),
        ))
        db.send_create_signal(u'calendarios', ['Calendario'])

        # Adding model 'Periodo'
        db.create_table(u'calendarios_periodo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('calendario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['calendarios.Calendario'])),
        ))
        db.send_create_signal(u'calendarios', ['Periodo'])

        # Adding model 'Tiempo'
        db.create_table(u'calendarios_tiempo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('codigo', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('anio', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('semana', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal(u'calendarios', ['Tiempo'])

        # Adding M2M table for field periodo on 'Tiempo'
        m2m_table_name = db.shorten_name(u'calendarios_tiempo_periodo')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tiempo', models.ForeignKey(orm[u'calendarios.tiempo'], null=False)),
            ('periodo', models.ForeignKey(orm[u'calendarios.periodo'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tiempo_id', 'periodo_id'])


    def backwards(self, orm):
        # Deleting model 'Calendario'
        db.delete_table(u'calendarios_calendario')

        # Deleting model 'Periodo'
        db.delete_table(u'calendarios_periodo')

        # Deleting model 'Tiempo'
        db.delete_table(u'calendarios_tiempo')

        # Removing M2M table for field periodo on 'Tiempo'
        db.delete_table(db.shorten_name(u'calendarios_tiempo_periodo'))


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
        u'calendarios.tiempo': {
            'Meta': {'object_name': 'Tiempo'},
            'anio': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'codigo': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'periodo': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['calendarios.Periodo']", 'symmetrical': 'False'}),
            'semana': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
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
        }
    }

    complete_apps = ['calendarios']