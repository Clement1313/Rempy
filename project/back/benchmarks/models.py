from django.db import models

class InputImage(models.Model):
    name       = models.CharField(max_length=255)
    image_file = models.ImageField(upload_to='inputs/images/')
    ##mask_file  = models.ImageField(upload_to='inputs/masks/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name


class Benchmark(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        RUNNING = 'running', 'En cours'
        DONE    = 'done',    'Terminé'
        FAILED  = 'failed',  'Echoué'

    name       = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    status     = models.CharField(choices=Status.choices, default=Status.PENDING)
    images     = models.ManyToManyField(InputImage, related_name='benchmarks')

    def __str__(self):
        return f"{self.name} ({self.status})"


class Result(models.Model):
    benchmark      = models.ForeignKey(Benchmark, on_delete=models.CASCADE, related_name='results')
    image          = models.ForeignKey(InputImage, on_delete=models.CASCADE)
    algorithm      = models.CharField(max_length=30)          
    output_image   = models.ImageField(upload_to='outputs/', null=True, blank=True)
    execution_time = models.FloatField(help_text="Temps en secondes")
    metrics        = models.JSONField(default=dict)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.algorithm}] {self.benchmark.name} - image {self.image.id}"