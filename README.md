# Various useful APIs

Various useful APIs for api2app.ru.

![screenshot #1](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/001.png?raw=true "Screenshot #1")
![screenshot #2](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/002.png?raw=true "Screenshot #2")

- API for monitoring changes in prices for products.
- Logging - testing webhooks.
- Downloading videos from YouTube (pytube and yt-dlp).
- Unlimited Microsoft Text-to-Speech (edge-tts)
- Password generator
- FactCheckExplorer (https://github.com/GONZOsint/factcheckexplorer)
- Unlimited Google Translate (googletrans)
- Unlimited Google Text-to-Speech (gTTS)
- Use YandexCloud Assistant (https://yandex.cloud/ru/docs/foundation-models/operations/assistant/create-with-searchindex)
- Coggle node API.

Create superuser:
~~~
python manage.py createsuperuser
~~~

Migrations:
~~~
python manage.py makemigrations
python manage.py migrate
~~~

Run server in development mode:
~~~
python manage.py runserver
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

Commands:
~~~
./manage.py site_monitoring --uuid=4217211a-80e5-11ef-b5ed-9fe997cb3299
./manage.py site_monitoring_log --uuid=4217211a-80e5-11ef-b5ed-9fe997cb3299

*/3 * * * * /home/andrew/python_projects/site_monitoring/venv/bin/python /home/andrew/python_projects/site_monitoring/manage.py site_monitoring > /dev/null
~~~
