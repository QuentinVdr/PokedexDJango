# Generated by Django 5.0 on 2023-12-07 13:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pokemon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pokemon_api_id', models.IntegerField()),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('money', models.IntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Person',
        ),
        migrations.AddField(
            model_name='pokemon',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pokedex.team'),
        ),
        migrations.AddField(
            model_name='team',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pokedex.userprofile'),
        ),
        migrations.AddField(
            model_name='pokemon',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pokedex.userprofile'),
        ),
    ]
