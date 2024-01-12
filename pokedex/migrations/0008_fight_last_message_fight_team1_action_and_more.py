# Generated by Django 5.0 on 2024-01-11 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0007_alter_fight_team2'),
    ]

    operations = [
        migrations.AddField(
            model_name='fight',
            name='last_message',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='fight',
            name='team1_action',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='fight',
            name='team1_life',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fight',
            name='team1_pokemon_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fight',
            name='team2_life',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='fight',
            name='team2_pokemon_number',
            field=models.IntegerField(default=0),
        ),
    ]