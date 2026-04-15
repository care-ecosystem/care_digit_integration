from rest_framework import serializers

from care.facility.models import Facility

from care_digit_integration.models.digit_complaint_types import DigitComplaintTypes
from care_digit_integration.models.pgr_complaints import PGRComplaints


class ServiceCodesSerializer(serializers.ModelSerializer):
    facility_id = serializers.CharField(source="facility.external_id")

    class Meta:
        model = DigitComplaintTypes
        fields = ["facility_id", "workflow", "service_codes"]


class DigitComplaintTypesCreateSerializer(serializers.ModelSerializer):
    facility_id = serializers.CharField(write_only=True)

    class Meta:
        model = DigitComplaintTypes
        fields = [
            "facility_id",
            "tenant_id",
            "workflow",
            "service_codes",
            "status",
        ]

    def validate(self, data):
        facility_external_id = data.pop("facility_id")

        try:
            facility = Facility.objects.get(external_id=facility_external_id)
        except Facility.DoesNotExist:
            raise serializers.ValidationError("Invalid facility_id")

        data["facility"] = facility

        return data



class PGRComplaintsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PGRComplaints
        fields = [
            "facility",
            "app_context",
            "service_code",
            "workflow",
            "reporter"
        ]

class PGRComplaintRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PGRComplaints
        fields = "__all__"
