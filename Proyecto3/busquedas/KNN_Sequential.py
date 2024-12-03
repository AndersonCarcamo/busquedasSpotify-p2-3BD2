import numpy as np
from typing import List, Tuple
import heapq


# Clase que representa un nodo con distancia y track_id
class DistanceNode:
    def __init__(self, distance: float, track_id: str):
        self.distance = distance
        self.track_id = track_id

    def __lt__(self, other):
        return self.distance > other.distance  # Para ordenar de menor a mayor distancia

    def __eq__(self, other):
        return self.distance == other.distance

    def __repr__(self) -> str:
        return str((self.track_id, self.distance))


# Clase para manejar el heap de manera optimizada
class OptimizedHeap:
    def __init__(self):
        self.heap = []

    def push(self, node: DistanceNode):
        heapq.heappush(self.heap, node)

    def pop(self) -> DistanceNode:
        return heapq.heappop(self.heap)

    def replace_top(self, node: DistanceNode):
        heapq.heapreplace(self.heap, node)

    def top(self) -> DistanceNode:
        return self.heap[0]

    def size(self) -> int:
        return len(self.heap)

    def heapsort(self) -> List[DistanceNode]:
        return sorted(self.heap, key=lambda x: x.distance)  # Ordenar el heap por distancia


# Implementación de KNN Secuencial
class KNN_Sequential:
    def __init__(self, collection: List[Tuple[str, np.ndarray]]) -> None:
        self.collection = collection

    def knn_heap_query(self, query_mfcc: np.ndarray, k: int) -> List[Tuple[str, float]]:
        result_heap = OptimizedHeap()  # Inicializar el heap optimizado

        for track_id, mfcc in self.collection:
            dist = np.linalg.norm(mfcc - query_mfcc)  # Distancia Euclidiana
            node = DistanceNode(distance=dist, track_id=track_id)

            if result_heap.size() < k:
                result_heap.push(node)
            elif result_heap.top().distance > dist:
                result_heap.replace_top(node)

        return [(node.track_id, node.distance) for node in result_heap.heapsort()]  # Devolver los k más cercanos

    def range_query(self, query_mfcc: np.ndarray, r: float) -> List[Tuple[str, float]]:
        result = []
        for track_id, mfcc in self.collection:
            dist = np.linalg.norm(mfcc - query_mfcc)  # Distancia Euclidiana
            if dist <= r:
                result.append((track_id, dist))
        return result
