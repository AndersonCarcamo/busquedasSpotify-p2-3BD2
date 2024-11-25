import requests
import io
import librosa
import json
import numpy as np


headers = {
    "Authorization": "BQCDLOECS-Ct-qHQ5zrM8gmvXK7SkIQJaI73ugJLF52FIPuwzCnCna3yFAXFH0RjT-jCy4TsIk4mYd4cqhKArfB8VYWlTB6Z4sE1lyFsLdwmiG35JrU",
    "Content-Type": "application/json"
}


artist_id = "3TVXtAsR1Inumwj472S9r4"  # Ejemplo: Drake
url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"

# Define parámetros adicionales
params = {
    "market": "US",
    "limit": 50,  # Máximo número de álbumes por solicitud
    "offset": 0   # Desplazamiento para paginación
}

# Realiza la solicitud
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    albums_data = response.json()
    album_ids = [album['id'] for album in albums_data['items']]
    print(f"Se encontraron {len(album_ids)} álbumes del artista.")
else:
    print(f"Error al obtener los álbumes: {response.status_code}")



# Endpoint base para obtener las pistas de un álbum
track_url = "https://api.spotify.com/v1/albums/{id}/tracks"

# Inicializa una lista para almacenar las URLs de las canciones
all_songs = []

for album_id in album_ids:
    # Solicita las canciones de cada álbum
    response = requests.get(track_url.format(id=album_id), headers=headers, params={"market": "US"})
    if response.status_code == 200:
        tracks_data = response.json()
        for track in tracks_data['items']:
            if 'preview_url' in track and track['preview_url']:
                all_songs.append({
                    "name": track['name'],
                    "preview_url": track['preview_url']
                })
    else:
        print(f"Error al obtener canciones del álbum {album_id}: {response.status_code}")

# Muestra cuántas canciones se encontraron
print(f"Se encontraron {len(all_songs)} canciones con URLs de vista previa.")


def extract_features_from_url(preview_url):
    response = requests.get(preview_url)
    if response.status_code == 200:
        # Leer el audio desde la respuesta
        audio_data = io.BytesIO(response.content)
        signal, sr = librosa.load(audio_data, sr=None)
        
        # Extraer características
        mfccs = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=13)
        rmse = librosa.feature.rms(y=signal)
        zero_crossing = sum(librosa.zero_crossings(signal, pad=False))
        tempo = librosa.beat.tempo(y=signal, sr=sr)
        
        # Retorna las características calculadas
        return {
            "mfccs": mfccs.mean(axis=1).tolist(),
            "rmse": rmse.mean(),
            "zero_crossing": zero_crossing,
            "tempo": tempo[0]
        }
    else:
        print(f"Error al obtener el audio desde la URL: {response.status_code}")
        return None

# Extrae vectores para todas las canciones
vectors = []
for song in all_songs:
    print(f"Procesando {song['name']}...")
    features = extract_features_from_url(song['preview_url'])
    if features:
        vectors.append({"name": song["name"], "features": features})

print(f"Se procesaron {len(vectors)} canciones.")


# Función personalizada para convertir datos no serializables
def custom_serializer(obj):
    if isinstance(obj, (np.ndarray, list)):
        return obj.tolist()
    elif isinstance(obj, np.float32):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# Guarda los vectores en un archivo JSON
with open("song_features.json", "w") as f:
    json.dump(vectors, f, default=custom_serializer)

print("Vectores guardados exitosamente en song_features.json.")

