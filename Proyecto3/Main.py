import os 
import librosa 
import pickle
import numpy as np
#import eyed3
import json 


directory = "canciones/data"

max_songs = 1
all_songs = []

# Recorre el directorio
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.lower().endswith(".mp3"):
            full_path = os.path.join(root, file)
            all_songs.append(full_path)

all_songs = all_songs[:max_songs]
print(f"Se encontraron {len(all_songs)} canciones en el dataset FMA.")


'''def obtener_metadatos_mp3(archivo):
    audio_file = eyed3.load(archivo)
    if audio_file.tag is not None:
        titulo = audio_file.tag.title
        #interprete = audio_file.tag.artist
        #album = audio_file.tag.album
        return {
            "titulo": titulo,
            #"interprete": interprete,
            #"album": album
        }
    else:
        return None'''


def normalizacion(vector):
    maximo = np.max(vector)
    minimo = np.min(vector)
    if maximo - minimo == 0:
        return np.zeros(vector.shape) # Evitar la división por cero 
    return (vector - minimo) / (maximo - minimo)


def extract_features_from_file(file_path):
    try:
        
        signal, sr = librosa.load(file_path, sr=None)

        # Calcula las características de la señal de audio
        mfccs = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=128)
        rmse = librosa.feature.rms(y=signal)
        zero_crossing = sum(librosa.zero_crossings(signal, pad=False))
        tempo = librosa.beat.tempo(y=signal, sr=sr)

        spectral_centroids = librosa.feature.spectral_centroid(y=signal, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=signal, sr=sr)[0]
        spectral_contrast = librosa.feature.spectral_contrast(y=signal, sr=sr)[0]
        spectral_flatness = librosa.feature.spectral_flatness(y=signal)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=signal, sr=sr)[0]

        # Normaliza las características calculadas
        mfccs = np.apply_along_axis(normalizacion, 1, mfccs)
        rmse = np.apply_along_axis(normalizacion, 1, rmse)
        spectral_centroids = normalizacion(spectral_centroids)
        spectral_bandwidth = normalizacion(spectral_bandwidth)
        spectral_contrast = normalizacion(spectral_contrast)
        spectral_flatness = normalizacion(spectral_flatness)
        spectral_rolloff = normalizacion(spectral_rolloff)

        # Retorna las características calculadas
        return {
            "mfccs": mfccs,
            "rmse": rmse,
            "zero_crossing": zero_crossing,
            "tempo": tempo[0],
            "spectral_centroids": spectral_centroids,
            "spectral_bandwidth": spectral_bandwidth,
            "spectral_contrast": spectral_contrast,
            "spectral_flatness": spectral_flatness,
            "spectral_rolloff": spectral_rolloff
        }
    except Exception as e:
        print(f"Error al procesar {file_path}: {e}")
        return None
    

# Extrae vectores para todas las canciones de FMA
vectors = []
for song_path in all_songs:
    print(f"Procesando {song_path}...")
    #PathDir = song_path.split("/")
    #metadatos = obtener_metadatos_mp3(song_path)
    features = extract_features_from_file(song_path)
    if features:
        vectors.append({"Path": song_path, "features": features})

print(f"Se procesaron {len(vectors)} canciones.")

'''# convertir a json [.tolist()]
with open("song_features_fma.json", "w") as f:
    json.dump(vectors, f, indent=4)
'''

# Pickle - guarda las características en un archivo binario
with open("song_features_fma.pkl", "wb") as f:
    pickle.dump(vectors, f)

print("Proceso terminado :D ")