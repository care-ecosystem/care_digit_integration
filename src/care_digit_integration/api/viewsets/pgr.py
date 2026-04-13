from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

import logging

from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404

from care_digit_integration.api.serializers import PGRComplaintsCreateSerializer, PGRComplaintRetrieveSerializer
from care_digit_integration.models.pgr_complaints import PGRComplaints
from care_digit_integration.api.services.token_service import TokenService
from care_digit_integration.api.services.pgr_service import PGRService



class PGRViewSet(ModelViewSet):
    queryset = PGRComplaints.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = PGRComplaintRetrieveSerializer

    def create(self, request, *args, **kwargs):
        data = request.data

        facility_id = data.get("facility")
        facility = get_object_or_404(Facility, external_id=facility_id)
        workflow = data.get("workflow")
        service_code = data.get("service_code")
        app_context = data.get("app_context")
        description = data.get("description")

        serializer = PGRComplaintsCreateSerializer(data={
            "facility": facility.id,
            "app_context": app_context,
            "service_code": service_code,
            "workflow": workflow,
            "reporter": request.user.id,
            "pgr_status": PGRComplaints.PGRStatusTypes.PENDING_SYNC
        })

        serializer.is_valid(raise_exception=True)
        instance = serializer.save()


        pgr_service = PGRService()

        try:
            response = pgr_service.create_complaint(
                facility_id=facility_id,
                workflow=workflow,
                service_code=service_code,
                description=description
            )

            instance.pgr_response = response

            wrappers = response.get("ServiceWrappers") or []
            service = wrappers[0].get("service") if wrappers else {}

            instance.pgr_status = service.get("applicationStatus")
            instance.pgr_ticket_id = service.get("serviceRequestId")

        except Exception as e:
            instance.pgr_status = PGRComplaints.PGRStatusTypes.SYNC_FAILED
            return Response(
                {"detail": "Failed to sync complaint with PGR system"},
            )

        finally:
            instance.save()


        return Response(
            PGRComplaintRetrieveSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )
