import logging
from typing import Any, Dict, List, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from usuarios.models import Papel, PapelContextual, Usuario

from .models import (
    EquipeOrganizadora,
    Evento,
    RegraSubmissao,
    StatusEvento,
)
from .validators import formatar_titulo_evento

logger = logging.getLogger(__name__)


class EventoService:

    @staticmethod
    def usuario_pode_gerenciar_evento(usuario: Usuario, evento: Evento) -> bool:
        if not (usuario and usuario.is_authenticated and usuario.is_active):
            return False

        if usuario.is_staff or usuario.is_superuser:
            return True

        if evento.usuario_representante_id == usuario.id:
            return True

        return usuario.has_role(evento.id, Papel.ORGANIZADOR)

    @classmethod
    @transaction.atomic
    def criar_evento(
        cls,
        usuario: Usuario,
        dados_evento: Dict[str, Any],
        organizadores: Optional[List[Dict[str, Any]]] = None,
        regra_submissao: Optional[Dict[str, Any]] = None,
    ) -> Evento:
        if not (usuario and usuario.is_authenticated):
            raise PermissionDenied(_('Usuário deve estar autenticado para criar eventos.'))

        if not (usuario.is_organizador() or usuario.is_staff or usuario.is_superuser):
            raise PermissionDenied(_('Usuário não possui homologação de organizador para criar eventos.'))

        payload = dados_evento.copy()
        payload.pop('usuario_representante', None)

        if 'nome' in payload and payload['nome']:
            payload['nome'] = formatar_titulo_evento(payload['nome'])

        if organizadores:
            payload.setdefault('status', StatusEvento.CONFIGURACAO)
        else:
            payload.setdefault('status', StatusEvento.RASCUNHO)

        evento = Evento(usuario_representante=usuario, **payload)
        evento.full_clean()
        evento.save()

        PapelContextual.objects.get_or_create(
            usuario=usuario,
            evento_id=evento.id,
            papel=Papel.ORGANIZADOR,
            defaults={'ativo': True},
        )

        if organizadores:
            for org_data in organizadores:
                EquipeOrganizadora.objects.create(
                    evento=evento,
                    nome=org_data['nome'],
                    email_publico=org_data['email_publico'],
                    papel_funcao=org_data.get('papel_funcao', 'Organizador'),
                )
        else:
            EquipeOrganizadora.objects.create(
                evento=evento,
                nome=usuario.nome_completo,
                email_publico=usuario.email,
                papel_funcao='Coordenador Geral',
            )

        if regra_submissao is not None:
            regra = RegraSubmissao(
                evento=evento,
                aceita_submissao=regra_submissao.get('aceita_submissao', False),
                data_hora_inicio=regra_submissao.get('data_hora_inicio'),
                data_hora_fim=regra_submissao.get('data_hora_fim'),
            )
            regra.full_clean()
            regra.save()
        else:
            RegraSubmissao.objects.create(evento=evento, aceita_submissao=False)

        return evento

    @classmethod
    @transaction.atomic
    def alterar_evento(cls, evento: Evento, dados: Dict[str, Any], usuario: Usuario) -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para alterar este evento.'))

        if evento.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            raise ValidationError(
                _('Eventos no estado %(status)s não podem sofrer alterações.'),
                params={'status': evento.get_status_display()},
            )

        nova_data = dados.get('data')
        if nova_data and str(nova_data) != str(evento.data):
            if not evento.pode_alterar_data():
                raise ValidationError(
                    _('A data do evento só pode ser alterada até 1 semana antes da data definida inicialmente.')
                )

        alterou_horario = (
            ('hora_inicio' in dados and str(dados['hora_inicio']) != str(evento.hora_inicio))
            or ('hora_fim' in dados and str(dados['hora_fim']) != str(evento.hora_fim))
        )
        alterou_descricao = 'descricao' in dados and dados['descricao'] != evento.descricao
        alterou_programacao = 'programacao_geral' in dados and dados['programacao_geral'] != evento.programacao_geral

        if (alterou_horario or alterou_descricao or alterou_programacao) and not evento.pode_alterar_detalhes():
            raise ValidationError(
                _('Horário, descrição e programação só podem ser modificados até 1 hora antes do início do evento.')
            )

        for campo, valor_campo in dados.items():
            valor_final = formatar_titulo_evento(valor_campo) if (campo == 'nome' and valor_campo) else valor_campo
            if hasattr(evento, campo):
                setattr(evento, campo, valor_final)

        evento.full_clean()
        evento.save()
        return evento

    @classmethod
    def publicar_evento(cls, evento: Evento, usuario: Usuario) -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para publicar este evento.'))

        if evento.status not in {StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO}:
            raise ValidationError(
                _('Apenas eventos em Rascunho ou Configuração podem ser publicados. Status atual: %(status)s.'),
                params={'status': evento.get_status_display()},
            )

        erros = {}
        if not evento.organizadores.exists():
            erros['organizadores'] = _('O evento deve possuir pelo menos um membro na equipe organizadora.')
        if evento.data_inicio_completa <= timezone.now():
            erros['data'] = _('Não é possível publicar eventos com data de início no passado.')

        if erros:
            raise ValidationError(erros)

        evento.status = StatusEvento.PUBLICADO
        evento.save(update_fields=['status', 'atualizado_em'])
        return evento

    @classmethod
    def abrir_inscricoes(cls, evento: Evento, usuario: Usuario) -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para abrir inscrições neste evento.'))

        if evento.status != StatusEvento.PUBLICADO:
            raise ValidationError(
                _('O evento precisa estar no estado "Publicado" para abrir inscrições.')
            )

        if timezone.now() >= evento.limite_encerramento_inscricoes:
            raise ValidationError(
                _('Não é possível abrir inscrições: o prazo de encerramento automático (15 minutos antes do início) já foi alcançado.')
            )

        evento.status = StatusEvento.INSCRICOES_ABERTAS
        evento.save(update_fields=['status', 'atualizado_em'])
        return evento

    @classmethod
    def cancelar_evento(cls, evento: Evento, usuario: Usuario, motivo: str = '') -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para cancelar este evento.'))

        if evento.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            raise ValidationError(
                _('Não é possível cancelar um evento que já está %(status)s.'),
                params={'status': evento.get_status_display()},
            )

        if not evento.pode_cancelar():
            if evento.is_curta_duracao:
                raise ValidationError(
                    _('Eventos de curta duração (Oficinas, Palestras, Treinamentos, etc.) só podem ser cancelados com até 1 hora de antecedência.')
                )
            raise ValidationError(
                _('O cancelamento de eventos em geral deve ser realizado com no mínimo 1 semana de antecedência da data inicial.')
            )

        evento.status = StatusEvento.CANCELADO
        evento.motivo_cancelamento = motivo or _('Cancelado pelo organizador.')
        evento.cancelado_em = timezone.now()
        evento.save(update_fields=['status', 'motivo_cancelamento', 'cancelado_em', 'atualizado_em'])
        return evento

    @classmethod
    def finalizar_evento(cls, evento: Evento, usuario: Usuario) -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para finalizar este evento.'))

        if evento.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            raise ValidationError(_('Este evento já foi concluído ou cancelado.'))

        evento.status = StatusEvento.FINALIZADO
        evento.save(update_fields=['status', 'atualizado_em'])
        return evento

    @classmethod
    def arquivar_evento(cls, evento: Evento, usuario: Usuario) -> Evento:
        if not cls.usuario_pode_gerenciar_evento(usuario, evento):
            raise PermissionDenied(_('Você não possui permissão para arquivar este evento.'))

        if evento.status not in {StatusEvento.FINALIZADO, StatusEvento.CANCELADO}:
            raise ValidationError(_('Apenas eventos finalizados ou cancelados podem ser arquivados.'))

        evento.status = StatusEvento.ARQUIVADO
        evento.save(update_fields=['status', 'atualizado_em'])
        return evento

    @classmethod
    def verificar_inscricoes_encerradas(cls, evento: Evento) -> bool:
        return not evento.inscricoes_abertas_status
