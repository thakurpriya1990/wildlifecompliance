# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-12-18 02:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mooring', '0080_booking_admission_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='RefundPricePeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentage', models.FloatField()),
                ('days', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
