import numpy as np
import soundfile as sf
import psutil
import GPUtil

def compute_snr(audio_data):
    signal_power = np.mean(np.square(audio_data))
    noise_power = np.var(audio_data - np.mean(audio_data))
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def calculate_clarity_score(audio_path):
    data, _ = sf.read(audio_path)
    rms = np.sqrt(np.mean(data**2))
    snr = compute_snr(data)

    # Normalize: rms (0–1), snr (0–40 dB scale normalize)
    norm_rms = min(rms / 0.1, 1.0)
    norm_snr = min(snr / 40, 1.0)  # varsayılan üst limit

    combined_score = round((0.4 * norm_rms + 0.6 * norm_snr), 3)  # ağırlıklı ortalama
    return combined_score


def estimate_accuracy(text, duration):
    num_words = len(text.split())
    if duration < 1:
        return 0.0
    
    words_per_sec = num_words / duration

    if num_words == 0 or not is_output_meaningful(text):
        return 0.0
    elif words_per_sec < 0.5:
        return 0.3
    elif words_per_sec > 5:
        return 0.4
    else:
        return 0.8 + min(0.2, (3 - abs(2.5 - words_per_sec)) / 3)


def is_output_meaningful(text):
    return len(text.strip()) > 3 and not any(char.isdigit() for char in text)


def get_system_usage():
    # CPU kullanımı
    cpu_percent = psutil.cpu_percent(interval=1)

    # GPU kullanımı (varsa)
    gpus = GPUtil.getGPUs()
    gpu_percent = 0
    if gpus:
        gpu_percent = gpus[0].load * 100  # İlk GPU'nun kullanım yüzdesi

    # RAM kullanımı
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Dictionary olarak döndür
    return {
        "cpu": cpu_percent,
        "gpu": gpu_percent,
        "memory": memory_percent
    }