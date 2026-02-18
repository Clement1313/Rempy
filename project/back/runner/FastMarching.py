import numpy as np
from imageio.v3 import imread
import matplotlib.pyplot as plt

from numba import njit

import heapq
from typing import Any

from sympy import arg

from Projet.Rempy.project.back.FastMarchingNumba import propagation2

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
    
    
def propagation(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rows, cols = img.shape
    D = np.full((rows, cols), 1e10, dtype=np.uint64)

    q = PQueue()
    arg = np.argwhere(mask > 0)
    for (row, col) in arg:
        D[row, col] = 0.0
        q.push(0.0, (row, col))

    neighbors = [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    while not q.empty():
        (dist, (row, col)) = q.pop()
        for (dist_row, dist_col) in neighbors:
            nrow, ncol = row + dist_row, col + dist_col
            if 0 <= nrow < rows and 0 <= ncol < cols:
                new_dist = dist + np.abs(img[nrow, ncol] - img[row, col])
                if new_dist < D[nrow, ncol]:
                    D[nrow, ncol] = new_dist
                    q.push(new_dist, (nrow, ncol))
                    

    return D

P = propagation(img, mask)

plt.figure(figsize=(10, 10))
plt.imshow(P, cmap="inferno")
