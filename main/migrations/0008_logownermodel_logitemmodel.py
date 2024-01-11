# Generated by Django 5.0 on 2024-01-11 12:17

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_imagemodel_image_alter_imagemodel_thumbnail'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogOwnerModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=200)),
                ('uuid', models.UUIDField(default=uuid.uuid1, editable=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Log owner',
                'db_table': 'log_owners',
            },
        ),
        migrations.CreateModel(
            name='LogItemModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('data', models.JSONField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_items', to='main.logownermodel')),
            ],
            options={
                'verbose_name': 'Log',
                'db_table': 'log',
            },
        ),
    ]