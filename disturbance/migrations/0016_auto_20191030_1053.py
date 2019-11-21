# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-30 02:53
from __future__ import unicode_literals

import disturbance.components.compliances.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0015_auto_20191030_1045'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisationcontact',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='organisationcontact',
            name='user_role',
            field=models.CharField(choices=[('organisation_admin', 'Organisation Admin'), ('organisation_user', 'Organisation User'), ('consultant', 'Consultant')], default='organisation_user', max_length=40, verbose_name='Role'),
        ),
        migrations.AddField(
            model_name='organisationcontact',
            name='user_status',
            field=models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending'), ('active', 'Active'), ('declined', 'Declined'), ('unlinked', 'Unlinked'), ('suspended', 'Suspended')], default='draft', max_length=40, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='compliancedocument',
            name='_file',
            field=models.FileField(max_length=500, upload_to=disturbance.components.compliances.models.update_proposal_complaince_filename),
        ),
    ]