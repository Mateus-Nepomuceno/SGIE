import logging
from functools import wraps
from typing import override

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission

from .services import UsuarioService

logger = logging.getLogger(__name__)


def organizador_required(view_func):
    """
    Decorator que restringe o acesso exclusivamente a Organizadores Homologados ou Superusuários (RF05, RN04).
    Redireciona para o painel de perfil caso o usuário não possua a homologação necessária.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('usuarios:login')
            return redirect(f'{login_url}?next={request.path}')

        if not request.user.is_organizador():
            try:
                messages.warning(request, _('Acesso restrito: é necessário possuir perfil de Organizador homologado para realizar esta ação.'))
            except Exception as exc:
                logger.debug('Não foi possível adicionar mensagem flash: %s', exc)
            return redirect('usuarios:perfil')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def role_required(papel_esperado: str, evento_param: str = 'evento_id'):
    """
    Decorator para proteção contextual de rotas por evento (RN03, RN05).
    Exportado para uso nos módulos de Submissão (Autor) e Avaliação (Avaliador).
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = reverse('usuarios:login')
                return redirect(f'{login_url}?next={request.path}')

            evento_id = kwargs.get(evento_param)
            if not evento_id:
                raise PermissionDenied(_('Parâmetro identificador do evento não foi informado.'))

            if not UsuarioService.verificar_papel_evento(request.user, int(evento_id), papel_esperado):
                raise PermissionDenied(_('Acesso restrito ao papel %(papel)s neste evento.') % {'papel': papel_esperado})

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class IsOrganizadorPermission(BasePermission):
    """Permissão do Django REST Framework para checar status de organizador."""

    message = _('Acesso restrito a organizadores homologados.')

    @override
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_organizador())


class HasEventRolePermission(BasePermission):
    """Permissão do Django REST Framework para checar papéis contextuais por evento."""

    message = _('Usuário não possui o papel exigido para este evento.')

    @override
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        papel_esperado = getattr(view, 'required_role', None)
        query_params = getattr(request, 'query_params', getattr(request, 'GET', {}))
        kwargs = getattr(view, 'kwargs', {}) or {}
        evento_id = kwargs.get('evento_id') or query_params.get('evento_id')

        if not papel_esperado or not evento_id:
            return False

        return UsuarioService.verificar_papel_evento(request.user, int(evento_id), papel_esperado)


class IsSelfOrAdmin(BasePermission):
    """
    Permissão DRF que garante que um usuário só pode visualizar/editar seu próprio cadastro,
    a menos que possua perfil de staff/administrador.
    Operações de exclusão (destroy) são restritas a superusuários/staff.
    """

    message = _('Você não possui permissão para acessar ou modificar este recurso.')

    @override
    def has_permission(self, request, view):
        if view.action == 'create':
            return True
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method == 'DELETE':
            return bool(request.user.is_staff or request.user.is_superuser)

        return bool(obj == request.user or request.user.is_staff or request.user.is_superuser)
