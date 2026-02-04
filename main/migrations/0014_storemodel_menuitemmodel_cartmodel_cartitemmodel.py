# Generated migration for marketplace models

import django.db.models.deletion
import django_resized.forms
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_alter_logownermodel_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, verbose_name='Название торговой точки')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Дополнительная информация')),
                ('logo', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format=None, keep_meta=True, null=True, quality=-1, scale=1, size=[800, 800], upload_to='stores/logos/%Y/%m/%d/', verbose_name='Логотип')),
                ('currency', models.CharField(choices=[('руб.', 'Рубли'), ('EUR', 'Евро'), ('USD', 'Доллары')], default='руб.', max_length=10, verbose_name='Валюта')),
                ('read_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Read UUID')),
                ('write_uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Write UUID')),
            ],
            options={
                'verbose_name': 'Торговая точка',
                'verbose_name_plural': 'Торговые точки',
                'db_table': 'stores',
            },
        ),
        migrations.CreateModel(
            name='MenuItemModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, verbose_name='Название товара')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание товара')),
                ('photo', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format=None, keep_meta=True, null=True, quality=-1, scale=1, size=[1920, 1080], upload_to='stores/menu_items/%Y/%m/%d/', verbose_name='Фото товара')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu_items', to='main.storemodel')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'db_table': 'menu_items',
            },
        ),
        migrations.CreateModel(
            name='CartModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='carts', to='main.storemodel')),
            ],
            options={
                'verbose_name': 'Корзина',
                'verbose_name_plural': 'Корзины',
                'db_table': 'carts',
            },
        ),
        migrations.CreateModel(
            name='CartItemModel',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='main.cartmodel')),
                ('menu_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='main.menuitemmodel')),
            ],
            options={
                'verbose_name': 'Товар в корзине',
                'verbose_name_plural': 'Товары в корзине',
                'db_table': 'cart_items',
                'unique_together': {('cart', 'menu_item')},
            },
        ),
    ]
