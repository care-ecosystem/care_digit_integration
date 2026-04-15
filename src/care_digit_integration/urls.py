from rest_framework.routers import DefaultRouter, SimpleRouter

from django.conf import settings

from care_digit_integration.api.viewsets.filestore import FileStoreViewSet
from care_digit_integration.api.viewsets.internal import InternalViewSet
from care_digit_integration.api.viewsets.pgr import PGRViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("filestore", FileStoreViewSet, basename="filestore")
router.register("internal", InternalViewSet, basename="internal")
router.register("pgr/complaints", PGRViewSet, basename="pgr_complaints")

urlpatterns = router.urls
