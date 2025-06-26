import sounddevice as sd
import numpy as np
import wave
import openai
from eddie.config import API_KEY
import time
from eddie.log import get_logger
from eddie.evaluation import calculate_clarity_score, estimate_accuracy, get_system_usage

logger = get_logger()
audio_duration = None

def record_audio(filename, sure=5, fs=16000):
    """Ses kaydeder ve WAV formatında kaydeder."""
    global audio_duration
    start = time.time()
    
    try:
        
        print("Kayıt başladı...")
        data = sd.rec(int(sure * fs), samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(data)
        print(f"Kayıt tamamlandı: {filename}")
        
        audio_duration = (time.time() - start) * 1000
        clarity_score = calculate_clarity_score("voice.wav")
        system_usage = get_system_usage()

        logger.debug(
            "Audio recording successful.",
            extra={
                "operation" : "record_audio",
                "response_time" : audio_duration,
                "clarity_score" : clarity_score,
                "cpu": system_usage.get("cpu"),
                "memory": system_usage.get("memory"),
                "gpu": system_usage.get("gpu"),
                "status" : "SUCCESS"
            }
        )
        
    except Exception as e:
        duration = (time.time() - start) * 1000
        
        logger.error(
            f"Audio recording failed: {e}",
            extra={
                "operation" : "record_audio",
                "response_time" : duration,
                **system_usage,
                "status" : "FAILURE"
            }
        )
        print(f"Hata oluştu: {e}")

def sesi_metne_donustur(dosya_adi):
    """OpenAI Whisper API ile sesi metne çevirir."""
    client = openai.OpenAI(api_key=API_KEY)
    try:
        
        start = time.time()
        with open(dosya_adi, "rb") as f:
            response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language= "tr"
        )
        duration = (time.time() - start) * 1000
        accuracy_score = estimate_accuracy(response.text, duration)
        system_usage = get_system_usage()

        logger.debug(
            "STT conversion successful.",
            extra={
                "operation" : "sesi_metne_donustur",
                "response_time" : duration,
                "accuracy_score" : accuracy_score,
                "cpu": system_usage.get("cpu"),
                "memory": system_usage.get("memory"),
                "gpu": system_usage.get("gpu"),
                "status" : "SUCCESS"
            }
        )
            
        return response.text
        
    except Exception as e:
        duration = (time.time() - start) * 1000
        
        logger.error(
            f"STT conversion failed: {e}",
            extra={
                "operation" : "record_audio",
                "response_time" : duration,
                **system_usage,
                "status" : "FAILURE"
            }
        )
        print(f"Hata oluştu: {e}")
        return None
        

  
recording = False
recorded_data = []
fs = 16000
_channels = 1
_stream = None
start_time_gui = None

def _callback(indata, frames, time, status):

    global recorded_data
    if recording:
        recorded_data.append(indata.copy())



def start_recording():
    global recording, recorded_data, _stream,start_time_gui
    start_time_gui = time.time()
    try:
        
        print("🎙️ Kayıt başlatılıyor...")
        recorded_data = []
        recording = True
        _stream = sd.InputStream(
        samplerate=fs,
        channels=_channels,
        dtype='int16', 
        callback=_callback
        )
        _stream.start()
        print("🎙️ Stream başlatıldı.")
         
    except Exception as e:
        
        print(f"Hata oluştu: {e}")

def stop_recording(filename="voice.wav"):
    
    global recording, _stream,start_time_gui
  
    try:
                print("⛔ Kayıt durduruluyor...")
                recording = False
                if _stream:
                    _stream.stop()
                    _stream.close()
                if not recorded_data:
                    print("⚠️ Kayıt verisi alınamadı!")
                    return
                audio_data = np.concatenate(recorded_data)
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(_channels)
                    wf.setsampwidth(2) 
                    wf.setframerate(fs)
                    wf.writeframes(audio_data.tobytes())  
                print(f"💾 Kayıt kaydedildi: {filename}")

                duration = (time.time() - start_time_gui) * 1000
                clarity_score = calculate_clarity_score("voice.wav")
                system_usage = get_system_usage()

                logger.debug(
                        "GUI Audio recording successful.",
                        extra={
                            "operation" : "gui_record_audio",
                            "response_time" : duration,
                            "clarity_score" : clarity_score,
                            "cpu": system_usage.get("cpu"),
                            "memory": system_usage.get("memory"),
                            "gpu": system_usage.get("gpu"),
                            "status" : "SUCCESS"
                        }
                    )
                    
    except Exception as e:
                    duration = (time.time() - start_time_gui) * 1000
                    
                    logger.error(
                        f"GUI Audio recording failed: {e}",
                        extra={
                            "operation" : "gui_record_audio",
                            "response_time" : duration,
                            **system_usage,
                            "status" : "FAILURE"
                        }
                    )
                    print(f"Hata oluştu: {e}")