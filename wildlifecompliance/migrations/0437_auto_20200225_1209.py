# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-02-25 04:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0436_auto_20200224_1040'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentartifact',
            name='brief_of_evidence_legal_cases',
        ),
        migrations.RemoveField(
            model_name='documentartifact',
            name='prosecution_brief_legal_cases',
        ),
        migrations.RemoveField(
            model_name='physicalartifact',
            name='brief_of_evidence_legal_cases',
        ),
        migrations.RemoveField(
            model_name='physicalartifact',
            name='prosecution_brief_legal_cases',
        ),
    ]
