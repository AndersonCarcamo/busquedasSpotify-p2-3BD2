import pandas as pd
import pickle

from busquedas.KNN_HighD import *
import os
import librosa
import numpy as np
import time
from sklearn.decomposition import PCA

# se ha creado en otro enviroment por problemas con las librerias

batchs_path = 'extractFeatures/batchs/'

def load_features_vectors(bath_folder):
    global_feature_vectors = []

    for file_name in os.listdir(bath_folder):
        if file_name.endswith('.pkl'):
            file_path = os.path.join(bath_folder, file_name)

            with open(file_path, 'rb') as f:
                try:
                    batch_data = pickle.load(f)

                    if isinstance(batch_data, list):
                        for track_id, features_vector in batch_data:
                            global_feature_vectors.append((track_id, features_vector))
                except Exception as e:
                    print(f'Error loading {file_path}: {e}')
    return global_feature_vectors

def apply_pca_to_collection(collection, n_components):
    features = np.array([i[1] for i in collection], dtype=np.float32)
    pca = PCA(n_components=n_components)
    reduced_features = pca.fit_transform(features)
    return [(collection[i][0], reduced_features[i]) for i in range(len(collection))]


diccionario_global = load_features_vectors(batchs_path)

dic_1000 = diccionario_global[:1000]
dic_5000 = diccionario_global[:5000]
dic_10000 = diccionario_global[:10000]
dic_20000 = diccionario_global[:20000]
dic_all = diccionario_global

nro_componentes = 28
dic_1000_pca = apply_pca_to_collection(dic_1000, nro_componentes)
dic_5000_pca = apply_pca_to_collection(dic_5000, nro_componentes)
dic_10000_pca = apply_pca_to_collection(dic_10000, nro_componentes)
dic_20000_pca = apply_pca_to_collection(dic_20000, nro_componentes)
dic_all_pca = apply_pca_to_collection(dic_all, nro_componentes)


query_path = 'fma_medium/037/037156.mp3'

y, sr = librosa.load(query_path, sr=None)
mfcc_query_features = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=128)
mfcc_query_features = np.mean(mfcc_query_features.T, axis=0)

# para la reduccion de la query
features = np.array([i[1] for i in dic_all], dtype=np.float32)
pca = PCA(n_components=nro_componentes)
pca.fit(features) 
mfcc_query_features_pca = pca.transform([mfcc_query_features])[0]

# test para bits optimos
results_for_bit_knnHighD = {}
bits = [8, 16, 32, 64, 128, 256, 512]

for bit in bits:
    total_time = 0
    knn_highd = KNN_HighD(bit, dic_all)
    for  _ in range(5):
        start = time.time()
        knn_highd.knn_query(mfcc_query_features, 10)
        end = time.time()
        total_time += (end - start)
    results_for_bit_knnHighD[f'knnHighD_for_{bit}_bits'] = total_time/5

sorted_results = sorted(results_for_bit_knnHighD.items(), key=lambda x: x[1])

print("Resultados ordenados por tiempo promedio:")
print(sorted_results)

knn_highd_1000 = KNN_HighD(128, dic_1000)
knn_highd_5000 = KNN_HighD(128, dic_5000)
knn_highd_10000 = KNN_HighD(128, dic_10000)
knn_highd_20000 = KNN_HighD(128, dic_20000)
knn_highd_all = KNN_HighD(128, dic_all)

result_knn_HighD = {}
list_knn_HighD = [knn_highd_1000, knn_highd_5000, knn_highd_10000, knn_highd_20000, knn_highd_all]
long_test = [1000, 5000, 10000, 20000, len(dic_all)]

for idx, knn_highd in enumerate(list_knn_HighD):
    result = 0
    for _ in range(5):
        start = time.time()
        result_query = knn_highd.knn_query(mfcc_query_features, 10)
        end = time.time()
        # print(result_query)
        result += (end - start)
    result_knn_HighD[f'knnHighD_{long_test[idx]}'] = result / 5

print('------------------------')
print(result_knn_HighD)

knn_highd_1000_pca = KNN_HighD(128, dic_1000_pca)
knn_highd_5000_pca = KNN_HighD(128, dic_5000_pca)
knn_highd_10000_pca = KNN_HighD(128, dic_10000_pca)
knn_highd_20000_pca = KNN_HighD(128, dic_20000_pca)
knn_highd_all_pca = KNN_HighD(128, dic_all_pca)

result_knn_HighD_pca = {}
list_knn_HighD_pca = [knn_highd_1000_pca, knn_highd_5000_pca, knn_highd_10000_pca, knn_highd_20000_pca, knn_highd_all_pca]

for idx, knn_highd in enumerate(list_knn_HighD_pca):
    result = 0
    for _ in range(5):
        start = time.time()
        result_query = knn_highd.knn_query(mfcc_query_features_pca, 10)
        end = time.time()
        # print(result_query)
        result += (end - start)
    result_knn_HighD_pca[f'knnHighD_{long_test[idx]}_pca'] = result / 5

print('------------------------')
print(result_knn_HighD_pca)
