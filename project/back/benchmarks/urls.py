from rest_framework.routers import DefaultRouter
from .views import InputImageViewSet, BenchmarkViewSet

router = DefaultRouter()
router.register('images', InputImageViewSet)
router.register('benchmarks', BenchmarkViewSet)

urlpatterns = router.urls