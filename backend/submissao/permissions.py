from typing import override

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Papel

from .models import Submissao
from .models import Avaliador


class CanCreateSubmissaoPermission(BasePermission):
    message = _('Apenas usuários com inscrição ativa podem submeter trabalhos.')

    @override
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return True


class IsSubmissaoAutorOrReadOnly(BasePermission):
    message = _('Você não possui autorização para gerenciar ou visualizar esta submissão.')

    @override
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if view.action == 'create':
            return bool(request.user and request.user.is_authenticated)

        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj: Submissao):
        if request.method in SAFE_METHODS:
            return bool(
                obj.autor_principal_id == request.user.id
                or obj.evento.usuario_representante_id == request.user.id
                or request.user.is_staff
                or request.user.is_superuser
                or request.user.has_role(obj.evento.id, Papel.ORGANIZADOR)
            )

        if not (request.user and request.user.is_authenticated):
            return False

        return bool(
            request.user.is_staff
            or request.user.is_superuser
            or obj.autor_principal_id == request.user.id
            or obj.evento.usuario_representante_id == request.user.id
            or request.user.has_role(obj.evento.id, Papel.ORGANIZADOR)
        )


class IsAvaliadorOrReadOnly(BasePermission):
    message = _('Apenas avaliadores ou organizadores do evento podem avaliar submissões.')

    @override
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return bool(
                obj.submissao.evento.usuario_representante_id == request.user.id
                or request.user.is_staff
                or request.user.is_superuser
                or request.user.has_role(obj.submissao.evento.id, Papel.ORGANIZADOR)
                or request.user == obj.avaliador
            )

        if not (request.user and request.user.is_authenticated):
            return False

        return bool(
            request.user.is_staff
            or request.user.is_superuser
            or obj.submissao.evento.usuario_representante_id == request.user.id
            or request.user.has_role(obj.submissao.evento.id, Papel.ORGANIZADOR)
        )


class IsOrganiadorEventoOrReadOnly(BasePermission):
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



class IsAvaliadorDonoOrReadOnly(BasePermission):
    message = _('Apenas o próprio avaliador ou a administração pode alterar este perfil.')

    @override
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user.is_staff
            or request.user.is_superuser
            or obj.usuario_id == request.user.id
        )