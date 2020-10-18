# Generated by Django 3.1.2 on 2020-10-11 12:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('state', models.JSONField()),
                ('phase', models.IntegerField(choices=[(1, 'Phase 1'), (2, 'Phase 2'), (3, 'Phase 3')], default=1)),
                ('current_player', models.IntegerField()),
                ('slug', models.SlugField(max_length=256, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Hand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hand', models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cookie', models.CharField(max_length=32)),
                ('name', models.CharField(max_length=32)),
                ('online', models.BooleanField(default=True)),
                ('current_game', models.ForeignKey(default=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rooms.game')),
                ('current_hand', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rooms.hand')),
            ],
        ),
    ]