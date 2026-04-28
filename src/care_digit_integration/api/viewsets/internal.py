from urllib3 import request

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404

from care_digit_integration.api.serializers import ServiceCodesSerializer, DigitComplaintTypesCreateSerializer
from care_digit_integration.models.digit_complaint_types import DigitComplaintTypes
from rest_framework.permissions import IsAuthenticated

# )
from care_digit_integration.api.authentication import HybridAuthentication


class InternalViewSet(GenericViewSet):

    authentication_classes = [
        HybridAuthentication,
    ]

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get", "post"], url_path="service-codes")
    def service_codes(self, request):
        if request.method == "GET":
            facility_id = request.query_params.get('facility_id')
            workflow = request.query_params.get('workflow')

            if not facility_id:
                return Response(
                    {"error": "facility_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not workflow:
                return Response(
                    {"error": "workflow is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            facility = get_object_or_404(
                Facility,
                external_id=facility_id
            )

            complaint_types = get_object_or_404(
                DigitComplaintTypes,
                facility=facility,
                workflow=workflow,
                status=DigitComplaintTypes.StatusTypes.ACTIVE
            )

            serializer = ServiceCodesSerializer(complaint_types)
            return Response(serializer.data)

        else:
            serializer = DigitComplaintTypesCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=400)

            serializer.save()

            return Response(serializer.data, status=201)
