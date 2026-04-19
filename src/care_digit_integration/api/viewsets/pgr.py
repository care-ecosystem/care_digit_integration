from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
import uuid


import logging

from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404

from care_digit_integration.api.serializers import PGRComplaintsCreateSerializer, PGRComplaintRetrieveSerializer
from care_digit_integration.models.pgr_complaints import PGRComplaints
from care_digit_integration.api.services.pgr_service import PGRService
from care_digit_integration.api.authentication import HybridAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination


from care.emr.models import Patient



logger = logging.getLogger(__name__)

class PGRPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PGRViewSet(ModelViewSet):
    queryset = PGRComplaints.objects.all()
    authentication_classes = [
        HybridAuthentication,
        SessionAuthentication,
    ]

    permission_classes = [IsAuthenticated]
    serializer_class = PGRComplaintRetrieveSerializer
    pagination_class = PGRPagination

    def get_queryset(self):
        user = self.request.user

        # STAFF
        if getattr(user, "external_id", None):
            return PGRComplaints.objects.filter(
                reporter=user.external_id
                ).order_by("-created_date", "-id")

        # PATIENT
        elif getattr(user, "phone_number", None):
            try:
                patient = Patient.objects.get(phone_number=user.phone_number)
                return PGRComplaints.objects.filter(
                    reporter=patient.external_id
                ).order_by("-created_date", "-id")
            except Patient.DoesNotExist:
                return PGRComplaints.objects.none()

        return PGRComplaints.objects.none()


    def create(self, request, *args, **kwargs):
        data = request.data
        logger.info(f"Request data: {request.data}")

        user = request.user
        reporter = None
        reporter_type = None

        # STAFF (normal users)
        if getattr(user, "external_id", None):
            reporter = user.external_id
            reporter_type = "staff"

        # PATIENT (JWT auth)
        elif getattr(user, "phone_number", None):
            try:
                patient = Patient.objects.get(phone_number=user.phone_number)
                reporter = patient.external_id
                reporter_type = "patient"
            except Patient.DoesNotExist:
                return Response(
                    {"detail": "Patient not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        else:
            return Response(
                {"detail": "Unable to determine reporter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reporter = uuid.UUID(str(reporter))
        except ValueError:
            return Response(
                {"detail": "Invalid reporter UUID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        facility_id = data.get("facility")
        facility = get_object_or_404(Facility, external_id=facility_id)
        workflow = data.get("workflow")
        service_code = data.get("service_code")
        app_context = data.get("app_context")

        description = data.get("description")
        filestore_uploads = data.get("filestore_uploads", [])
        source = data.get("source")

        logger.info(f"reporter id: {reporter} | reporter type: {reporter_type}")

        serializer = PGRComplaintsCreateSerializer(data={
            "facility": facility.id,
            "app_context": app_context,
            "service_code": service_code,
            "workflow": workflow,
            "reporter": reporter,
            "reporter_type": reporter_type,
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            return Response(response)

            # logger.info(f"Fetched complaint status for ticket id {kwargs.get('pk')} from PGR system")
            # logger.info(f"Response: {response}")

        except Exception as e:
            # logger.error(f"Failed to fetch complaint status for ticket id {kwargs.get("pk")}")
            logger.error(f"Failed to fetch complaint status: {str(e)}")

            return Response(
                {"detail": "Failed to fetch complaint status from PGR system"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # finally:
        #     return Response(
        #         response,
        #     )
