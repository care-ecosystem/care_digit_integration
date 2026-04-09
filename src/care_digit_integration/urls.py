from rest_framework.routers import DefaultRouter, SimpleRouter

from django.conf import settings

from care_digit_integration.api.viewsets.internal import InternalViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("internal", InternalViewSet, basename="internal")

urlpatterns = router.urls
