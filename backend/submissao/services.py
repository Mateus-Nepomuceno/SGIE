import logging
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from eventos.models import Evento
from usuarios.models import Usuario

from .models import (
    Apresentacao,
    Avaliacao,
    Local,
    StatusParecer,
    StatusSubmissao,
    Submissao,
    SubmissaoAutor,
    SubmissaoVersao,
    TipoParticipacaoAutor,
)
from .validators import validar_arquivo_submissao

logger = logging.getLogger(__name__)


class SubmissaoService:

    @staticmethod
    def usuario_pode_editar_submissao(usuario: Usuario, submissao: Submissao) -> bool:
        if not (usuario and usuario.is_authenticated and usuario.is_active):
            return False

        if usuario.is_staff or usuario.is_superuser:
            return True

        if submissao.autor_principal_id == usuario.id:
            return True

        return submissao.evento.usuario_representante_id == usuario.id

    @staticmethod
    def usuario_pode_avaliar_submissao(usuario: Usuario, submissao: Submissao) -> bool:
        if not (usuario and usuario.is_authenticated and usuario.is_active):
            return False

        if usuario.is_staff or usuario.is_superuser:
            return True

        return submissao.evento.usuario_representante_id == usuario.id

    @classmethod
    @transaction.atomic
    def criar_submissao(
        cls,
        usuario: Usuario,
        evento_id: int,
        area_id: int,
        dados_submissao: Dict[str, Any],
        arquivo: Optional[Any] = None,
        autores_dados: Optional[list] = None,
        dados_autor_principal: Optional[Dict[str, Any]] = None,
    ) -> Submissao:
        if not (usuario and usuario.is_authenticated):
            raise PermissionDenied(_('Usuário deve estar autenticado para criar submissões.'))

        try:
            evento = Evento.objects.select_related('regra_submissao').get(id=evento_id)
        except Evento.DoesNotExist:
            raise ValidationError(_('Evento não encontrado.'))

        regra = getattr(evento, 'regra_submissao', None)
        if not regra or not regra.aceita_submissao:
            raise ValidationError(_('Este evento não aceita submissão de trabalhos acadêmicos.'))

        dados = dados_submissao.copy()

        # Extrair arquivo se fornecido diretamente ou dentro de dados_submissao
        arquivo_final = arquivo if arquivo is not None else dados.get('arquivo')

        # Extrair autores se fornecidos diretamente ou dentro de dados_submissao
        coautores = autores_dados if autores_dados is not None else (dados.get('autores') or dados.get('coautores'))

        # Extrair dados de perfil do autor principal
        perfil_principal = (dados_autor_principal or {}).copy()
        for campo in ('lattes_url', 'linkedin_url', 'afiliacao_institucional', 'maior_titulacao', 'maiór_titulacao'):
            if campo in dados:
                val = dados.get(campo)
                if val and campo not in perfil_principal:
                    perfil_principal[campo] = val

        # Limpar chaves que não pertencem ao modelo Submissao
        dados.pop('arquivo', None)
        dados.pop('autores', None)
        dados.pop('coautores', None)
        dados.pop('lattes_url', None)
        dados.pop('linkedin_url', None)
        dados.pop('afiliacao_institucional', None)
        dados.pop('maior_titulacao', None)
        dados.pop('maiór_titulacao', None)
        dados.pop('autor_principal', None)
        dados.pop('evento', None)
        dados.pop('evento_id', None)
        dados.pop('area', None)
        dados.pop('area_id', None)
        dados.pop('status', None)

        # Criar a submissão como rascunho
        submissao = Submissao(
            evento=evento,
            area_id=area_id,
            autor_principal=usuario,
            status=StatusSubmissao.RASCUNHO,
            **dados,
        )
        submissao.full_clean()
        submissao.save()

        # Criar registro de autor principal com perfil acadêmico
        lattes_url = perfil_principal.get('lattes_url', '')
        linkedin_url = perfil_principal.get('linkedin_url', '')
        afiliacao_institucional = perfil_principal.get('afiliacao_institucional', '')
        maior_titulacao = (
            perfil_principal.get('maior_titulacao')
            or perfil_principal.get('maiór_titulacao', '')
        )

        SubmissaoAutor.objects.create(
            submissao=submissao,
            usuario=usuario,
            tipo_participacao=TipoParticipacaoAutor.PRINCIPAL,
            ordem_autoria=1,
            lattes_url=lattes_url,
            linkedin_url=linkedin_url,
            afiliacao_institucional=afiliacao_institucional,
            maiór_titulacao=maior_titulacao,
        )

        # Criar coautores caso informados
        if coautores:
            ordem_atual = 2
            for item in coautores:
                if isinstance(item, SubmissaoAutor):
                    continue
                coautor_dict = dict(item) if isinstance(item, dict) else {}
                usuario_coautor = coautor_dict.pop('usuario', None)
                if not usuario_coautor:
                    user_id = coautor_dict.pop('usuario_id', None)
                    if user_id:
                        usuario_coautor = Usuario.objects.filter(id=user_id).first()
                elif isinstance(usuario_coautor, (int, str)) and not isinstance(usuario_coautor, Usuario):
                    usuario_coautor = Usuario.objects.filter(id=usuario_coautor).first()

                if not usuario_coautor or usuario_coautor.id == usuario.id:
                    continue

                if SubmissaoAutor.objects.filter(submissao=submissao, usuario=usuario_coautor).exists():
                    continue

                coautor_dict.pop('submissao', None)
                titulacao = (
                    coautor_dict.pop('maior_titulacao', None)
                    or coautor_dict.pop('maiór_titulacao', '')
                )
                tipo_part = coautor_dict.pop('tipo_participacao', TipoParticipacaoAutor.COAUTOR)
                ordem = coautor_dict.pop('ordem_autoria', None) or ordem_atual
                ordem_atual = max(ordem_atual, ordem) + 1

                SubmissaoAutor.objects.create(
                    submissao=submissao,
                    usuario=usuario_coautor,
                    tipo_participacao=tipo_part,
                    ordem_autoria=ordem,
                    maiór_titulacao=titulacao,
                    **coautor_dict,
                )

        # Se arquivo fornecido, submeter versão 1 imediatamente
        if arquivo_final:
            cls.submeter_trabalho(submissao=submissao, arquivo=arquivo_final, usuario=usuario)
            submissao.refresh_from_db()

        logger.info(f'Submissão {submissao.id} criada pelo autor {usuario.id} (status: {submissao.status})')
        return submissao

    @classmethod
    @transaction.atomic
    def atualizar_submissao(
        cls,
        submissao: Submissao,
        dados_submissao: Dict[str, Any],
        usuario: Usuario,
    ) -> Submissao:
        if not cls.usuario_pode_editar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para editar esta submissão.'))

        if not submissao.pode_editar:
            raise ValidationError(
                _('Submissão no status "%(status)s" não pode ser editada.'),
                params={'status': submissao.get_status_display()},
            )

        dados = dados_submissao.copy()
        dados.pop('evento', None)
        dados.pop('autor_principal', None)

        for attr, value in dados.items():
            setattr(submissao, attr, value)

        submissao.full_clean()
        submissao.save()

        logger.info(f'Submissão {submissao.id} atualizada por usuário {usuario.id}')
        return submissao

    @classmethod
    @transaction.atomic
    def submeter_trabalho(cls, submissao: Submissao, arquivo, usuario: Usuario) -> SubmissaoVersao:
        if not cls.usuario_pode_editar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para submeter este trabalho.'))

        if not submissao.pode_submeter:
            raise ValidationError(
                _('A submissão não pode ser enviada neste momento. Verifique o status e o período de submissão.')
            )

        validar_arquivo_submissao(arquivo)

        numero_versao = submissao.versoes.count() + 1

        versao = SubmissaoVersao(
            submissao=submissao,
            numero_versao=numero_versao,
            caminho_arquivo=arquivo,
        )
        versao.full_clean()
        versao.save()

        submissao.status = StatusSubmissao.SUBMETIDA
        submissao.save()

        logger.info(f'Trabalho {submissao.id} submetido em versão {numero_versao} por usuário {usuario.id}')
        return versao

    @classmethod
    @transaction.atomic
    def criar_avaliacao(
        cls,
        submissao: Submissao,
        avaliador: Usuario,
        status_parecer: str,
        observacoes: str,
        pontuacao: Optional[float] = None,
    ) -> Avaliacao:
        if not cls.usuario_pode_avaliar_submissao(avaliador, submissao):
            raise PermissionDenied(_('Você não tem permissão para avaliar esta submissão.'))

        avaliacao = Avaliacao(
            submissao=submissao,
            avaliador=avaliador,
            status_parecer=status_parecer,
            observacoes=observacoes,
            pontuacao=pontuacao,
        )

        avaliacao.full_clean()
        avaliacao.save()

        if submissao.status not in {StatusSubmissao.EM_AVALIACAO, StatusSubmissao.CORRECOES_SOLICITADAS}:
            submissao.status = StatusSubmissao.EM_AVALIACAO
            submissao.save()

        logger.info(f'Avaliação criada para submissão {submissao.id} por avaliador {avaliador.id}')
        return avaliacao

    @classmethod
    @transaction.atomic
    def aprovar_submissao(cls, submissao: Submissao, usuario: Usuario, observacoes: str = '') -> Submissao:
        if not cls.usuario_pode_avaliar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para aprovar esta submissão.'))

        submissao.status = StatusSubmissao.APROVADA
        submissao.save()

        logger.info(f'Submissão {submissao.id} aprovada por usuário {usuario.id}')
        return submissao

    @classmethod
    @transaction.atomic
    def rejeitar_submissao(cls, submissao: Submissao, usuario: Usuario, motivo: str) -> Submissao:
        if not cls.usuario_pode_avaliar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para rejeitar esta submissão.'))

        submissao.status = StatusSubmissao.REJEITADA
        submissao.save()

        Avaliacao.objects.create(
            submissao=submissao,
            avaliador=usuario,
            status_parecer=StatusParecer.REJEITADO,
            observacoes=motivo,
        )

        logger.info(f'Submissão {submissao.id} rejeitada por usuário {usuario.id}')
        return submissao

    @classmethod
    @transaction.atomic
    def solicitar_correcao(
        cls,
        submissao: Submissao,
        usuario: Usuario,
        observacoes: str,
    ) -> Submissao:
        if not cls.usuario_pode_avaliar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para solicitar correção nesta submissão.'))

        submissao.status = StatusSubmissao.CORRECOES_SOLICITADAS
        submissao.save()

        Avaliacao.objects.create(
            submissao=submissao,
            avaliador=usuario,
            status_parecer=StatusParecer.NECESSITA_CORRECAO,
            observacoes=observacoes,
        )

        logger.info(f'Correção solicitada para submissão {submissao.id} por usuário {usuario.id}')
        return submissao

    @classmethod
    def agendar_apresentacao(
        cls,
        submissao: Submissao,
        local: Local,
        inicio,
        duracao_minutos: int,
        usuario: Usuario,
    ) -> Apresentacao:
        if not cls.usuario_pode_avaliar_submissao(usuario, submissao):
            raise PermissionDenied(_('Você não tem permissão para agendar apresentações desta submissão.'))

        if submissao.status != StatusSubmissao.APROVADA:
            raise ValidationError(
                _('Apenas submissões aprovadas podem ter apresentações agendadas.')
            )

        apresentacao = Apresentacao(
            submissao=submissao,
            local=local,
            inicio=inicio,
            duracao_minutos=duracao_minutos,
        )

        apresentacao.full_clean()
        apresentacao.save()

        logger.info(f'Apresentação agendada para submissão {submissao.id} por usuário {usuario.id}')
        return apresentacao
