from functools import wraps
from typing import override

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .services import UsuarioService


def organizador_required(view_func):
    """
    Decorator que restringe o acesso exclusivamente a Organizadores Homologados ou Superusuários (RF05, RN04).
    Lança PermissionDenied caso o usuário não esteja autenticado ou não possua a homologação necessária.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user and request.user.is_authenticated):
            raise PermissionDenied(_('Autenticação necessária para acessar este recurso.'))

        if not request.user.is_organizador():
            raise PermissionDenied(_('Acesso restrito: é necessário possuir perfil de Organizador homologado para realizar esta ação.'))

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
            if not (request.user and request.user.is_authenticated):
                raise PermissionDenied(_('Autenticação necessária para acessar este recurso.'))

            evento_id = kwargs.get(evento_param)
            if not evento_id:
                raise PermissionDenied(_('Parâmetro identificador do evento não foi informado.'))

            try:
                ev_id = int(evento_id)
            except (ValueError, TypeError):
                raise PermissionDenied(_('Identificador do evento inválido.'))

            if not UsuarioService.verificar_papel_evento(request.user, ev_id, papel_esperado):
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

        try:
            ev_id = int(evento_id)
        except (ValueError, TypeError):
            return False

        return UsuarioService.verificar_papel_evento(request.user, ev_id, papel_esperado)


class IsSelfOrAdmin(BasePermission):
    """
    Permissão DRF que garante que um usuário só pode visualizar/editar seu próprio cadastro ou perfil,
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

        target_user = getattr(obj, 'usuario', obj)
        return bool(target_user == request.user or request.user.is_staff or request.user.is_superuser)


class IsPapelContextualManagerOrReadOnly(BasePermission):
    """
    Permissão para PapelContextualViewSet (RN03, RN05):
    - Leitura aberta a todos os usuários autenticados.
    - Modificação e exclusão restritas a organizadores homologados e staff.
    - Criação permitida para organizadores/staff ou para solicitação própria de papéis permitidos (RF06).
    """

    message = _('Você não possui permissão para gerenciar papéis de eventos.')

    @override
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in {'GET', 'HEAD', 'OPTIONS'}:
            return True
        if request.user.is_staff or request.user.is_superuser or request.user.is_organizador():
            return True
        return view.action == 'create'

    @override
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_staff or request.user.is_superuser or request.user.is_organizador())
