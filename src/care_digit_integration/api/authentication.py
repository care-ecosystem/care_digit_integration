from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from care.emr.models import Encounter


class JWTTokenStaffAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result is None:
            return None

        user, _ = auth_result

        if not user:
            raise AuthenticationFailed("User is not a staff")

        return auth_result


class EncounterBasedAuthentication(BaseAuthentication):
    def authenticate(self, request):
        import logging
        logger = logging.getLogger(__name__)

        data = request.data if request.method == "POST" else request.query_params

        logger.info(f"EncounterBasedAuthentication data: {data}")

        auth_type = data.get("auth_type")
        if auth_type != "encounter_based":
            return None

        encounter_id = data.get("encounter_id")
        birth_year = data.get("birth_year")
        phone_number = data.get("phone_number")

        if not encounter_id:
            raise AuthenticationFailed("Encounter ID is required")

        if not (birth_year or phone_number):
            raise AuthenticationFailed("Either birth year or phone number is required")

        try:
            encounter = Encounter.objects.select_related("patient").get(external_id=encounter_id)
        except Encounter.DoesNotExist:
            raise AuthenticationFailed("Invalid encounter ID.")

        patient = encounter.patient

        birth_year_valid = False
        phone_valid = False

        if birth_year:
            try:
                birth_year_valid = patient.year_of_birth == int(birth_year)
            except (TypeError, ValueError):
                if not phone_number:
                    raise AuthenticationFailed("Enter a valid birth year") from None
                birth_year_valid = False

        if phone_number:
            if not isinstance(phone_number, str):
                raise AuthenticationFailed("Enter a valid phone number")
            phone_valid = patient.phone_number == phone_number.strip()

        if birth_year_valid or phone_valid:
            return (patient, None)

        raise AuthenticationFailed("User credentials do not match")
