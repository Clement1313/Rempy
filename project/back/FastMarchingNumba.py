import numpy as np
from imageio.v3 import imread
import matplotlib.pyplot as plt

from numba import njit

import heapq
from typing import Any

from sympy import arg

IMAGE_PATH = "C:\\Users\\Utilisateur\\Desktop\\ING2\\Python\\TP1\\TP1\\TP1\\data\\img.png" # Change the path to point to your image
MASK_PATH = "C:\\Users\\Utilisateur\\Desktop\\ING2\\Python\\TP1\\TP1\\TP1\\data\\mask.png"
img = imread(IMAGE_PATH)
mask = imread(MASK_PATH)

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
    


@njit
def propagation2(img, mask):
    rows, cols = img.shape
    D = np.full((rows, cols), 1e10, dtype=np.uint64)

    max_size = rows * cols * 9
    h_dist = np.full(max_size, 1e10, dtype=np.uint64)
    h_row  = np.zeros(max_size, dtype=np.int64)
    h_col  = np.zeros(max_size, dtype=np.int64)
    heap_size = 0

    for r in range(rows):
        for c in range(cols):
            if mask[r, c] > 0:
                D[r, c] = 0.0
                h_dist[heap_size] = 0.0
                h_row[heap_size]  = r
                h_col[heap_size]  = c
                heap_size += 1

    dr = np.array([-1, 1, 0, 0, -1, -1, 1,  1], dtype=np.int64)
    dc = np.array([0,  0, 1,-1, -1,  1,-1,  1], dtype=np.int64)

    while heap_size > 0:
        min_idx = 0
        for i in range(1, heap_size):
            if h_dist[i] < h_dist[min_idx]:
                min_idx = i

        dist = h_dist[min_idx]
        row  = h_row[min_idx]
        col  = h_col[min_idx]

        heap_size -= 1
        h_dist[min_idx] = h_dist[heap_size]
        h_row[min_idx]  = h_row[heap_size]
        h_col[min_idx]  = h_col[heap_size]

        if dist > D[row, col]:
            continue

        for i in range(8):
            nrow = row + dr[i]
            ncol = col + dc[i]
            if 0 <= nrow < rows and 0 <= ncol < cols:
                new_dist = dist + abs(float(img[nrow, ncol]) - float(img[row, col]))
                if new_dist < D[nrow, ncol]:
                    D[nrow, ncol] = new_dist
                    h_dist[heap_size] = new_dist
                    h_row[heap_size]  = nrow
                    h_col[heap_size]  = ncol
                    heap_size += 1

    return D

P = propagation2(img, mask)

plt.figure(figsize=(10, 10))
plt.imshow(P, cmap="inferno")