# Generated by Django 5.0 on 2023-12-16 17:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0005_fight'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pokemon',
            name='number',
        ),
        migrations.RemoveField(
            model_name='pokemon',
            name='team',
        ),
        migrations.CreateModel(
            name='TeamPokemon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('pokemon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pokedex.pokemon')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pokedex.team')),
            ],
        ),
    ]
