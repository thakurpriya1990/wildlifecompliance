# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-07-09 07:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0051_campsite_max_vehicles'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='override_reason_info',
            field=models.TextField(blank=True, null=True),
        ),
    ]