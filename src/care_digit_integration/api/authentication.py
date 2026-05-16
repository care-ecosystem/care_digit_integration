from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.patient_otp_authentication import JWTTokenPatientAuthentication


class HybridAuthentication(BaseAuthentication):
    def __init__(self) -> None:
        self.patient_auth = JWTTokenPatientAuthentication()
        self.staff_auth = JWTAuthentication()


    def _validate_auth_header(self, auth_header):
        if not auth_header:
            raise AuthenticationFailed("Authorization header missing")

        parts = auth_header.split()

        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header format")

        scheme = parts[0].decode().lower()

        if scheme != "bearer":
            raise AuthenticationFailed("Unsupported authentication type")


    def _authenticate_patient(self, request):
        try:
            auth_result = self.patient_auth.authenticate(request)
            if auth_result:
                return auth_result
            raise AuthenticationFailed("Invalid patient token")

        except AuthenticationFailed:
            return None


    def _authenticate_staff(self, request):
        try:
            auth_result = self.staff_auth.authenticate(request)
            if auth_result and auth_result[0] and auth_result[0].is_staff:
                return auth_result

            raise AuthenticationFailed("User is not authorized as staff")

        except AuthenticationFailed:
            return None


    def authenticate(self, request):
        auth_header = get_authorization_header(request)
        self._validate_auth_header(auth_header)

        patient_auth = self._authenticate_patient(request)
        if patient_auth:
            return patient_auth

        staff_auth = self._authenticate_staff(request)
        if staff_auth:
            return staff_auth

        raise AuthenticationFailed("Invalid token or user not authorized")
