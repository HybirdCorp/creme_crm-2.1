# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone

import creme.creme_core.models.fields


class Migration(migrations.Migration):
    dependencies = [
        ('creme_core', '0001_initial'),
        ('persons', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('activities', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketSegment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('property_type', models.ForeignKey(editable=False, to='creme_core.CremePropertyType')),
            ],
            options={
                'verbose_name': 'Market segment',
                'verbose_name_plural': 'Market segments',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=75, verbose_name='Title')),
                ('is_custom', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('title',),
                'verbose_name': 'Type of Commercial Action',
                'verbose_name_plural': 'Types of Commercial Actions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Act',
            fields=[
                ('cremeentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='creme_core.CremeEntity')),
                ('name', models.CharField(max_length=100, verbose_name='Name of the commercial action')),
                ('expected_sales', models.PositiveIntegerField(verbose_name='Expected sales')),
                ('cost', models.PositiveIntegerField(null=True, verbose_name='Cost of the commercial action', blank=True)),
                ('goal', models.TextField(null=True, verbose_name='Goal of the action', blank=True)),
                ('start', models.DateField(verbose_name='Start')),
                ('due_date', models.DateField(verbose_name='Due date')),
                ('segment', models.ForeignKey(verbose_name='Related segment', to='commercial.MarketSegment')),
                ('act_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='Type', to='commercial.ActType')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Commercial Action',
                'verbose_name_plural': 'Commercial Actions',
            },
            bases=('creme_core.cremeentity',),
        ),
        migrations.CreateModel(
            name='ActObjective',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('counter', models.PositiveIntegerField(default=0, verbose_name='Counter', editable=False)),
                ('counter_goal', models.PositiveIntegerField(default=1, verbose_name='Value to reach')),
                ('act', models.ForeignKey(related_name='objectives', editable=False, to='commercial.Act')),
                ('ctype', creme.creme_core.models.fields.CTypeForeignKey(blank=True, editable=False, to='contenttypes.ContentType', null=True, verbose_name='Counted type')),
                ('filter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, editable=False, to='creme_core.EntityFilter', null=True, verbose_name='Filter on counted entities')),
            ],
            options={
                'verbose_name': 'Commercial Objective',
                'verbose_name_plural': 'Commercial Objectives',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActObjectivePattern',
            fields=[
                ('cremeentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='creme_core.CremeEntity')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('average_sales', models.PositiveIntegerField(verbose_name='Average sales')),
                ('segment', models.ForeignKey(verbose_name='Related segment', to='commercial.MarketSegment')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Commercial objective pattern',
                'verbose_name_plural': 'Commercial objective patterns',
            },
            bases=('creme_core.cremeentity',),
        ),
        migrations.CreateModel(
            name='ActObjectivePatternComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('success_rate', models.PositiveIntegerField(verbose_name='Success rate')),
                ('ctype', creme.creme_core.models.fields.CTypeForeignKey(blank=True, editable=False, to='contenttypes.ContentType', null=True, verbose_name='Counted type')),
                ('filter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, editable=False, to='creme_core.EntityFilter', null=True, verbose_name='Filter on counted entities')),
                ('parent', models.ForeignKey(related_name='children', editable=False, to='commercial.ActObjectivePatternComponent', null=True)),
                ('pattern', models.ForeignKey(related_name='components', editable=False, to='commercial.ActObjectivePattern')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommercialApproach',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('ok_or_in_futur', models.BooleanField(default=False, verbose_name='Done ?', editable=False)),
                ('description', models.TextField(null=True, verbose_name='Description', blank=True)),
                ('creation_date', creme.creme_core.models.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='Creation date', editable=False, blank=True)),
                ('entity_id', models.PositiveIntegerField(editable=False)),
                ('entity_content_type', models.ForeignKey(related_name='comapp_entity_set', editable=False, to='contenttypes.ContentType')),
                ('related_activity', models.ForeignKey(editable=False, to='activities.Activity', null=True)),
            ],
            options={
                'verbose_name': 'Commercial approach',
                'verbose_name_plural': 'Commercial approaches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Strategy',
            fields=[
                ('cremeentity_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='creme_core.CremeEntity')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('evaluated_orgas', models.ManyToManyField(to='persons.Organisation', null=True, editable=False)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Commercial strategy',
                'verbose_name_plural': 'Commercial strategies',
            },
            bases=('creme_core.cremeentity',),
        ),
        migrations.CreateModel(
            name='MarketSegmentDescription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('product', models.TextField(null=True, verbose_name='Product', blank=True)),
                ('place', models.TextField(null=True, verbose_name='Place', blank=True)),
                ('price', models.TextField(null=True, verbose_name='Price', blank=True)),
                ('promotion', models.TextField(null=True, verbose_name='Promotion', blank=True)),
                ('segment', models.ForeignKey(to='commercial.MarketSegment')),
                ('strategy', models.ForeignKey(related_name='segment_info', editable=False, to='commercial.Strategy')),
            ],
            options={
                'verbose_name': 'Market segment description',
                'verbose_name_plural': 'Market segment descriptions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommercialAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('strategy', models.ForeignKey(related_name='assets', editable=False, to='commercial.Strategy')),
            ],
            options={
                'verbose_name': 'Commercial asset',
                'verbose_name_plural': 'Commercial assets',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommercialAssetScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.PositiveSmallIntegerField()),
                ('asset', models.ForeignKey(to='commercial.CommercialAsset')),
                ('organisation', models.ForeignKey(to='persons.Organisation')),
                ('segment_desc', models.ForeignKey(to='commercial.MarketSegmentDescription')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MarketSegmentCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.PositiveSmallIntegerField()),
                ('organisation', models.ForeignKey(to='persons.Organisation')),
                ('strategy', models.ForeignKey(to='commercial.Strategy')),
                ('segment_desc', models.ForeignKey(to='commercial.MarketSegmentDescription')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MarketSegmentCharm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('strategy', models.ForeignKey(related_name='charms', editable=False, to='commercial.Strategy')),
            ],
            options={
                'verbose_name': 'Segment charm',
                'verbose_name_plural': 'Segment charms',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MarketSegmentCharmScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.PositiveSmallIntegerField()),
                ('charm', models.ForeignKey(to='commercial.MarketSegmentCharm')),
                ('organisation', models.ForeignKey(to='persons.Organisation')),
                ('segment_desc', models.ForeignKey(to='commercial.MarketSegmentDescription')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
