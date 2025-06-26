from eddie.audio import record_audio, sesi_metne_donustur
from eddie.chat import chatgpt_cevap
from eddie.tts import metni_sese_donustur
from eddie.sound_device_checker import check_microphone
from eddie.sound_device_checker import check_speaker
from eddie.report import load_data, generate_pdf_report
from os.path import expanduser, join
from eddie.sound_isolation import sound_isolation
def main():
    
    if not check_microphone():
        return
    
    if not check_speaker():
        return
    
    filename = "voice.wav"
    record_audio(filename, 5)
    sound_isolation()
    user_text = sesi_metne_donustur("clean.wav")
    print("Sen:", user_text)

    reply = chatgpt_cevap(user_text)
    print("AI:", reply)

    metni_sese_donustur(reply,"OpenAI TTS")
    
    log_dir = join(expanduser("~"), "EddieApp", "logs")
    log_path = join(log_dir, "system_log.jsonl")
    data = load_data(log_path)
    generate_pdf_report(data)


if __name__ == "__main__":
    main()