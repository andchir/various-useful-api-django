import os
import base64
import edge_tts
from datetime import datetime
from edge_tts import VoicesManager


async def edge_tts_find_voice(language=None, gender=None) -> None:
    voices = await VoicesManager.create()
    if language is None and gender is None:
        return voices.voices
    if gender is None:
        result = voices.find(Language=language)
    else:
        result = voices.find(Gender=gender.capitalize(), Language=language)
    return result


async def edge_tts_create_audio(text, voice_id, output_file_path) -> None:
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file_path)


def audio_to_base64(file_path):
    with open(file_path, 'rb') as binary_file:
        binary_file_data = binary_file.read()
        base64_encoded_data = base64.b64encode(binary_file_data)
        base64_output = base64_encoded_data.decode('utf-8')
    return base64_output


def delete_old_files(dir_path, max_hours=2):
    files_list = os.listdir(dir_path)
    now = datetime.now()
    deleted = 0
    for file in files_list:
        if not os.path.isfile(os.path.join(dir_path, file)):
            continue
        mtime = datetime.fromtimestamp(os.stat(os.path.join(dir_path, file)).st_mtime)
        diff = now - mtime
        if diff.total_seconds() / 60 / 60 > max_hours:
            os.remove(os.path.join(dir_path, file))
            deleted += 1
    return deleted
