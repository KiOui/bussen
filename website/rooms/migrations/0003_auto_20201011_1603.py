# Generated by Django 3.1.2 on 2020-10-11 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0002_auto_20201011_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='phase',
            field=models.IntegerField(choices=[(0, 'Open for participants'), (1, 'Phase 1'), (2, 'Phase 2'), (3, 'Phase 3')], default=1),
        ),
        migrations.AlterField(
            model_name='player',
            name='current_game',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rooms.game'),
        ),
    ]
