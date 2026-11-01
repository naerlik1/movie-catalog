from rest_framework.permissions import BasePermission, SAFE_METHODS


class MoviePermission(BasePermission):
    message = "Добавлять фильмы может только администратор."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (request.user.is_authenticated and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff and obj.owner_id == request.user.id
