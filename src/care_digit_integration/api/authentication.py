from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTTokenStaffAuthentication(JWTAuthentication):
    def authenticate(self, request):
        auth_result = super().authenticate(request)
        
        if auth_result is None:
            return None

        user, _ = auth_result

        if not user.is_staff:
            raise AuthenticationFailed("User is not a staff")

        return auth_result
