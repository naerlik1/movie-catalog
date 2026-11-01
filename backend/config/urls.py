from django.contrib import admin
from django.urls import include, path
from movies.views import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("movies.urls")),
    path("health", HealthView.as_view()),
]
