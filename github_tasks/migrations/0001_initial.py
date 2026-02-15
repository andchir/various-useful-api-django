# Generated migration file for github_tasks app

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GitHubTask',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('issue_link', models.URLField(max_length=500, verbose_name='GitHub issue link')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('error', 'Error'), ('canceled', 'Canceled')], default='pending', max_length=20, verbose_name='Status')),
                ('owner', models.CharField(blank=True, max_length=200, null=True, verbose_name='Repository owner')),
                ('is_private', models.BooleanField(default=False, verbose_name='Is private repository')),
                ('tool', models.CharField(blank=True, max_length=200, null=True, verbose_name='Tool name')),
                ('model', models.CharField(blank=True, max_length=200, null=True, verbose_name='AI model name')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email for notifications')),
                ('telegram_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Telegram user ID for notifications')),
            ],
            options={
                'verbose_name': 'GitHub Task',
                'verbose_name_plural': 'GitHub Tasks',
                'db_table': 'github_tasks',
                'ordering': ['-date_created'],
            },
        ),
    ]
