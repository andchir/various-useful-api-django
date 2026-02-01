# Various useful APIs

Various useful APIs for api2app.ru.

![screenshot #1](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/001.png?raw=true "Screenshot #1")
![screenshot #2](https://github.com/andchir/price-monitoring-django/blob/main/screenshots/002.png?raw=true "Screenshot #2")

## API Endpoints

| Description | Group | URL |
|-------------|-------|-----|
| Users management (CRUD operations) | Users | `/api/v1/users` |
| Groups management (CRUD operations) | Users groups | `/api/v1/groups` |
| Products monitoring (CRUD operations) | Price monitoring | `/api/v1/products` |
| List product names | Price monitoring | `/api/v1/products/list_names` |
| List cities | Price monitoring | `/api/v1/products/list_cities` |
| List shop names | Price monitoring | `/api/v1/products/list_shop_names` |
| Log owners management (CRUD operations) | Logging | `/api/v1/log_owners` |
| Log items management (CRUD operations) | Logging | `/api/v1/log` |
| Create log record | Logging | `/api/v1/create_log_record` |
| Create log record by UUID | Logging | `/api/v1/create_log_record/<owner_uuid>` |
| Get video information (yt-dlp) | YouTube | `/api/v1/yt_dlp` |
| Get video information (pytube) | YouTube | `/api/v1/youtube_dl` |
| Download video from YouTube | YouTube | `/api/v1/youtube_dl/download` |
| List Google Translate languages | GoogleTransTTS | `/api/v1/googletrans_languages_list` |
| Translate text | GoogleTransTTS | `/api/v1/googletrans_translate` |
| List Google TTS languages | GoogleTransTTS | `/api/v1/google_tts_languages_list` |
| Generate speech from text (gTTS) | GoogleTransTTS | `/api/v1/google_tts` |
| List all available voices | EdgeTTS | `/api/v1/edge_tts_voices_list` |
| List voices by language | EdgeTTS | `/api/v1/edge_tts_voices_list_by_lang/<language>` |
| List available languages | EdgeTTS | `/api/v1/edge_tts_languages_list` |
| Generate speech from text (edge-tts) | EdgeTTS | `/api/v1/edge_tts/<voice_id>` |
| Password generator | Other | `/api/v1/password_generate` |
| Fact-checking explorer | FactCheckExplorer | `/api/v1/fact_check_explorer` |
| Upload and share files on YandexDisk | YandexDisk | `/api/v1/upload_and_share_yadisk` |
| YandexCloud Assistant integration | YandexGPT | `/api/v1/yandexgpt_assistant` |
| Get Coggle diagram node data | Coggle | `/api/v1/coggle_nodes/<diagram_id>/<node_id>` |
| Create and store embeddings | OpenAI Embeddings | `/api/v1/store_create` |
| Query stored embeddings | OpenAI Embeddings | `/api/v1/store_question` |
| Extract frame from video | Video | `/api/v1/extract_video_frame` |
| Replace or add audio track to video | Video | `/api/v1/replace_video_audio` |
| Trim video segment | Video | `/api/v1/trim_video` |
| Concatenate multiple videos | Video | `/api/v1/concatenate_videos` |
| Create website screenshot | Screenshot | `/api/v1/website_screenshot` |
| Generate widget embed code for chat integration | Widget | `/api/v1/widget_embed_code` |
| Generate QR code from text or URL | QR Code Generator | `/api/v1/qr_code_generator` |
| Extract text from images using OCR | OCR Text Recognition | `/api/v1/ocr_text_recognition` |
| Convert currencies | Currency Converter | `/api/v1/currency_converter` |
| Get weather information | Weather API | `/api/v1/weather` |
| Check text similarity/plagiarism | Plagiarism Checker | `/api/v1/plagiarism_checker` |

### CSS Tools
- SVG to CSS background-image URL converter
- CSS gradient generator (linear, radial, conic)
- CSS box-shadow generator
- CSS transform generator (rotate, scale, translate, skew)
- CSS animation/keyframes generator
- CSS filter effects generator (blur, brightness, contrast, etc.)

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
