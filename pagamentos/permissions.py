from typing import override

from rest_framework import permissions

from usuarios.models import Papel


def usuario_e_organizador_ou_admin(user, evento) -> bool:
    """Verifica se o usuário é organizador do evento ou administrador do sistema."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if evento.usuario_representante_id == user.id:
        return True
    return user.has_role(evento.id, Papel.ORGANIZADOR)


class IsOrganizadorDoEventoOuAdmin(permissions.BasePermission):
    """
    Permite leitura para usuários autenticados, mas escrita apenas para
    organizadores do evento associado ou administradores.
    """

    @override
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        # Localiza o evento correspondente no objeto
        evento = getattr(obj, 'evento', None)
        if not evento and hasattr(obj, 'categoria_preco'):
            evento = obj.categoria_preco.evento

        if request.method in permissions.SAFE_METHODS:
            return True

        if not evento:
            return bool(request.user.is_staff or request.user.is_superuser)

        return usuario_e_organizador_ou_admin(request.user, evento)


class IsDonoDoObjetoOuOrganizador(permissions.BasePermission):
    """
    Permite acesso ao participante dono do registro financeiro (inscrição/pagamento)
    ou aos organizadores do respectivo evento / administradores.
    """

    @override
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    @override
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or user.is_superuser:
            return True

        dono_id = None
        evento = None

        if hasattr(obj, 'inscricao'):
            dono_id = obj.inscricao.usuario_id
            evento = obj.inscricao.evento
        elif hasattr(obj, 'cobranca'):
            dono_id = obj.cobranca.inscricao.usuario_id
            evento = obj.cobranca.inscricao.evento
        elif hasattr(obj, 'solicitado_por'):
            dono_id = obj.solicitado_por_id
            evento = obj.pagamento.cobranca.inscricao.evento

        if dono_id and dono_id == user.id:
            return True

        return bool(evento and usuario_e_organizador_ou_admin(user, evento))
