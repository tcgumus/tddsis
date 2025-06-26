from os import path
import numpy as np
import librosa
import matplotlib.pyplot as plt
import soundfile as sf
import scipy.fftpack as fft
from scipy.signal import medfilt


def sound_isolation():
    y, sr = librosa.load('voice.wav', sr=None)
    S_full, phase = librosa.magphase(librosa.stft(y))
    noise_power = np.mean(S_full[:, :int(sr*0.1)], axis=1)
    mask = S_full > noise_power[:, None]
    mask = mask.astype(float)
    mask = medfilt(mask, kernel_size=(1, 5))
    S_clean = S_full * mask
    Y_clean = librosa.istft(S_clean * phase)
    sf.write('clean.wav', Y_clean, sr)