# price-monitoring-django

Create super user:
~~~
python manage.py createsuperuser
~~~

Migrations:
~~~
python manage.py makemigrations
python manage.py migrate
~~~

# Deploy
~~~
sudo nano /etc/systemd/system/price-monitoring.service
sudo nano /etc/systemd/system/price-monitoring.socket
~~~

Enable and start the socket (it will autostart at boot too):
~~~
sudo systemctl start price-monitoring.socket
sudo systemctl enable price-monitoring.socket
~~~
