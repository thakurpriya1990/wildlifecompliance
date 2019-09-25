# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-09-25 07:40
from __future__ import unicode_literals

import disturbance.components.compliances.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0014_auto_20190925_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amendmentrequestdocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='approvaldocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='approvallogdocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='compliancedocument',
            name='_file',
            field=models.FileField(upload_to=disturbance.components.compliances.models.update_proposal_complaince_filename),
        ),
        migrations.AlterField(
            model_name='compliancedocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='compliancelogdocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='proposaldocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='proposallogdocument',
            name='name',
            field=models.CharField(blank=True, max_length=255, verbose_name='name'),
        ),
    ]
