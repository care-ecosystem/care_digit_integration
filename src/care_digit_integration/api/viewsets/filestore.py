from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from care.facility.models import Facility
from care.utils.shortcuts import get_object_or_404

from care_digit_integration.api.services.filestore_service import FileStoreService
from care_digit_integration.api.authentication import HybridAuthentication
from care_digit_integration.models.digit_complaint_types import DigitComplaintTypes


class FileStoreViewSet(GenericViewSet):
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def upload(self, request):
        files = request.FILES
        facility_id = request.data.get("facility_id")
        workflow = request.data.get("workflow")

        facility = get_object_or_404(Facility, external_id=facility_id)

        digit_complaint_type = get_object_or_404(
            DigitComplaintTypes,
            facility=facility,
            workflow=workflow
        )

        tenant_id = digit_complaint_type.tenant_id

        try:
            filestore_service = FileStoreService()
            response = filestore_service.upload_files(
                files=files,
                tenant_id=tenant_id
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
