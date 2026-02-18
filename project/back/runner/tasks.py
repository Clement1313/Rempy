import time
import io
from matplotlib.image import imread
import numpy as np
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


def run_benchmark(benchmark_id: int):
    benchmark = Benchmark.objects.get(id=benchmark_id)
    benchmark.status = Benchmark.Status.RUNNING
    benchmark.save()

    try:
        for bench_image in benchmark.images.all():
            img_path  = bench_image.image_file.path
            mask_path = bench_image.mask_file.path

            for algo_name, algo_module in ALGORITHMS.items():
                img = load_grayscale(img_path)
                mask = load_grayscale(mask_path)

                start = time.perf_counter()
                D = algo_module.propagation(img, mask)  
                elapsed = time.perf_counter() - start

                metrics = {
                    'max_distance':  float(D.max()),
                    'mean_distance': float(D.mean()),
                    'min_distance':  float(D.min() if D.size > 0 else 0),
                    'image_width':   int(img.shape[1]), 
                    'image_height':  int(img.shape[0]),
                    'image_pixels':  int(img.shape[0] * img.shape[1]),
                }

                result = Result(
                    benchmark=benchmark,
                    image=bench_image,
                    algorithm=algo_name,
                    execution_time=elapsed,
                    metrics=metrics,
                )
                
                png_bytes = array_to_png(D)
                result.output_image.save(
                    f'output_{algo_name}_{bench_image.id}.png',
                    ContentFile(png_bytes)
                )
                result.save()

        benchmark.status = Benchmark.Status.DONE

    except Exception as e:
        benchmark.status = Benchmark.Status.FAILED
        raise e

    finally:
        benchmark.save()