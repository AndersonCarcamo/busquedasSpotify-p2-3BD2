import requests
import io
import librosa
import numpy as nps
import pickle

headers = {
    "Authorization": "Bearer BQBYQAdDTNfuemqBxr3AfRil18olpEoIupkh4aaE-oO-1X7HT2EldnK9bWszwg2iMGr26Aad3LHhAJd0sliVeA_jX5UyukvIKMYfTd4yrsQb57byIVs",
    "Content-Type": "application/json"
}

# Buscar artistas por género
url = "https://api.spotify.com/v1/search"
params = {
    "q": "pop",
    "type": "artist", 
    "limit": 5
}

# Realiza la solicitud
response = requests.get(url, headers=headers, params=params)
if response.status_code == 200:
    artists_data = response.json()
    artist_ids = [artist['id'] for artist in artists_data['artists']['items']]
    print(f"Se encontraron {len(artist_ids)} artistas populares.")
else:
    print(f"Error al buscar artistas: {response.status_code}")


#Extraer albunes de cada artista 
album_ids = []
for artist_id in artist_ids:
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {"market": "US", "limit": 5}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        albums_data = response.json()
        album_ids.extend([album['id'] for album in albums_data['items']])
    else:
        print(f"Error al obtener albumes del artista {artist_id}: {response.status_code}")

print(f"Se encontraron {len(album_ids)} albumes en total.")

#obtener cancion de cada album 
all_songs = []
for album_id in album_ids:
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    params = {"market": "US"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        tracks_data = response.json()
        for track in tracks_data['items']:
            if track['preview_url']:
                all_songs.append({
                    "name": track['name'],
                    "preview_url": track['preview_url']
                })
    else:
        print(f"Error al obtener canciones del album {album_id}: {response.status_code}")

print(f"Se encontraron {len(all_songs)} canciones")


def extract_features_from_url(preview_url):
    response = requests.get(preview_url)
    if response.status_code == 200:
        # Leer el audio desde la respuesta
        audio_data = io.BytesIO(response.content) # bytesIO es un buffer de lectura
        signal, sr = librosa.load(audio_data, sr=None)
        
        # Extraer características
        mfccs = librosa.feature.mfcc(y=signal, sr=sr, n_mfcc=20)
        rmse = librosa.feature.rms(y=signal)
        zero_crossing = sum(librosa.zero_crossings(signal, pad=False))
        tempo = librosa.beat.tempo(y=signal, sr=sr)

        spectral_centroids = librosa.feature.spectral_centroid(y=signal, sr=sr)[0]
        spectral_bandwidth=librosa.feature.spectral_bandwidth(y=signal, sr=sr)[0]
        spectral_contrast=librosa.feature.spectral_contrast(y=signal, sr=sr)[0]
        spectral_flatness=librosa.feature.spectral_flatness(y=signal)[0]
        spectral_rolloff=librosa.feature.spectral_rolloff(y=signal, sr=sr)[0]
        
        # Retorna las características calculadas
        return {
            "mfccs": mfccs,
            "rmse": rmse,
            "zero_crossing": zero_crossing,
            "tempo": tempo[0] , 
            "spectral_centroids": spectral_centroids,
            "spectral_bandwidth": spectral_bandwidth,
            "spectral_contrast": spectral_contrast,
            "spectral_flatness": spectral_flatness,
            "spectral_rolloff": spectral_rolloff
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


#Pickle - convierte los vectores en un archivo binario
with open("song_features.pkl", "wb") as f:  # wb: write binary
    pickle.dump(vectors, f)

print("Proceso terminado :D ")

