from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

# import logging

from care_digit_integration.settings import plugin_settings as settings
from care_digit_integration.api.services.filestore_service import FileStoreService
from rest_framework.permissions import IsAuthenticated
from care_digit_integration.api.authentication import HybridAuthentication
from rest_framework.authentication import SessionAuthentication


# logger = logging.getLogger(__name__)


class FileStoreViewSet(GenericViewSet):
    authentication_classes = [
        HybridAuthentication,
        SessionAuthentication,
    ]

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def upload(self, request):
        # logger.info("Modified\nInitiating file upload...")
        files = request.FILES
        tenant_id = settings.USER_INFO["TENANT_ID"]

        try:
            filestore_service = FileStoreService()
            response = filestore_service.upload_files(
                files=files,
                tenant_id=tenant_id
            )

            # logger.info(f"File upload successful: {response}")

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            # logger.error(f"File upload failed: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
