import os
import time
import io
import numpy as np
import pandas as pd
from imageio.v3 import imread
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from benchmarks.models import Benchmark, Result

from runner import FastMarching, FastMarchingNumba

ALGORITHMS = {
    'fast_marching':       FastMarching,
    'fast_marching_numba': FastMarchingNumba,
}


def array_to_png(array: np.ndarray) -> bytes:
    normalized = (array / array.max() * 255).astype(np.uint8)
    img = PILImage.fromarray(normalized)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def load_grayscale(path: str) -> np.ndarray:
    img = imread(path)
    if img.ndim == 3:
        return np.mean(img[:, :, :3], axis=2).astype(np.float64)
    return img.astype(np.float64)


def run_benchmark(benchmark_id: int) -> dict:
    benchmark = Benchmark.objects.get(id=benchmark_id)
    benchmark.status = Benchmark.Status.RUNNING
    benchmark.save()

    rows = []

    try:
        for bench_image in benchmark.images.all():
            img_path  = bench_image.image_file.path
            mask_path = bench_image.mask_file.path
            img       = load_grayscale(img_path)
            mask      = load_grayscale(mask_path)

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