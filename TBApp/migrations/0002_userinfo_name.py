# Generated by Django 3.0.5 on 2024-08-22 03:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TBApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='name',
            field=models.CharField(default=None, max_length=100),
        ),
    ]
