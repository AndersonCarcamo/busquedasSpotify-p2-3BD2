import os
import pickle
import numpy as np

# Ruta a los lotes
batch_folder = 'batchs2/'


def load_and_combine_batches(batch_folder):
    all_mfccs = []
    all_filenames = []

    for batch_file in os.listdir(batch_folder):
        if batch_file.endswith('.pkl'):
            batch_path = os.path.join(batch_folder, batch_file)
            print(f"Cargando {batch_path}...")

            with open(batch_path, 'rb') as f:
                batch_data = pickle.load(f)

                all_mfccs.extend(batch_data)

                all_filenames.extend(
                    [batch_file] * len(batch_data))

    all_mfccs = np.array(all_mfccs)

    return all_mfccs, all_filenames


def save_combined_features(all_mfccs, output_filename='combined_mfccs.pkl'):
    with open(output_filename, 'wb') as f:
        pickle.dump(all_mfccs, f)
    print(f"Características combinadas guardadas en {output_filename}")


all_mfccs, all_filenames = load_and_combine_batches(batch_folder)

save_combined_features(all_mfccs)
