# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-03-03 02:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0440_offence_occurrence_datetime_to'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offence',
            name='occurrence_date_from',
        ),
        migrations.RemoveField(
            model_name='offence',
            name='occurrence_date_to',
        ),
        migrations.RemoveField(
            model_name='offence',
            name='occurrence_time_from',
        ),
        migrations.RemoveField(
            model_name='offence',
            name='occurrence_time_to',
        ),
    ]
