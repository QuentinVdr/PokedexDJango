# Generated by Django 5.0 on 2023-12-07 14:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0002_pokemon_team_userprofile_delete_person_pokemon_team_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokemon',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pokedex.team'),
        ),
    ]