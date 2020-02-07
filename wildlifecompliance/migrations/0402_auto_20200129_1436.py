# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-01-29 06:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0401_auto_20200129_1344'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='briefofevidencerecordofinterview',
            name='parent',
        ),
        migrations.AddField(
            model_name='briefofevidencerecordofinterview',
            name='children',
            field=models.ManyToManyField(related_name='_briefofevidencerecordofinterview_children_+', to='wildlifecompliance.BriefOfEvidenceRecordOfInterview'),
        ),
    ]
