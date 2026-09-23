from rest_framework import permissions

class IsDonoDaInscricao(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.usuario == request.user:
            return True

        if request.user.is_staff:
            return True

        return False
