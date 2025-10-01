from rest_framework.routers import DefaultRouter
from .views import TrainingBlockViewSet, TrainingSessionViewSet, ExerciseViewSet, AthleteProgressViewSet

router = DefaultRouter()
router.register(r'blocks', TrainingBlockViewSet)
router.register(r'sessions', TrainingSessionViewSet)
router.register(r'exercises', ExerciseViewSet)
router.register(r'progress', AthleteProgressViewSet)

urlpatterns = router.urls
