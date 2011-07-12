# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("creme_core", "0001_initial"),
    )

    def forwards(self, orm):

        # Adding model 'MarketSegment'
        db.create_table('commercial_marketsegment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('property_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['creme_core.CremePropertyType'])),
        ))
        db.send_create_signal('commercial', ['MarketSegment'])

        # Adding model 'ActType'
        db.create_table('commercial_acttype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('commercial', ['ActType'])

        # Adding model 'Act'
        db.create_table('commercial_act', (
            ('cremeentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['creme_core.CremeEntity'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('expected_sales', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('cost', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('goal', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('due_date', self.gf('django.db.models.fields.DateField')()),
            ('act_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.ActType'])),
            ('segment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegment'])),
        ))
        db.send_create_signal('commercial', ['Act'])

        # Adding model 'ActObjective'
        db.create_table('commercial_actobjective', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('act', self.gf('django.db.models.fields.related.ForeignKey')(related_name='objectives', to=orm['commercial.Act'])),
            ('counter', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('counter_goal', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('ctype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
        ))
        db.send_create_signal('commercial', ['ActObjective'])

        # Adding model 'ActObjectivePattern'
        db.create_table('commercial_actobjectivepattern', (
            ('cremeentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['creme_core.CremeEntity'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('average_sales', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('segment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegment'])),
        ))
        db.send_create_signal('commercial', ['ActObjectivePattern'])

        # Adding model 'ActObjectivePatternComponent'
        db.create_table('commercial_actobjectivepatterncomponent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pattern', self.gf('django.db.models.fields.related.ForeignKey')(related_name='components', to=orm['commercial.ActObjectivePattern'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['commercial.ActObjectivePatternComponent'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ctype', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('success_rate', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('commercial', ['ActObjectivePatternComponent'])

        # Adding model 'CommercialApproach'
        db.create_table('commercial_commercialapproach', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('ok_or_in_futur', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('related_activity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['activities.Activity'], null=True)),
            ('entity_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comapp_entity_set', to=orm['contenttypes.ContentType'])),
            ('entity_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('commercial', ['CommercialApproach'])

        # Adding model 'Strategy'
        db.create_table('commercial_strategy', (
            ('cremeentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['creme_core.CremeEntity'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('commercial', ['Strategy'])

        # Adding M2M table for field evaluated_orgas on 'Strategy'
        db.create_table('commercial_strategy_evaluated_orgas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('strategy', models.ForeignKey(orm['commercial.strategy'], null=False)),
            ('organisation', models.ForeignKey(orm['persons.organisation'], null=False))
        ))
        db.create_unique('commercial_strategy_evaluated_orgas', ['strategy_id', 'organisation_id'])

        # Adding model 'MarketSegmentDescription'
        db.create_table('commercial_marketsegmentdescription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('strategy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='segment_info', to=orm['commercial.Strategy'])),
            ('segment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegment'])),
            ('product', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('place', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('price', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('promotion', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('commercial', ['MarketSegmentDescription'])

        # Adding model 'CommercialAsset'
        db.create_table('commercial_commercialasset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('strategy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assets', to=orm['commercial.Strategy'])),
        ))
        db.send_create_signal('commercial', ['CommercialAsset'])

        # Adding model 'CommercialAssetScore'
        db.create_table('commercial_commercialassetscore', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('score', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('segment_desc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegmentDescription'])),
            ('asset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.CommercialAsset'])),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Organisation'])),
        ))
        db.send_create_signal('commercial', ['CommercialAssetScore'])

        # Adding model 'MarketSegmentCharm'
        db.create_table('commercial_marketsegmentcharm', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('strategy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='charms', to=orm['commercial.Strategy'])),
        ))
        db.send_create_signal('commercial', ['MarketSegmentCharm'])

        # Adding model 'MarketSegmentCharmScore'
        db.create_table('commercial_marketsegmentcharmscore', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('score', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('segment_desc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegmentDescription'])),
            ('charm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegmentCharm'])),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Organisation'])),
        ))
        db.send_create_signal('commercial', ['MarketSegmentCharmScore'])

        # Adding model 'MarketSegmentCategory'
        db.create_table('commercial_marketsegmentcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('strategy', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.Strategy'])),
            ('segment_desc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['commercial.MarketSegmentDescription'])),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Organisation'])),
        ))
        db.send_create_signal('commercial', ['MarketSegmentCategory'])


    def backwards(self, orm):

        # Deleting model 'MarketSegment'
        db.delete_table('commercial_marketsegment')

        # Deleting model 'ActType'
        db.delete_table('commercial_acttype')

        # Deleting model 'Act'
        db.delete_table('commercial_act')

        # Deleting model 'ActObjective'
        db.delete_table('commercial_actobjective')

        # Deleting model 'ActObjectivePattern'
        db.delete_table('commercial_actobjectivepattern')

        # Deleting model 'ActObjectivePatternComponent'
        db.delete_table('commercial_actobjectivepatterncomponent')

        # Deleting model 'CommercialApproach'
        db.delete_table('commercial_commercialapproach')

        # Deleting model 'Strategy'
        db.delete_table('commercial_strategy')

        # Removing M2M table for field evaluated_orgas on 'Strategy'
        db.delete_table('commercial_strategy_evaluated_orgas')

        # Deleting model 'MarketSegmentDescription'
        db.delete_table('commercial_marketsegmentdescription')

        # Deleting model 'CommercialAsset'
        db.delete_table('commercial_commercialasset')

        # Deleting model 'CommercialAssetScore'
        db.delete_table('commercial_commercialassetscore')

        # Deleting model 'MarketSegmentCharm'
        db.delete_table('commercial_marketsegmentcharm')

        # Deleting model 'MarketSegmentCharmScore'
        db.delete_table('commercial_marketsegmentcharmscore')

        # Deleting model 'MarketSegmentCategory'
        db.delete_table('commercial_marketsegmentcategory')


    models = {
        'activities.activity': {
            'Meta': {'ordering': "('-start',)", 'object_name': 'Activity', '_ormbases': ['creme_core.CremeEntity']},
            'busy': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'calendars': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['activities.Calendar']", 'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'is_all_day': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'minutes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['activities.Status']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['activities.ActivityType']"})
        },
        'activities.activitytype': {
            'Meta': {'object_name': 'ActivityType'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'default_day_duration': ('django.db.models.fields.IntegerField', [], {}),
            'default_hour_duration': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'activities.calendar': {
            'Meta': {'ordering': "['name']", 'object_name': 'Calendar'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'activities.status': {
            'Meta': {'object_name': 'Status'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_team': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['creme_core.UserRole']", 'null': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'commercial.act': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Act', '_ormbases': ['creme_core.CremeEntity']},
            'act_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.ActType']"}),
            'cost': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'due_date': ('django.db.models.fields.DateField', [], {}),
            'expected_sales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'goal': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'segment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegment']"}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'commercial.actobjective': {
            'Meta': {'object_name': 'ActObjective'},
            'act': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'objectives'", 'to': "orm['commercial.Act']"}),
            'counter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'counter_goal': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'ctype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'commercial.actobjectivepattern': {
            'Meta': {'ordering': "('id',)", 'object_name': 'ActObjectivePattern', '_ormbases': ['creme_core.CremeEntity']},
            'average_sales': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'segment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegment']"})
        },
        'commercial.actobjectivepatterncomponent': {
            'Meta': {'object_name': 'ActObjectivePatternComponent'},
            'ctype': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['commercial.ActObjectivePatternComponent']"}),
            'pattern': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'components'", 'to': "orm['commercial.ActObjectivePattern']"}),
            'success_rate': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'commercial.acttype': {
            'Meta': {'object_name': 'ActType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '75'})
        },
        'commercial.commercialapproach': {
            'Meta': {'object_name': 'CommercialApproach'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'entity_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comapp_entity_set'", 'to': "orm['contenttypes.ContentType']"}),
            'entity_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ok_or_in_futur': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'related_activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['activities.Activity']", 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'commercial.commercialasset': {
            'Meta': {'object_name': 'CommercialAsset'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assets'", 'to': "orm['commercial.Strategy']"})
        },
        'commercial.commercialassetscore': {
            'Meta': {'object_name': 'CommercialAssetScore'},
            'asset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.CommercialAsset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Organisation']"}),
            'score': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'segment_desc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegmentDescription']"})
        },
        'commercial.marketsegment': {
            'Meta': {'object_name': 'MarketSegment'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'property_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['creme_core.CremePropertyType']"})
        },
        'commercial.marketsegmentcategory': {
            'Meta': {'object_name': 'MarketSegmentCategory'},
            'category': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Organisation']"}),
            'segment_desc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegmentDescription']"}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.Strategy']"})
        },
        'commercial.marketsegmentcharm': {
            'Meta': {'object_name': 'MarketSegmentCharm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'charms'", 'to': "orm['commercial.Strategy']"})
        },
        'commercial.marketsegmentcharmscore': {
            'Meta': {'object_name': 'MarketSegmentCharmScore'},
            'charm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegmentCharm']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Organisation']"}),
            'score': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'segment_desc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegmentDescription']"})
        },
        'commercial.marketsegmentdescription': {
            'Meta': {'object_name': 'MarketSegmentDescription'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'promotion': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'segment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['commercial.MarketSegment']"}),
            'strategy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'segment_info'", 'to': "orm['commercial.Strategy']"})
        },
        'commercial.strategy': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Strategy', '_ormbases': ['creme_core.CremeEntity']},
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'evaluated_orgas': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['persons.Organisation']", 'null': 'True', 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'creme_core.cremeentity': {
            'Meta': {'ordering': "('id',)", 'object_name': 'CremeEntity'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'entity_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'header_filter_search_field': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_actived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'creme_core.cremepropertytype': {
            'Meta': {'object_name': 'CremePropertyType'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subject_ctypes': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'subject_ctypes_creme_property_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['contenttypes.ContentType']"}),
            'text': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'creme_core.userrole': {
            'Meta': {'object_name': 'UserRole'},
            'creatable_ctypes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'raw_admin_4_apps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'raw_allowed_apps': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        'media_managers.image': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Image', '_ormbases': ['creme_core.CremeEntity']},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'Image_media_category_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['media_managers.MediaCategory']"}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '500'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'media_managers.mediacategory': {
            'Meta': {'object_name': 'MediaCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'object_set'", 'to': "orm['contenttypes.ContentType']"}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'po_box': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'persons.legalform': {
            'Meta': {'object_name': 'LegalForm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.organisation': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Organisation', '_ormbases': ['creme_core.CremeEntity']},
            'annual_revenue': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'billing_address_orga_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'capital': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['media_managers.Image']", 'null': 'True', 'blank': 'True'}),
            'legal_form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.LegalForm']", 'null': 'True', 'blank': 'True'}),
            'naf': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'rcs': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Sector']", 'null': 'True', 'blank': 'True'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_address_orga_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'siren': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'siret': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'staff_size': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.StaffSize']", 'null': 'True', 'blank': 'True'}),
            'subject_to_vat': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tvaintra': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url_site': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'persons.sector': {
            'Meta': {'object_name': 'Sector'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.staffsize': {
            'Meta': {'object_name': 'StaffSize'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['commercial']
