from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound

from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404
from care.emr.models import Patient

from care_digit_integration.api.serializers import PGRComplaintsCreateSerializer, PGRComplaintRetrieveSerializer
from care_digit_integration.models.pgr_complaints import PGRComplaints
from care_digit_integration.api.services.pgr_service import PGRService
from care_digit_integration.api.authentication import HybridAuthentication

class PGRViewSet(ModelViewSet):
    queryset = PGRComplaints.objects.all()
    authentication_classes = [
        HybridAuthentication,
    ]

    permission_classes = [IsAuthenticated]
    serializer_class = PGRComplaintRetrieveSerializer
    # def get_queryset(self):
    #     return PGRComplaints.objects.filter(
    #         workflow="system",
    #         reporter=self.request.user
    #     ).order_by("-created_date")

    def _get_reporter_details(self, request):
        user = request.user

        # STAFF
        if getattr(user, "external_id", None):
            return {
                "reporter": user.external_id,
                "reporter_type": "staff",
            }

        if getattr(user, "phone_number", None):
            patients = Patient.objects.filter(phone_number=user.phone_number)

            if not patients.exists():
                raise NotFound("Patient not found")

            if patients.count() == 1:
                patient = patients.first()
                return {
                    "reporter": patient.external_id,
                    "reporter_type": "patient",
                }

            patient_external_id = request.query_params.get("patient")

            if not patient_external_id:
                raise ValidationError(
                    "Multiple patients found for this phone number. Please provide 'patient' (external_id)."
                )

            try:
                patient = patients.get(external_id=patient_external_id)
            except Patient.DoesNotExist:
                raise ValidationError("Invalid patient external_id")

            return {
                "reporter": patient.external_id,
                "reporter_type": "patient",
            }

        raise ValidationError("Unable to determine reporter")

    def get_queryset(self):
        try:
            reporter_data = self._get_reporter_details(self.request)
            reporter = reporter_data["reporter"]

            return (
                PGRComplaints.objects.filter(reporter=reporter)
                .order_by("-created_date", "-id")
            )

        except (ValidationError, NotFound):
            return PGRComplaints.objects.none()

    def create(self, request, *args, **kwargs):
        data = request.data
        reporter_data = self._get_reporter_details(request)
        reporter = reporter_data["reporter"]
        reporter_type = reporter_data["reporter_type"]

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
        instance = get_object_or_404(
            PGRComplaints, pgr_ticket_id=kwargs.get("pk"))

        pgr_service = PGRService()

        try:

            response = pgr_service.fetch_complaint(
                pgr_ticket_id=kwargs.get('pk'),
                facility_id=instance.facility.external_id,
                workflow=instance.workflow
            )
            return Response(response)

        except Exception as e:

            return Response(
                {"detail": "Failed to fetch complaint status from PGR system"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
