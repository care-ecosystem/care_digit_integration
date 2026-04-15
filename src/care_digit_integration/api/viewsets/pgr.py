from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

# import logging

from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404

from care_digit_integration.api.serializers import PGRComplaintsCreateSerializer, PGRComplaintRetrieveSerializer
from care_digit_integration.models.pgr_complaints import PGRComplaints
from care_digit_integration.api.services.pgr_service import PGRService


# logger = logging.getLogger(__name__)


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
        filestore_uploads = data.get("filestore_uploads", [])
        source = data.get("source")

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
                description=description,
                filestore_uploads=filestore_uploads,
                source=source
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


    @action(detail=True, methods=["get"])
    def check_status(self, request, *args, **kwargs):
        instance = get_object_or_404(PGRComplaints, pgr_ticket_id=kwargs.get("pk"))

        pgr_service = PGRService()

        try:
            # logger.info(f"Fetching complaint status for ticket id {kwargs.get('pk')} from PGR system")

            response = pgr_service.fetch_complaint(
                pgr_ticket_id=kwargs.get('pk'),
                facility_id=instance.facility.external_id,
                workflow=instance.workflow
            )

            # logger.info(f"Fetched complaint status for ticket id {kwargs.get('pk')} from PGR system")
            # logger.info(f"Response: {response}")

        except Exception as e:
            # logger.error(f"Failed to fetch complaint status for ticket id {kwargs.get("pk")}")

            return Response(
                {"detail": "Failed to fetch complaint status from PGR system"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        finally:
            return Response(
                response,
            )
