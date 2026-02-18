import time
import numpy as np
from django.core.files.base import ContentFile
from benchmarks.models import Benchmark, Result
from PIL import Image as PILImage
import io
from .FastMarching import propagation
from .FastMarchingNumba import propagation2

def run_benchmark(benchmark_id: int):
    benchmark = Benchmark.objects.get(id=benchmark_id)
    benchmark.status = Benchmark.Status.RUNNING
    benchmark.save()

    try:
        for image in benchmark.images.all():
            img_path = image.file.path
            start = time.perf_counter()
            
            output_array, metrics = propagation(img_path)  
            elapsed = time.perf_counter() - start


            pil_img = PILImage.fromarray(output_array.astype(np.uint8))
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            buffer.seek(0)

            result = Result(
                benchmark=benchmark,
                image=image,
                execution_time=elapsed,
                metrics=metrics,  
            )
            result.output_image.save(f'output_{image.id}.png', ContentFile(buffer.read()))
            result.save()

        benchmark.status = Benchmark.Status.DONE

    except Exception as e:
        benchmark.status = Benchmark.Status.FAILED
        print(f"Benchmark failed: {e}")

    finally:
        benchmark.save()