import numpy as np
import heapq
from typing import Any
from imageio.v3 import imread


class PQueue:
    def __init__(self):
        self.heap = []
        self.entries = {}

    def push(self, p: float, v: Any):
        if v in self.entries:
            self.entries[v][2] = False
        entry = [p, v, True]
        self.entries[v] = entry
        heapq.heappush(self.heap, (p, entry))

    def pop(self) -> tuple[float, Any]:
        while self.heap:
            p, entry = heapq.heappop(self.heap)
            if entry[2]:
                del self.entries[entry[1]]
                return p, entry[1]
        raise IndexError("pop from an empty queue")

    def empty(self) -> bool:
        return len(self.entries) == 0


def propagation(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rows, cols = img.shape
    D = np.full((rows, cols), 1e10, dtype=np.float64)

    q = PQueue()
    for (row, col) in np.argwhere(mask > 0):
        D[row, col] = 0.0
        q.push(0.0, (row, col))

    neighbors = [(-1, 0), (1, 0), (0, 1), (0, -1),
                 (-1, -1), (-1, 1), (1, -1), (1, 1)]

    while not q.empty():
        dist, (row, col) = q.pop()
        for dr, dc in neighbors:
            nrow, ncol = row + dr, col + dc
            if 0 <= nrow < rows and 0 <= ncol < cols:
                new_dist = dist + abs(float(img[nrow, ncol]) - float(img[row, col]))
                if new_dist < D[nrow, ncol]:
                    D[nrow, ncol] = new_dist
                    q.push(new_dist, (nrow, ncol))

    return D


def run(img_path: str, mask_path: str) -> np.ndarray:
    img  = imread(img_path,  mode='L')
    mask = imread(mask_path, mode='L')
    return propagation(img, mask)