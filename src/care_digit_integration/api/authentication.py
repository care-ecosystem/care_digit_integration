from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from config.patient_otp_authentication import JWTTokenPatientAuthentication


class HybridAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request)

        # No authorization header provided, no auth attempted.
        if not header:
            return None

        parts = header.split()

        if len(parts) != 2:
            raise AuthenticationFailed("Invalid Authorization header format")

        prefix = parts[0].lower()

        if prefix != b"bearer":
            raise AuthenticationFailed("Unsupported authentication type.")

        try:
            user_auth = JWTTokenPatientAuthentication().authenticate(request)
            if user_auth:
                return user_auth
        except AuthenticationFailed:
            pass  

        try:
            jwt_auth = JWTAuthentication()
            user, token = jwt_auth.authenticate(request)

            if user.is_staff:
                return (user, token)
            else:
                raise AuthenticationFailed("User is not authorized as staff")
        except AuthenticationFailed:
            pass 

        raise AuthenticationFailed("Invalid or expired token")
