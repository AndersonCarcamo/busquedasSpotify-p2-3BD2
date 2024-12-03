import os
import librosa
import numpy as np
import pickle

# Ruta principal
base_path = '../../fma_medium'

# Función para extraer MFCC con promedio para reducir las caracteristicas a 1 dimension por caracteristicas
def extract_mfcc(file_path, n_mfcc=128):
    try:
        y, sr = librosa.load(file_path, sr=None)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        mfcc = np.mean(mfcc.T, axis=0)
        return mfcc
    except Exception as e:
        print(f"Error al procesar {file_path}: {e}")
        return None

# cada batch es un bloque en pkl (estrategia para en caso de cuelgues)
def save_features_in_batches(batch_data, batch_size=1000, batch_index=0):
    batch_filename = f"./batchs/mfcc_batch_{batch_index}.pkl"

    with open(batch_filename, 'wb') as f:
        pickle.dump(batch_data, f)
    print(f"Guardado lote {batch_index} con {len(batch_data)} características.")


def process_songs_in_batches(start_folder=0, end_folder=155, batch_size=1000):
    batch_data = []
    batch_index = 0

    for folder in range(start_folder, end_folder + 1):
        folder_path = os.path.join(base_path, f"{folder:03d}")

        if not os.path.exists(folder_path):
            continue

        for track_file in os.listdir(folder_path):
            track_path = os.path.join(folder_path, track_file)

            if track_file.endswith('.mp3') or track_file.endswith('.wav'):
                print(f"Procesando: {track_path}")

                mfcc = extract_mfcc(track_path)
                if mfcc is not None:
                    track_id = os.path.splitext(track_file)[0]
                    batch_data.append((track_id, mfcc))

                if len(batch_data) >= batch_size:
                    save_features_in_batches(batch_data, batch_size, batch_index)
                    batch_data = []
                    batch_index += 1

    if batch_data:
        save_features_in_batches(batch_data, batch_size, batch_index)

process_songs_in_batches()
