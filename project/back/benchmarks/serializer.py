from rest_framework import serializers
from .models import InputImage, Benchmark, Result


class InputSerializer(serializers.ModelSerializer):
    class Meta:
        model  = InputImage
        fields = ['id', 'name', 'image_file', 'uploaded_at'] #MODIF THOMAS


class ResultSerializer(serializers.ModelSerializer):
    image_name = serializers.CharField(source='image.name', read_only=True)

    class Meta:
        model  = Result
        fields = ['id', 'image_name', 'algorithm', 'output_image',
                  'execution_time', 'metrics', 'created_at']


class BenchmarkSerializer(serializers.ModelSerializer):
    results   = ResultSerializer(many=True, read_only=True)
    images    = InputSerializer(many=True, read_only=True)
    image_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=InputImage.objects.all(),
        write_only=True, source='images'
    )

    class Meta:
        model  = Benchmark
        fields = ['id', 'name', 'status', 'created_at', 'images', 'image_ids', 'results']