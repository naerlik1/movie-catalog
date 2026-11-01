from datetime import datetime, timezone
from django.utils import timezone as django_timezone
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from .models import RevokedToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class LoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response({"access": str(AccessToken.for_user(user)), "user": UserSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        RevokedToken.objects.filter(expires_at__lt=django_timezone.now()).delete()
        RevokedToken.objects.get_or_create(jti=request.auth["jti"], defaults={
            "expires_at": datetime.fromtimestamp(request.auth["exp"], tz=timezone.utc),
        })
        return Response(status=204)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
