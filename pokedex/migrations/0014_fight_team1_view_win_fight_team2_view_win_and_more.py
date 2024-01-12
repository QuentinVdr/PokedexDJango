# Generated by Django 5.0 on 2024-01-12 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0013_fight_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='fight',
            name='team1_view_win',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fight',
            name='team2_view_win',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='fight',
            name='last_message',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
