from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import InputImage, Benchmark
from .serializers import InputImageSerializer, BenchmarkSerializer
from runner.tasks import run_benchmark  

class InputImageViewSet(viewsets.ModelViewSet):
    queryset = InputImage.objects.all()
    serializer_class = InputImageSerializer


class BenchmarkViewSet(viewsets.ModelViewSet):
    queryset = Benchmark.objects.prefetch_related('images', 'results').all()
    serializer_class = BenchmarkSerializer

    def perform_create(self, serializer):
        benchmark = serializer.save()
        run_benchmark(benchmark.id)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Relancer un benchmark existant"""
        benchmark = self.get_object()
        run_benchmark(benchmark.id)
        return Response({'status': 'started'})
