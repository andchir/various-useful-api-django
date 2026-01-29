# Various useful APIs

Various useful APIs for api2app.ru.

![screenshot #1](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/001.png?raw=true "Screenshot #1")
![screenshot #2](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/002.png?raw=true "Screenshot #2")

## API Endpoints

### Price monitoring
- Products monitoring (CRUD operations)
- List product names
- List cities
- List shop names

### Logging
- Log owners management (CRUD operations)
- Log items management (CRUD operations)
- Create log record

### YouTube
- Get video information (yt-dlp)
- Get video information (pytube)
- Download video from YouTube

### Google Translate & TTS
- List Google Translate languages
- Translate text
- List Google TTS languages
- Generate speech from text (gTTS)

### Microsoft Edge TTS
- List all available voices
- List voices by language
- List available languages
- Generate speech from text (edge-tts)

### Other
- Password generator

### FactCheckExplorer
- Fact-checking explorer (https://github.com/GONZOsint/factcheckexplorer)

### YandexDisk
- Upload and share files on YandexDisk

### YandexGPT
- YandexCloud Assistant integration (https://yandex.cloud/ru/docs/foundation-models/operations/assistant/create-with-searchindex)

### Coggle
- Get Coggle diagram node data

### OpenAI Embeddings
- Create and store embeddings
- Query stored embeddings

### Video Processing
- Extract frame from video
- Replace or add audio track to video
- Trim video segment
- Concatenate multiple videos

### Widget
- Generate widget embed code for chat integration

## Installation and management

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
sudo nano /etc/systemd/system/various-useful-apis.service
sudo nano /etc/systemd/system/various-useful-apis.socket

systemctl daemon-reload
~~~

Enable and start the socket (it will autostart at boot too):
~~~
sudo systemctl start various-useful-apis.socket
sudo systemctl enable various-useful-apis.socket

sudo service various-useful-apis start
~~~

Commands:
~~~
./manage.py site_monitoring --uuid=4217211a-80e5-11ef-b5ed-9fe997cb3299
./manage.py site_monitoring_log --uuid=4217211a-80e5-11ef-b5ed-9fe997cb3299

*/3 * * * * /home/andrew/python_projects/site_monitoring/venv/bin/python /home/andrew/python_projects/site_monitoring/manage.py site_monitoring > /dev/null
~~~
