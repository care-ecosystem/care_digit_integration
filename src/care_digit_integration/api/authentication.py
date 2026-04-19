from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
    TokenAuthentication,
    BasicAuthentication,
)
from config.patient_otp_authentication import JWTTokenPatientAuthentication
from rest_framework.exceptions import AuthenticationFailed


class HybridAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request)

        if not header:
            return None

        parts = header.split()

        if len(parts) != 2:
            return AuthenticationFailed("Invalid Authorization header format")

        prefix = parts[0].lower()

        try:
            if prefix == b"bearer":
                return JWTTokenPatientAuthentication().authenticate(request)

            elif prefix == b"token":
                return TokenAuthentication().authenticate(request)

            elif prefix == b"basic":
                return BasicAuthentication().authenticate(request)

            else:
                return AuthenticationFailed("Unsupported authentication type")

        except Exception as e:
            return AuthenticationFailed(str(e))