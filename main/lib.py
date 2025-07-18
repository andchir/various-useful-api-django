import os
import base64
import uuid
import edge_tts
from datetime import datetime
from edge_tts import VoicesManager
from babel import Locale
from urllib.parse import urlparse
import mimetypes
import yadisk


async def edge_tts_find_voice(language=None, gender=None):
    voices = await VoicesManager.create()
    if language is None and gender is None:
        return voices.voices
    if gender is None:
        result = voices.find(Language=language)
    else:
        result = voices.find(Gender=gender.capitalize(), Language=language)
    return result


async def edge_tts_create_audio(text, voice_id, output_file_path):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file_path)


def lists_to_dict(list_keys, list_values):
    res = {}
    for index, val in enumerate(list_keys):
        res[list_keys[index]] = list_values[index]
    return res


def create_lang_list(list_keys, list_values):
    res = []
    for index, val in enumerate(list_keys):
        code = list_keys[index].split('-')[0]
        res.append({'name': list_values[index], 'locale': list_keys[index], 'code': code})
    return res


async def edge_tts_locales():
    lang_locales = []
    lang_names = []
    voices = await VoicesManager.create()
    for voice in voices.voices:
        if voice['Locale'] in lang_locales:
            continue
        lang_locales.append(voice['Locale'])
        tmp = voice['Locale'].split('-')
        try:
            locale = Locale(tmp[0], tmp[1])
            lang_name = locale.display_name
        except Exception as e:
            lang_name = voice['Locale']
        lang_names.append(lang_name)
    return create_lang_list(lang_locales, lang_names)


def audio_to_base64(file_path):
    with open(file_path, 'rb') as binary_file:
        binary_file_data = binary_file.read()
        base64_encoded_data = base64.b64encode(binary_file_data)
        base64_output = base64_encoded_data.decode('utf-8')
    return base64_output


def delete_old_files(dir_path, max_hours=2, print_time=False):
    files_list = os.listdir(dir_path)
    now = datetime.now()
    deleted = 0
    for file in files_list:
        if not os.path.isfile(os.path.join(dir_path, file)):
            continue
        file_stat = os.stat(os.path.join(dir_path, file))
        mtime = datetime.fromtimestamp(max(file_stat.st_ctime, file_stat.st_mtime))
        diff = now - mtime
        if print_time:
            print('----------------------------------')
            print(file, mtime)
            print('diff_seconds:', diff.total_seconds())
            print('diff_hours:', diff.total_seconds() / 60 / 60)
            print('----------------------------------')
        if diff.total_seconds() / 60 / 60 > max_hours:
            os.remove(os.path.join(dir_path, file))
            deleted += 1
    return deleted


def upload_and_share_yadisk(file_path, dir_path, yadisk_token):
    client = yadisk.Client(token=yadisk_token)
    with client:
        if not client.check_token():
            # TODO: use refresh_token()
            return None, None, 'YandexDisk token is invalid.'

        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1]

        if extension in ['.mp4', '.3gp', '.avi']:
            result = client.upload(file_path, str(os.path.join(dir_path, base_name.replace(extension, ''))), overwrite=True, timeout=3600)
            result = client.rename(result.path, base_name, overwrite=True)
        else:
            result = client.upload(file_path, f'{dir_path}/{base_name}', overwrite=True, timeout=3600)

        if result is None or not hasattr(result, 'path'):
            return None, None, 'Failed to upload file.'

        # print(f'Uploaded {base_name} to {dir_path}.')

        result = client.publish(result.path)

        if result is None or not hasattr(result, 'path'):
            return None, None, 'Failed to upload file.'

        # print(f'Published!')

        meta = client.get_meta(result.path)
        # print(meta)

        return meta.file, meta.public_url, ''


def is_internal_url(url, request):
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        return True

    server_domain = request.get_host()
    return parsed_url.netloc == server_domain


def get_safe_filename(url, content_type, response_headers):
    content_disposition = response_headers.get('Content-Disposition', '')
    if 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"\'')
        if filename:
            return filename

    url_path = urlparse(url).path
    filename = os.path.basename(url_path) if url_path else None

    if not filename or '.' not in filename:
        ext = mimetypes.guess_extension(content_type.split(';')[0].strip()) or '.txt'
        filename = f'file_{uuid.uuid4().hex[:8]}{ext}'

    filename = ''.join(c for c in filename if c.isalnum() or c in ('.', '-', '_'))
    return filename[:255]

