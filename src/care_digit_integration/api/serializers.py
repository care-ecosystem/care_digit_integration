from rest_framework import serializers

from care_digit_integration.models.digit_complaint_types import DigitComplaintTypes


class ServiceCodesSerializer(serializers.ModelSerializer):
    facility_id = serializers.CharField(source="facility.external_id")
    
    class Meta:
        model = DigitComplaintTypes
        fields = ["facility_id", "workflow", "service_codes"]
