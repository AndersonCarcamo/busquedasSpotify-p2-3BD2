import numpy as np
from rtree import index as rtree_index
from typing import Tuple, List


class KNN_RTree:
    def __init__(self, m: int, collection: List[Tuple[str, np.ndarray]]) -> None:
        p = rtree_index.Property()
        p.dimension = collection[0][1].shape[0]  # Número de dimensiones del vector MFCC
        p.buffering_capacity = m  # Capacidad de almacenamiento del nodo
        self.collection = collection
        self.idx = rtree_index.Index(properties=p)

        for i in range(len(collection)):
            coordinates = tuple(collection[i][1])
            self.idx.insert(id=i, coordinates=(coordinates + coordinates))  # Inserción en RTree

    def query(self, query_mfcc: np.ndarray, k: int) -> List[Tuple[str, float]]:
        coordinates = tuple(query_mfcc)
        if len(coordinates) == self.idx.properties.dimension:
            coordinates = coordinates + coordinates  # Duplicar coordenadas para RTree

        nearest = self.idx.nearest(coordinates, num_results=k)  # Consultar vecinos más cercanos
        result = []
        for item_id in nearest:
            obj = self.collection[item_id]
            result.append((obj[0], np.linalg.norm(obj[1] - query_mfcc)))  # Distancia Euclidiana
        return result
