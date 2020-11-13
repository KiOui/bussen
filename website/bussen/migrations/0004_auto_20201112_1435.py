# Generated by Django 3.1.2 on 2020-11-12 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bussen', '0003_auto_20201108_1507'),
    ]

    operations = [
        migrations.AddField(
            model_name='hand',
            name='game',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='bussen.busgamemodel'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='busgamemodel',
            name='current_player_index',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='busgamemodel',
            name='phase',
            field=models.IntegerField(choices=[(0, 'Phase 1'), (1, 'Phase 2'), (2, 'Phase 3'), (3, 'Finished')], default=0),
        ),
    ]
