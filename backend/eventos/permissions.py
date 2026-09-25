from typing import override

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Papel

from .models import Evento, StatusEvento, VisibilidadeEvento


class CanCreateEventoPermission(BasePermission):
    message = _('Apenas organizadores homologados ou administradores podem cadastrar novos eventos.')

    @override
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return bool(request.user.is_organizador() or request.user.is_staff or request.user.is_superuser)


class IsEventoOrganizadorOrReadOnly(BasePermission):
    message = _('Você não possui autorização para gerenciar ou visualizar este evento.')

    @override
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if view.action == 'create':
            return bool(
                request.user
                and request.user.is_authenticated
                and (request.user.is_organizador() or request.user.is_staff or request.user.is_superuser)
            )

        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj: Evento):
        if request.method in SAFE_METHODS and obj.visibilidade == VisibilidadeEvento.PUBLICO and obj.status not in {
            StatusEvento.RASCUNHO,
            StatusEvento.CONFIGURACAO,
        }:
            return True

        if not (request.user and request.user.is_authenticated):
            return False

        return bool(
            request.user.is_staff
            or request.user.is_superuser
            or obj.usuario_representante_id == request.user.id
            or request.user.has_role(obj.id, Papel.ORGANIZADOR)
        )


class IsEventoSubResourceOrganizadorOrReadOnly(BasePermission):
    message = _('Apenas organizadores do evento podem modificar estas informações.')

    @override
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        evento = getattr(obj, 'evento', None)
        if not evento:
            return bool(request.user and (request.user.is_staff or request.user.is_superuser))

        if request.user.is_staff or request.user.is_superuser:
            return True

        if evento.usuario_representante_id == request.user.id:
            return True

        return request.user.has_role(evento.id, Papel.ORGANIZADOR)
