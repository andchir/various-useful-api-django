import edge_tts
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
