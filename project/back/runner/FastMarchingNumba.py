import numpy as np
from numba import njit
from imageio.v3 import imread


@njit
def propagation(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rows, cols = img.shape
    D = np.full((rows, cols), 1e10, dtype=np.float64)

    max_size = rows * cols * 9
    h_dist = np.full(max_size, 1e10, dtype=np.float64)
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

    dr = np.array([-1, 1,  0, 0, -1, -1,  1, 1], dtype=np.int64)
    dc = np.array([ 0, 0,  1, -1, -1,  1, -1, 1], dtype=np.int64)

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


def run(img_path: str, mask_path: str) -> np.ndarray:
    img  = imread(img_path,  mode='L')
    mask = imread(mask_path, mode='L')
    return propagation(img, mask)