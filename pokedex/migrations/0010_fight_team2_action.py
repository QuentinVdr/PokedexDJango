# Generated by Django 5.0 on 2024-01-11 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0009_alter_fight_last_message_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fight',
            name='team2_action',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
