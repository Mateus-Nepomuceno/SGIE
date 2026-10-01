from rest_framework import permissions

from usuarios.models import Papel


class IsDonoDaInscricao(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.usuario == request.user:
            return True

        if request.user.is_staff:
            return True

        return False


class IsOrganizadorDoEvento(permissions.BasePermission):
    message = 'Apenas o organizador deste evento pode consultar a lista de participantes.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, evento):
        user = request.user

        if user.is_staff or user.is_superuser:
            return True

        if evento.usuario_representante_id == user.id:
            return True

        return user.has_role(evento.id, Papel.ORGANIZADOR)
