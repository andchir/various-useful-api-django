# Generated by Django 5.0 on 2024-10-02 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_logitemmodel_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='logownermodel',
            name='site_url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
