import os
import subprocess
from tempfile import NamedTemporaryFile
from elevenlabs import ElevenLabs
from pydub import AudioSegment
from pydub.playback import play
from elevenlabs import VoiceSettings
from openai import OpenAI
from eddie.config import ELEVENLABS_API_KEY,API_KEY
import time
from eddie.log import get_logger
from eddie.evaluation import calculate_clarity_score, get_system_usage
os.environ["FFMPEG_BINARY"] = os.path.join("executables", "ffmpeg.exe")
logger = get_logger()

def metni_sese_donustur(metin,motor):
    
   if motor == "ElevenLabs":
       _elevenlabs_tts(metin)
   elif motor == "OpenAI TTS":
       _openai_tts(metin)


def _elevenlabs_tts(metin):
    """Metni ElevenLabs kullanarak sese çevirir ve oynatır."""
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    try:
        
        start = time.time()
        audio = client.text_to_speech.convert(
            voice_id="7jNcYFFK9Ch5Szj4siVk",  # Emre Timur pre-made voice
            model_id="eleven_multilingual_v2",
            text=metin,

            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
                speed=1.0,
            ),
        )
        
        audio = b"".join(audio)
        
        with open("cevap.mp3", "wb") as f:
            f.write(audio)
            
        duration = (time.time() - start) * 1000
        clarity_score = calculate_clarity_score("cevap.mp3")
        system_usage = get_system_usage()

        logger.debug(
            "TTS conversion successful.",
            extra={
                "operation" : "metni_sese_donustur",
                "response_time" : duration,
                "clarity_score" : clarity_score,
                "cpu": system_usage.get("cpu"),
                "memory": system_usage.get("memory"),
                "gpu": system_usage.get("gpu"),
                "status" : "SUCCESS"
            }
        )

        with NamedTemporaryFile("w+b", suffix=".wav", delete=False) as temp_file:
            temp_file.close() 
            seg = AudioSegment.from_mp3('cevap.mp3')
            seg.export(temp_file.name, format="wav")

            subprocess.call(["ffplay", "-nodisp", "-autoexit", "-hide_banner", temp_file.name])
            
    except Exception as e:
        duration = (time.time() - start) * 1000
        system_usage = get_system_usage()
        logger.error(
            f"TTS conversion failed: {e}",
            extra={
                "operation" : "metni_sese_donustur",
                "response_time" : duration,
                **system_usage,
                "status" : "FAILURE"
            }
        )
        print(f"Hata oluştu: {e}")
        
def _openai_tts(metin):
    """ OpenAI’nin 'gpt-4o-mini-tts' modelini kullanarak metni sese çevirir ve oynatır."""
    client = OpenAI(api_key=API_KEY)
    
    try:
        start = time.time()
        
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="echo",
            input=metin,
            response_format="mp3"
        )
        
        response.stream_to_file("cevap.mp3")

        duration = (time.time() - start) * 1000
        clarity_score = calculate_clarity_score("cevap.mp3")
        system_usage = get_system_usage()
        
        logger.debug(
            "TTS conversion successful.",
            extra={
                "operation": "metni_sese_donustur",
                "response_time": duration,
                "clarity_score": clarity_score,
                "cpu": system_usage.get("cpu"),
                "memory": system_usage.get("memory"),
                "gpu": system_usage.get("gpu"),
                "status": "SUCCESS"
            }
        )

        with NamedTemporaryFile("w+b", suffix=".wav", delete=False) as temp_file:
            temp_file.close()
            seg = AudioSegment.from_mp3("cevap.mp3")
            seg.export(temp_file.name, format="wav")
            subprocess.call([
                "ffplay", "-nodisp", "-autoexit", "-hide_banner",
                temp_file.name
            ])

    except Exception as e:
        duration = (time.time() - start) * 1000
        system_usage = get_system_usage()
        logger.error(
            f"TTS conversion failed: {e}",
            extra={
                "operation": "metni_sese_donustur",
                "response_time": duration,
                **system_usage,
                "status": "FAILURE"
            }
        )
        print(f"Hata oluştu (OpenAI gpt-4o-mini-tts): {e}")