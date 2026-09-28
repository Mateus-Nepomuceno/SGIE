import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional, override

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from inscricao.models import Inscricao
from inscricao.services import processar_fila_espera
from pagamentos.models import (
    Canal,
    CategoriaPreco,
    Cobranca,
    Comunicacao,
    IsencaoPagamento,
    Lote,
    MetodoPagamento,
    Pagamento,
    Reembolso,
    StatusCobranca,
    StatusPagamento,
    StatusReembolso,
    TipoIsencao,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# DTOs de Retorno do Gateway
# -----------------------------------------------------------------------------


@dataclass
class ResultadoProcessamentoPagamento:
    sucesso: bool
    status: StatusPagamento
    transacao_id: str = ''
    qr_code_pix: str = ''
    url_pagamento: str = ''
    detalhes: dict[str, Any] = field(default_factory=dict)
    mensagem_erro: str = ''


@dataclass
class ResultadoProcessamentoReembolso:
    sucesso: bool
    status: StatusReembolso
    transacao_reembolso_id: str = ''
    detalhes: dict[str, Any] = field(default_factory=dict)
    mensagem_erro: str = ''


# -----------------------------------------------------------------------------
# Interface do Gateway de Pagamento (<<interface>> GatewayPagamento)
# -----------------------------------------------------------------------------


class GatewayPagamento(ABC):
    """
    Contrato para a integração com provedores de pagamento externos (PSP).
    Representa a interface GatewayPagamento descrita no DIAGRAMA_DE_CLASSE.md.
    """

    nome: str = 'BaseGateway'

    @abstractmethod
    def enviar_pagamento(
        self,
        pagamento: Pagamento,
        dados_cartao: Optional[dict[str, Any]] = None,
        retorno_url: str = '',
    ) -> ResultadoProcessamentoPagamento:
        """
        Envia a requisição de pagamento ao PSP externo.
        Corresponde ao método enviarPagamento(dados, valor, método, retornoURL).
        """
        pass

    @abstractmethod
    def consultar_pagamento(self, transacao_id: str) -> ResultadoProcessamentoPagamento:
        """Consulta o status de uma transação diretamente no PSP."""
        pass

    @abstractmethod
    def enviar_reembolso(
        self,
        reembolso: Reembolso,
    ) -> ResultadoProcessamentoReembolso:
        """Processa a solicitação de estorno/reembolso no PSP."""
        pass


# -----------------------------------------------------------------------------
# Implementação Padrão/Simulada (Sandbox Mock Gateway)
# -----------------------------------------------------------------------------


class GatewaySimulado(GatewayPagamento):
    """
    Gateway de Pagamento Simulado para testes, desenvolvimento e ambiente sandbox.
    Gera códigos Pix copia-e-cola válidos em formato texto, boletos fictícios
    e processa pagamentos via cartão de forma determinística.
    """

    nome: str = 'GatewaySimulado'

    @override
    def enviar_pagamento(  # noqa: PLR0912
        self,
        pagamento: Pagamento,
        dados_cartao: Optional[dict[str, Any]] = None,
        retorno_url: str = '',
    ) -> ResultadoProcessamentoPagamento:
        transacao_id = f'SIM-{uuid.uuid4().hex[:12].upper()}'
        detalhes = {
            'gateway': self.nome,
            'metodo': pagamento.metodo,
            'valor': str(pagamento.valor),
            'timestamp': timezone.now().isoformat(),
        }

        # Simulação por método
        if pagamento.metodo == MetodoPagamento.PIX:
            qr_code = f'00020126580014BR.GOV.BCB.PIX0136{uuid.uuid4()}520400005303986540{pagamento.valor:.2f}5802BR5913SGIE EVENTOS6008SALVADOR62070503***6304ABCD'
            detalhes['qr_code'] = qr_code
            return ResultadoProcessamentoPagamento(
                sucesso=True,
                status=StatusPagamento.PROCESSANDO,
                transacao_id=transacao_id,
                qr_code_pix=qr_code,
                detalhes=detalhes,
            )

        if pagamento.metodo == MetodoPagamento.BOLETO:
            url_boleto = f'https://sandbox.pagamentos.sgie.edu.br/boletos/{transacao_id}.pdf'
            detalhes['url_boleto'] = url_boleto
            return ResultadoProcessamentoPagamento(
                sucesso=True,
                status=StatusPagamento.PROCESSANDO,
                transacao_id=transacao_id,
                url_pagamento=url_boleto,
                detalhes=detalhes,
            )

        if pagamento.metodo in {MetodoPagamento.CARTAO_CREDITO, MetodoPagamento.CARTAO_DEBITO}:
            # Se fornecido cartão com final '0000', simula recusa/erro para testes
            numero_cartao = (dados_cartao or {}).get('numero_cartao', '')
            if str(numero_cartao).endswith('0000'):
                return ResultadoProcessamentoPagamento(
                    sucesso=False,
                    status=StatusPagamento.RECUSADO,
                    transacao_id=transacao_id,
                    detalhes={**detalhes, 'motivo_recusa': 'Saldo insuficiente ou cartão inválido'},
                    mensagem_erro='Pagamento com cartão recusado pela operadora.',
                )

            # Caso padrão: aprovado
            return ResultadoProcessamentoPagamento(
                sucesso=True,
                status=StatusPagamento.APROVADO,
                transacao_id=transacao_id,
                detalhes={**detalhes, 'nsu': '123456', 'autorizacao': 'AUTH-789'},
            )

        return ResultadoProcessamentoPagamento(
            sucesso=False,
            status=StatusPagamento.RECUSADO,
            transacao_id=transacao_id,
            mensagem_erro='Método de pagamento não suportado.',
        )

    @override
    def consultar_pagamento(self, transacao_id: str) -> ResultadoProcessamentoPagamento:
        return ResultadoProcessamentoPagamento(
            sucesso=True,
            status=StatusPagamento.APROVADO,
            transacao_id=transacao_id,
            detalhes={'consulta_simulada': True},
        )

    @override
    def enviar_reembolso(self, reembolso: Reembolso) -> ResultadoProcessamentoReembolso:
        transacao_reembolso_id = f'REF-{uuid.uuid4().hex[:12].upper()}'
        return ResultadoProcessamentoReembolso(
            sucesso=True,
            status=StatusReembolso.CONCLUIDO,
            transacao_reembolso_id=transacao_reembolso_id,
            detalhes={'valor': str(reembolso.valor), 'data': timezone.now().isoformat()},
        )


# -----------------------------------------------------------------------------
# Serviço de Notificações (Serviço de Notificações do Diagrama de Sequência)
# -----------------------------------------------------------------------------


class ServicoNotificacao:
    """
    Gerencia avisos por e-mail e persistência de mensagens de pós-evento/pagamento.
    """

    @staticmethod
    def notificar_participante(  # noqa: PLR0913, PLR0917
        destinatario,
        assunto: str,
        mensagem: str,
        canal: Canal = Canal.EMAIL,
        certificado=None,
    ) -> Comunicacao:
        """Registra a comunicação no banco e dispara e-mail se o canal for EMAIL."""
        comunicacao = Comunicacao.objects.create(
            destinatario=destinatario,
            certificado=certificado,
            canal=canal,
            assunto=assunto,
            mensagem=mensagem,
        )

        if canal == Canal.EMAIL and destinatario.email:
            try:
                send_mail(
                    subject=assunto,
                    message=mensagem,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'sgie@universidade.edu.br'),
                    recipient_list=[destinatario.email],
                    fail_silently=True,
                )
                comunicacao.enviado = True
                comunicacao.data_envio = timezone.now()
                comunicacao.save(update_fields=['enviado', 'data_envio'])
            except Exception as e:
                logger.warning(f'Falha no envio de e-mail para {destinatario.email}: {e}')

        return comunicacao


# -----------------------------------------------------------------------------
# Serviço de Cobrança (Serviço de Cobranças do Diagrama de Sequência)
# -----------------------------------------------------------------------------


class ServicoCobranca:
    """
    Responsável pelo faturamento, cálculo de valores de lote, vigência e isenções.
    Corresponde ao Serviço de Cobranças do DIAGRAMA_DE_SEQUENCIA_DE_PAGAMENTOS.md.
    """

    @staticmethod
    @transaction.atomic
    def gerar_cobranca(
        inscricao: Inscricao,
        categoria: Optional[CategoriaPreco] = None,
        lote: Optional[Lote] = None,
        dias_vencimento: int = 3,
    ) -> Cobranca:
        """
        Cria a cobrança para a inscrição com status PENDENTE e valor calculado (Passos 3 a 5).
        """
        if inscricao.evento.e_gratuito:
            raise ValidationError(_('Este evento é gratuito e não demanda geração de cobrança.'))

        # Determina o lote aplicável se não fornecido explicitamente
        if not lote and categoria:
            lote = categoria.lotes.filter(ativo=True).order_by('numero', 'data_inicio').first()

        # Calcula o valor original
        if lote:
            if not lote.esta_vigente:
                raise ValidationError(_('O lote selecionado não está vigente no momento.'))
            if not lote.tem_vagas:
                raise ValidationError(_('O lote selecionado não possui mais vagas disponíveis.'))
            valor = lote.preco
        else:
            valor = getattr(inscricao.evento, 'preco', Decimal('0.00'))

        data_vencimento = timezone.now() + timezone.timedelta(days=dias_vencimento)

        cobranca = Cobranca.objects.create(
            inscricao=inscricao,
            lote=lote,
            valor_original=valor,
            valor_final=valor,
            status=StatusCobranca.PENDENTE,
            data_vencimento=data_vencimento,
        )

        logger.info(f'Cobrança #{cobranca.id} gerada para a inscrição #{inscricao.id} no valor de R$ {valor}.')
        return cobranca

    @staticmethod
    @transaction.atomic
    def conceder_isencao(  # noqa: PLR0913, PLR0917
        cobranca: Cobranca,
        tipo: TipoIsencao,
        motivo: str,
        aprovado_por,
        desconto_percentual: Optional[Decimal] = None,
        desconto_valor: Optional[Decimal] = None,
    ) -> IsencaoPagamento:
        """
        Registra uma isenção/abatimento na cobrança e recalcula o valor_final (UC4).
        Se a isenção resultar em valor zerado (ou for TOTAL), a cobrança é quitada
        e a inscrição do participante é confirmada automaticamente.
        """
        if cobranca.status == StatusCobranca.PAGA:
            raise ValidationError(_('Não é possível conceder isenção em uma cobrança já paga.'))

        isencao, _created = IsencaoPagamento.objects.update_or_create(
            cobranca=cobranca,
            defaults={
                'tipo': tipo,
                'motivo': motivo,
                'aprovado_por': aprovado_por,
                'desconto_percentual': desconto_percentual or Decimal('0.00'),
                'desconto_valor': desconto_valor or Decimal('0.00'),
            },
        )
        isencao.aplicar_a_cobranca()

        if cobranca.valor_final == Decimal('0.00'):
            inscricao = cobranca.inscricao
            inscricao.status = 'confirmada'
            inscricao.save(update_fields=['status'])

            # Decrementa vaga do lote se houver
            if cobranca.lote and cobranca.lote.quantidade_disponivel > 0:
                cobranca.lote.quantidade_disponivel -= 1
                cobranca.lote.save(update_fields=['quantidade_disponivel'])

            ServicoNotificacao.notificar_participante(
                destinatario=inscricao.usuario,
                assunto=f'Inscrição Confirmada (Isenção) - {inscricao.evento.nome}',
                mensagem=f'Olá {inscricao.usuario.nome_completo}, sua inscrição no evento {inscricao.evento.nome} foi confirmada mediante concessão de isenção de pagamento.',
            )

        return isencao


# -----------------------------------------------------------------------------
# Serviço de Pagamento (ServicoPagamento do Diagrama de Classes e Sequência)
# -----------------------------------------------------------------------------


class ServicoPagamento:
    """
    Orquestrador da lógica de pagamentos e transições de estado financeiras.
    Integra-se com a interface GatewayPagamento para processamento de transações e reembolsos.
    """

    def __init__(self, gateway: Optional[GatewayPagamento] = None):
        self.gateway = gateway or GatewaySimulado()

    @transaction.atomic
    def processar_pagamento(  # noqa: PLR0913, PLR0917
        self,
        cobranca: Cobranca,
        metodo_pagamento: MetodoPagamento,
        valor: Optional[Decimal] = None,
        dados_cartao: Optional[dict[str, Any]] = None,
        retorno_url: str = '',
    ) -> Pagamento:
        """
        Executa o fluxo completo de pagamento:
        1. Cria o pagamento associado à cobrança (status PENDENTE).
        2. Transiciona o status para PROCESSANDO.
        3. Envia os dados para o Gateway / PSP.
        4. Avalia a resposta do Gateway:
           - Se APROVADO: confirma a inscrição, abate lote e notifica o participante.
           - Se RECUSADO: notifica falha e mantém a inscrição pendente.
        """
        if cobranca.status == StatusCobranca.PAGA:
            raise ValidationError(_('Esta cobrança já foi quitada.'))
        if cobranca.esta_vencida:
            cobranca.status = StatusCobranca.EXPIRADA
            cobranca.save(update_fields=['status'])
            raise ValidationError(_('A data de vencimento desta cobrança expirou.'))

        valor_pagamento = valor or cobranca.valor_final

        # Cria a instância de pagamento
        pagamento = Pagamento.objects.create(
            cobranca=cobranca,
            valor=valor_pagamento,
            metodo=metodo_pagamento,
            status=StatusPagamento.PENDENTE,
            gateway_nome=self.gateway.nome,
        )

        # Transiciona para PROCESSANDO
        pagamento.atualizar_status(StatusPagamento.PROCESSANDO)

        # Envia ao Gateway externo (Passo 9)
        resultado = self.gateway.enviar_pagamento(
            pagamento=pagamento,
            dados_cartao=dados_cartao,
            retorno_url=retorno_url,
        )

        # Atualiza status e metadados no pagamento (Passo 11)
        pagamento.qr_code_pix = resultado.qr_code_pix
        pagamento.url_pagamento = resultado.url_pagamento
        pagamento.atualizar_status(
            novo_status=resultado.status,
            transacao_id=resultado.transacao_id,
            detalhes=resultado.detalhes,
        )

        # Avaliação de Cenários Alternativos (Passos 13 a 20)
        inscricao = cobranca.inscricao

        if resultado.status == StatusPagamento.APROVADO:
            # Cenário 1: [status = APROVADO]
            cobranca.status = StatusCobranca.PAGA
            cobranca.save(update_fields=['status'])

            inscricao.status = 'confirmada'
            inscricao.save(update_fields=['status'])

            # Atualiza vagas do lote se aplicável
            if cobranca.lote and cobranca.lote.quantidade_disponivel > 0:
                cobranca.lote.quantidade_disponivel -= 1
                cobranca.lote.save(update_fields=['quantidade_disponivel'])

            ServicoNotificacao.notificar_participante(
                destinatario=inscricao.usuario,
                assunto=f'Pagamento Aprovado - {inscricao.evento.nome}',
                mensagem=(f'Olá {inscricao.usuario.nome_completo},\n\nSeu pagamento de R$ {valor_pagamento:.2f} para o evento "{inscricao.evento.nome}" foi confirmado com sucesso! Sua inscrição está confirmada.\nTransação: {resultado.transacao_id}'),
            )
            logger.info(f'Pagamento #{pagamento.id} aprovado. Inscrição #{inscricao.id} confirmada.')

        elif resultado.status == StatusPagamento.RECUSADO:
            # Cenário 2: [status = RECUSADO ou ERRO]
            ServicoNotificacao.notificar_participante(
                destinatario=inscricao.usuario,
                assunto=f'Falha no Pagamento - {inscricao.evento.nome}',
                mensagem=(f'Olá {inscricao.usuario.nome_completo},\n\nNão foi possível aprovar seu pagamento no valor de R$ {valor_pagamento:.2f}.\nMotivo: {resultado.mensagem_erro or "Transação não autorizada pela instituição bancária."}\nPor favor, tente novamente utilizando outro método de pagamento.'),
            )
            logger.warning(f'Pagamento #{pagamento.id} recusado para a inscrição #{inscricao.id}.')

        return pagamento

    @staticmethod
    @transaction.atomic
    def processar_notificacao_webhook(
        transacao_id: str,
        novo_status: StatusPagamento,
        detalhes: Optional[dict[str, Any]] = None,
    ) -> Pagamento:
        """
        Atualiza o pagamento de forma assíncrona após notificação webhook do PSP.
        """
        try:
            pagamento = Pagamento.objects.select_for_update().get(transacao_id=transacao_id)
        except Pagamento.DoesNotExist:
            raise ValidationError(_('Transação de pagamento não localizada.'))

        if pagamento.status == novo_status:
            return pagamento

        pagamento.atualizar_status(novo_status=novo_status, detalhes=detalhes)
        cobranca = pagamento.cobranca
        inscricao = cobranca.inscricao

        if novo_status == StatusPagamento.APROVADO:
            cobranca.status = StatusCobranca.PAGA
            cobranca.save(update_fields=['status'])

            inscricao.status = 'confirmada'
            inscricao.save(update_fields=['status'])

            if cobranca.lote and cobranca.lote.quantidade_disponivel > 0:
                cobranca.lote.quantidade_disponivel -= 1
                cobranca.lote.save(update_fields=['quantidade_disponivel'])

            ServicoNotificacao.notificar_participante(
                destinatario=inscricao.usuario,
                assunto=f'Pagamento Confirmado - {inscricao.evento.nome}',
                mensagem='Seu pagamento foi aprovado com sucesso via webhook! Inscrição confirmada.',
            )

        return pagamento

    @transaction.atomic
    def solicitar_reembolso(
        self,
        pagamento: Pagamento,
        motivo: str,
        solicitado_por,
        valor: Optional[Decimal] = None,
    ) -> Reembolso:
        """
        Processa reembolso de pagamento aprovado conforme UC10 e UC13.
        Ao concluir o reembolso:
        - Pagamento transiciona para REEMBOLSADO.
        - Cobrança é CANCELADA.
        - Inscrição é cancelada.
        - Se havia lote, a vaga é devolvida.
        - A fila de espera do evento é reprocessada.
        """
        if pagamento.status != StatusPagamento.APROVADO:
            raise ValidationError(_('Apenas pagamentos aprovados podem ser reembolsados.'))

        if hasattr(pagamento, 'reembolso'):
            raise ValidationError(_('Já existe um processo de reembolso para este pagamento.'))

        valor_reembolso = valor or pagamento.valor
        if valor_reembolso > pagamento.valor:
            raise ValidationError(_('O valor do reembolso não pode ser superior ao valor do pagamento.'))

        reembolso = Reembolso.objects.create(
            pagamento=pagamento,
            valor=valor_reembolso,
            motivo=motivo,
            solicitado_por=solicitado_por,
            status=StatusReembolso.SOLICITADO,
        )

        # Envia comando de estorno ao Gateway
        resultado = self.gateway.enviar_reembolso(reembolso)

        if resultado.sucesso:
            reembolso.status = StatusReembolso.CONCLUIDO
            reembolso.transacao_reembolso_id = resultado.transacao_reembolso_id
            reembolso.data_conclusao = timezone.now()
            reembolso.save(update_fields=['status', 'transacao_reembolso_id', 'data_conclusao'])

            # Atualiza o ciclo de vida do pagamento
            pagamento.atualizar_status(StatusPagamento.REEMBOLSADO)

            cobranca = pagamento.cobranca
            cobranca.status = StatusCobranca.CANCELADA
            cobranca.save(update_fields=['status'])

            inscricao = cobranca.inscricao
            inscricao.status = 'cancelada'
            inscricao.save(update_fields=['status'])

            # Devolve vaga ao lote
            if cobranca.lote:
                cobranca.lote.quantidade_disponivel += 1
                cobranca.lote.save(update_fields=['quantidade_disponivel'])

            # Aciona processamento da fila de espera do evento
            processar_fila_espera(inscricao.evento)

            ServicoNotificacao.notificar_participante(
                destinatario=inscricao.usuario,
                assunto=f'Reembolso Concluído - {inscricao.evento.nome}',
                mensagem=(f'Olá {inscricao.usuario.nome_completo},\n\nSeu reembolso no valor de R$ {valor_reembolso:.2f} foi processado com sucesso.\nIdentificador do estorno: {resultado.transacao_reembolso_id}'),
            )
            logger.info(f'Reembolso #{reembolso.id} concluído para pagamento #{pagamento.id}.')
        else:
            reembolso.status = StatusReembolso.RECUSADO
            reembolso.save(update_fields=['status'])
            logger.error(f'Falha ao processar estorno no gateway: {resultado.mensagem_erro}')

        return reembolso
