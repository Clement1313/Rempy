from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import InputImage, Benchmark
from .serializer import InputSerializer, BenchmarkSerializer
from runner.tasks import run_benchmark
import pandas as pd
import os




class InputImageViewSet(viewsets.ModelViewSet):
    queryset = InputImage.objects.all()
    serializer_class = InputSerializer


class BenchmarkViewSet(viewsets.ModelViewSet):
    queryset = Benchmark.objects.prefetch_related('images', 'results').all()
    serializer_class = BenchmarkSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = []

        for benchmark in queryset:
            serializer = self.get_serializer(benchmark)
            data = serializer.data

            rows = []
            for r in benchmark.results.all():
                rows.append({
                    'image':         os.path.basename(r.image.image_file.name),
                    'algorithm':     r.algorithm,
                    'taille (px)':   f"{r.metrics.get('image_width', '?')}x{r.metrics.get('image_height', '?')}",
                    'pixels':        r.metrics.get('image_pixels', 0),
                    'temps (s)':     round(r.execution_time, 4),
                    'max_distance':  r.metrics.get('max_distance', 0),
                    'mean_distance': round(r.metrics.get('mean_distance', 0), 4),
                    'min_distance':  r.metrics.get('min_distance', 0),
                    'output_image':  r.output_image.url if r.output_image else None,
                })

            if rows:
                df = pd.DataFrame(rows)
                df_pivot = df.pivot_table(
                    index=['image', 'taille (px)', 'pixels', 'max_distance', 'mean_distance', 'min_distance'],
                    columns='algorithm',
                    values='temps (s)',
                    aggfunc='first'
                ).reset_index()
                df_pivot.columns.name = None
                data['table'] = df_pivot.to_dict(orient='records')
                data['raw']   = rows

            result.append(data)

        return Response(result)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        benchmark = serializer.save()

        threshold = request.data.get('threshold', 95.0)
        result_dict = run_benchmark(benchmark.id, threshold=float(threshold))

        return Response(result_dict, status=201)
    
    def retrieve(self, request, *args, **kwargs):
        benchmark = self.get_object()
        serializer = self.get_serializer(benchmark)
        data = serializer.data

        rows = []
        for result in benchmark.results.all():
            rows.append({
                'image':         os.path.basename(r.image.image_file.name),
                'algorithm':     r.algorithm,
                'taille (px)':   f"{r.metrics.get('image_width', '?')}x{r.metrics.get('image_height', '?')}",
                'pixels':        r.metrics.get('image_pixels', 0),
                'temps (s)':     round(r.execution_time, 4),
                'max_distance':  r.metrics.get('max_distance', 0),
                'mean_distance': round(r.metrics.get('mean_distance', 0), 4),
                'min_distance':  r.metrics.get('min_distance', 0),
                'output_image':  r.output_image.url if r.output_image else None,
            })
        if rows:
            df = pd.DataFrame(rows)
            df_pivot = df.pivot_table(
                index=['image', 'taille (px)', 'pixels', 'max_distance', 'mean_distance', 'min_distance'],
                columns='algorithm',
                values='temps (s)',
                aggfunc='first'
            ).reset_index()
            df_pivot.columns.name = None
            data['table'] = df_pivot.to_dict(orient='records')
            data['raw']   = rows

        return Response(data)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        benchmark   = self.get_object()
        result_dict = run_benchmark(benchmark.id)
        return Response(result_dict)