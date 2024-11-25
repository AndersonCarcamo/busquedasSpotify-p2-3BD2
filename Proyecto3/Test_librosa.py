import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import requests
import io

def extract_features_from_url(preview_url):
    # Descargamos el archivo de audio desde la URL
    response = requests.get(preview_url)
    
    # Verificamos que la respuesta sea exitosa
    if response.status_code == 200:
        # Cargamos el contenido de la respuesta en formato de audio con librosa
        audio_data = io.BytesIO(response.content)
        signal, sr = librosa.load(audio_data, sr=None)
        
        # Extraemos las características de la canción
        mfccs = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=20)
        rmse = librosa.feature.rms(y=signal)
        Zero_crossing = sum(librosa.zero_crossings(signal, pad=False))
        tempo, _ = librosa.beat.beat_track(y=signal, sr=sr)
        
        spectral_centroids = librosa.feature.spectral_centroid(y=signal, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=signal, sr=sr)[0]
        spectral_contrast = librosa.feature.spectral_contrast(y=signal, sr=sr)[0]
        spectral_flatness = librosa.feature.spectral_flatness(y=signal)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=signal, sr=sr)[0]
        
        # Regresa las características como una lista
        return [mfccs, rmse, Zero_crossing, tempo, spectral_centroids, spectral_bandwidth, spectral_contrast, spectral_flatness, spectral_rolloff]
    else:
        print("Error al descargar el audio:", response.status_code)
        return None

# Ruta del archivo
preview_url = "https://p.scdn.co/mp3-preview/2b3b9bf5c1c8b7192e4b535f7af11301d1f521af?cid=84ca09cf880140549348915d17384e57"
features = extract_features_from_url(preview_url)
if features:
    print(features)