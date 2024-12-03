import faiss
import numpy as np
from typing import List, Tuple


class KNN_HighD:
    def __init__(self, num_bits: int, collection: List[Tuple[str, np.ndarray]]) -> None:
        self.collection = collection
        d = collection[0][1].shape[0]  # Dimensiones del vector MFCC
        self.index = faiss.IndexLSH(d, num_bits)  # Creación del índice LSH de FAISS
        self.index.add(np.ascontiguousarray(np.asarray([i[1] for i in self.collection], dtype="float32")))

    def knn_query(self, query_mfcc: np.ndarray, k: int) -> List[Tuple[str, float]]:
        query_mfcc = np.asarray([query_mfcc], dtype="float32")
        ranking, id_array = self.index.search(query_mfcc, k)  # Búsqueda en el índice

        result: List[Tuple[str, float]] = []
        for idx in id_array[0]:
            if idx == -1:
                continue
            obj = self.collection[idx]
            dist = np.linalg.norm(obj[1] - query_mfcc[0])  # Distancia Euclidiana
            result.append((obj[0], dist))
        return sorted(result, key=lambda x: x[1])  # Ordenar por distancia
