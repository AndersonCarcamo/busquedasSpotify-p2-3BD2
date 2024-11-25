import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

def extract_features(audio_path):
    signal, sr = librosa.load(audio_path, sr=None)
    #MFCCS promedio
    mfccs = librosa.feature.mfcc(y=signal, sr=sr , n_mfcc=20)
    #Energia
    rmse = librosa.feature.rms(y=signal)
    #zero crossing rate
    Zero_crossing = sum(librosa.zero_crossings(signal, pad=False))
    #Tempo
    tempo = librosa.beat.tempo(y=signal, sr=sr)
    
    #Spectral features
    spectral_centroids = librosa.feature.spectral_centroid(y=signal, sr=sr)[0]
    spectral_bandwidth=librosa.feature.spectral_bandwidth(y=signal, sr=sr)[0]
    spectral_contrast=librosa.feature.spectral_contrast(y=signal, sr=sr)[0]
    spectral_flatness=librosa.feature.spectral_flatness(y=signal)[0]
    spectral_rolloff=librosa.feature.spectral_rolloff(y=signal, sr=sr)[0]
   
    features = {
        "rms": rmse,
        "zero_crossing_rate": Zero_crossing,
        "tempo": tempo,
        "mfccs": mfccs,
        "spectral_centroids": spectral_centroids,
        "spectral_bandwidth": spectral_bandwidth,
        "spectral_contrast": spectral_contrast,
        "spectral_flatness": spectral_flatness,
        "spectral_rolloff": spectral_rolloff
    }
    #return [rmse, Zero_crossing, tempo, mfccs, spectral_centroids, spectral_bandwidth, spectral_contrast, spectral_flatness, spectral_rolloff]
    return features


# Ruta del archivo
audio_path = 'Menu.mp3'
features = extract_features(audio_path)
for i , j  in features.items():
    print(j)