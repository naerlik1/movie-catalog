from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import RevokedToken


class CatalogJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        token = super().get_validated_token(raw_token)
        if RevokedToken.objects.filter(jti=token["jti"]).exists():
            raise AuthenticationFailed("Вы вышли из аккаунта. Войдите снова.")
        return token
