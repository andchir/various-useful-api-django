# Various useful APIs

API for monitoring changes in prices for products.

![screenshot #1](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/001.png?raw=true "Screenshot #1")
![screenshot #2](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/002.png?raw=true "Screenshot #2")

Create superuser:
~~~
python manage.py createsuperuser
~~~

Migrations:
~~~
python manage.py makemigrations
python manage.py migrate
~~~

Copy all files from static folders into the STATIC_ROOT directory:
~~~
python manage.py collectstatic
~~~

Generate API schema:
~~~
python manage.py spectacular --color --file schema.yml
~~~

API schema URLs:
~~~
/api/schema/swagger-ui/
/api/schema/redoc/
~~~

Deploy:
~~~
sudo nano /etc/systemd/system/price-monitoring.service
sudo nano /etc/systemd/system/price-monitoring.socket
~~~

Enable and start the socket (it will autostart at boot too):
~~~
sudo systemctl start price-monitoring.socket
sudo systemctl enable price-monitoring.socket
~~~
