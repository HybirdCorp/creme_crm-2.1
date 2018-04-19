# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-18 10:53
from __future__ import unicode_literals

import uuid

from django.conf import settings
from django.db import migrations, models
from django.db.models.deletion import CASCADE, PROTECT


class Migration(migrations.Migration):
    dependencies = [
        ('creme_core', '0039_v1_8__imprint'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sandbox',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('type_id', models.CharField(editable=False, max_length=48, verbose_name='Type of sandbox')),
                ('role', models.ForeignKey(default=None, editable=False, null=True, on_delete=CASCADE, to='creme_core.UserRole', verbose_name='Related role')),
                ('user', models.ForeignKey(default=None, editable=False, null=True, on_delete=CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Related user')),
            ],
        ),
        migrations.AddField(
            model_name='cremeentity',
            name='sandbox',
            field=models.ForeignKey(editable=False, null=True, on_delete=PROTECT, to='creme_core.Sandbox'),
        ),
    ]
