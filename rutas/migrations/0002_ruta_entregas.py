# Generated by Django 5.1.7 on 2025-03-27 18:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entrega', '0004_remove_entrega_ruta'),
        ('rutas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruta',
            name='entregas',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rutas', to='entrega.entrega'),
        ),
    ]
