# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-05-01 06:06
from __future__ import unicode_literals

import disturbance.components.approvals.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0003_auto_20180430_1344'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalLogDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('_file', models.FileField(upload_to=disturbance.components.approvals.models.update_approval_comms_log_filename)),
                ('log_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='disturbance.ApprovalLogEntry')),
            ],
        ),
    ]