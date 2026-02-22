import os
import time
import io
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from imageio.v3 import imread
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from scipy import ndimage
from benchmarks.models import Benchmark, Result


from runner import FastMarching, FastMarchingNumba

ALGORITHMS = {
    'fast_marching':       FastMarching,
    'fast_marching_numba': FastMarchingNumba,
}

def array_to_png(array: np.ndarray) -> bytes:
    matplotlib.use('Agg')
    normalized = array / array.max()
    
    colored = cm.inferno(normalized)  
    colored_uint8 = (colored[:, :, :3] * 255).astype(np.uint8)  
    
    img = PILImage.fromarray(colored_uint8)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def generate_mask(img: np.ndarray, threshold_percentile: float = 95.0) -> np.ndarray:
    normalized = (img / img.max() * 255).astype(np.uint8)
    
    threshold = np.percentile(normalized, threshold_percentile)
    mask = (normalized >= threshold).astype(np.uint8)
    
    for i in range(5):
        mask = ndimage.binary_opening(mask, structure=np.ones((2, 2))).astype(np.uint8)
        mask = ndimage.binary_closing(mask, structure=np.ones((3, 3))).astype(np.uint8)

    mask = ndimage.binary_dilation(mask, structure=np.ones((2, 2))).astype(np.uint8)
    mask = ndimage.binary_opening(mask, structure=np.ones((2, 2))).astype(np.uint8)
    
    labeled, num_features = ndimage.label(mask)
    if num_features == 0:
        return np.zeros_like(normalized)
    
    sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
    sorted_indices = np.argsort(sizes)[::-1] + 1
     
    new_mask = np.zeros_like(mask)
    for idx in sorted_indices[:2]:
        new_mask[labeled == idx] = 1
    
    new_mask = ndimage.binary_closing(new_mask, structure=np.ones((5, 5))).astype(np.uint8)
    
    return new_mask * 255


def load_grayscale(path: str) -> np.ndarray:
    img = imread(path)
    if img.ndim == 3:
        return np.mean(img[:, :, :3], axis=2).astype(np.float64)
    return img.astype(np.float64)


def run_benchmark(benchmark_id: int, threshold: float = 95.0) -> dict:
    benchmark = Benchmark.objects.get(id=benchmark_id)
    benchmark.status = Benchmark.Status.RUNNING
    benchmark.save()

    rows = []

    try:
        for bench_image in benchmark.images.all():
            img_path  = bench_image.image_file.path
            img       = load_grayscale(img_path)
            mask      = generate_mask(img, threshold_percentile=threshold)

            from django.core.files.base import ContentFile
            mask_png = PILImage.fromarray(mask.astype(np.uint8))
            mask_buffer = io.BytesIO()
            mask_png.save(mask_buffer, format='PNG')
            mask_buffer.seek(0)
            from django.core.files.storage import default_storage
            default_storage.save(
                f'outputs/mask_{bench_image.id}.png',
                ContentFile(mask_buffer.read())
                )

            for algo_name, algo_module in ALGORITHMS.items():
                start   = time.perf_counter()
                D       = algo_module.propagation(img, mask)
                elapsed = time.perf_counter() - start

                result = Result(
                    benchmark=benchmark,
                    image=bench_image,
                    algorithm=algo_name,
                    execution_time=elapsed,
                    metrics={
                        'max_distance':  float(D.max()),
                        'mean_distance': float(D.mean()),
                        'min_distance':  float(D.min()),
                        'image_width':   int(img.shape[1]),
                        'image_height':  int(img.shape[0]),
                        'image_pixels':  int(img.shape[0] * img.shape[1]),
                    },
                )
                png_bytes = array_to_png(D)
                result.output_image.save(
                    f'output_{algo_name}_{bench_image.id}.png',
                    ContentFile(png_bytes)
                )
                result.save()


                rows.append({
                    'image':          os.path.basename(bench_image.image_file.name),
                    'algorithm':      algo_name,
                    'taille (px)':    f"{int(img.shape[1])}x{int(img.shape[0])}",
                    'pixels':         int(img.shape[0] * img.shape[1]),
                    'temps (s)':      round(elapsed, 4),
                    'max_distance':   float(D.max()),
                    'mean_distance':  round(float(D.mean()), 4),
                    'min_distance':   float(D.min()),
                    'output_image':   result.output_image.url,
                    'input_image':    bench_image.image_file.url,

                })

        benchmark.status = Benchmark.Status.DONE

    except Exception as e:
        benchmark.status = Benchmark.Status.FAILED
        raise e

    finally:
        benchmark.save()

    df = pd.DataFrame(rows)

    df_pivot = df.pivot_table(
        index=['image', 'taille (px)', 'pixels', 'max_distance', 'mean_distance', 'min_distance'],
        columns='algorithm',
        values='temps (s)',
        aggfunc='first'
    ).reset_index()

    df_pivot.columns.name = None 

    print("\nDataFrame brut")
    print(df.to_string())
    print("\n=========== DataFrame final ==========")
    print(df_pivot.to_string())
    print()

    return {
        'benchmark_id':   benchmark.id,
        'benchmark_name': benchmark.name,
        'status':         benchmark.status,
        'table':          df_pivot.to_dict(orient='records'),  
        'raw':            df.to_dict(orient='records'),        
    }

def _warmup_numba():
    dummy_img  = np.ones((10, 10), dtype=np.float64)
    dummy_mask = np.zeros((10, 10), dtype=np.float64)
    dummy_mask[5, 5] = 1.0
    FastMarchingNumba.propagation(dummy_img, dummy_mask)

_warmup_numba() 