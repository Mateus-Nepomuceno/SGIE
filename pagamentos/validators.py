import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# =============================================================================
# Constantes de Domínio e Limites Operacionais
# =============================================================================

VALOR_MINIMO_TRANSACAO = Decimal('0.01')
DESCONTO_PERCENTUAL_MINIMO = Decimal('0.00')
DESCONTO_PERCENTUAL_MAXIMO = Decimal('100.00')
DIAS_MINIMOS_VENCIMENTO = 1
DIAS_MAXIMOS_VENCIMENTO = 60
PRAZO_MAXIMO_REEMBOLSO_DIAS = 7

TAMANHO_MIN_CARTAO = 13
TAMANHO_MAX_CARTAO = 19
TAMANHO_CVV = (3, 4)
TAMANHO_MAXIMO_TRANSACAO_ID = 255
TAMANHO_MIN_NOME_TITULAR = 3

LIMITE_DIGITO_LUHN = 9
MES_MINIMO = 1
MES_MAXIMO = 12
LIMITE_ANO_DOIS_DIGITOS = 100
SECULO_BASE = 2000


# =============================================================================
# Helpers de Limpeza e Formatação
# =============================================================================


def limpar_digitos(valor: Optional[Union[str, int]]) -> str:
    """Remove caracteres não numéricos do valor fornecido."""
    if not valor:
        return ''
    return re.sub(r'\D', '', str(valor))


# =============================================================================
# Validações Numéricas e Valores Financeiros
# =============================================================================


def validar_valor_minimo_positivo(valor: Optional[Decimal]) -> None:
    """
    Valida se o montante financeiro é fornecido e superior ou igual ao piso transacional (R$ 0,01).
    """
    if valor is None:
        raise ValidationError(_('O valor financeiro é obrigatório.'), code='valor_obrigatorio')

    try:
        valor_decimal = Decimal(str(valor))
    except Exception:
        raise ValidationError(_('O valor financeiro deve ser um número decimal válido.'), code='valor_invalido')

    if valor_decimal < VALOR_MINIMO_TRANSACAO:
        raise ValidationError(
            _('O valor deve ser de no mínimo R$ %(minimo)s.'),
            params={'minimo': str(VALOR_MINIMO_TRANSACAO)},
            code='valor_inferior_minimo',
        )


def validar_intervalo_datas(data_inicio: Optional[datetime], data_fim: Optional[datetime]) -> None:
    """
    Garante que a data de término seja estritamente posterior à data de início.
    """
    if data_inicio and data_fim and data_inicio >= data_fim:
        raise ValidationError(
            _('A data de término deve ser posterior à data de início.'),
            code='data_fim_invalida',
        )


def validar_quantidade_vagas_lote(quantidade_total: Optional[int], quantidade_disponivel: Optional[int]) -> None:
    """
    Garante a coerência entre as vagas totais e vagas disponíveis do lote.
    """
    if quantidade_total is not None and quantidade_total < 1:
        raise ValidationError(
            _('A quantidade total do lote deve ser de pelo menos 1 vaga.'),
            code='quantidade_total_invalida',
        )

    if quantidade_disponivel is not None and quantidade_total is not None:
        if quantidade_disponivel > quantidade_total:
            raise ValidationError(
                _('A quantidade disponível (%(disp)d) não pode ser superior à quantidade total (%(tot)d).'),
                params={'disp': quantidade_disponivel, 'tot': quantidade_total},
                code='quantidade_disponivel_excedida',
            )


def validar_desconto_isencao(
    tipo: str,
    desconto_percentual: Optional[Decimal],
    desconto_valor: Optional[Decimal],
    valor_original: Optional[Decimal] = None,
) -> None:
    """
    Valida regras de concessão de desconto para isenções totais ou parciais (UC4).
    """
    if tipo == 'TOTAL':
        return

    if tipo == 'PARCIAL':
        percentual = Decimal(str(desconto_percentual or '0.00'))
        valor = Decimal(str(desconto_valor or '0.00'))

        if percentual <= Decimal('0.00') and valor <= Decimal('0.00'):
            raise ValidationError(
                _('Para isenção parcial, informe um percentual ou valor de desconto válido superior a zero.'),
                code='isencao_parcial_sem_desconto',
            )

        if percentual < DESCONTO_PERCENTUAL_MINIMO or percentual > DESCONTO_PERCENTUAL_MAXIMO:
            raise ValidationError(
                _('O desconto percentual deve estar entre 0%% e 100%%.'),
                code='desconto_percentual_invalido',
            )

        if valor < Decimal('0.00'):
            raise ValidationError(
                _('O valor de desconto não pode ser negativo.'),
                code='desconto_valor_negativo',
            )

        if valor_original is not None and valor > valor_original:
            raise ValidationError(
                _('O valor do desconto (R$ %(desc)s) não pode exceder o valor original (R$ %(orig)s).'),
                params={'desc': str(valor), 'orig': str(valor_original)},
                code='desconto_excede_valor_original',
            )


def validar_valor_reembolso(valor_reembolso: Optional[Decimal], valor_pagamento: Optional[Decimal]) -> None:
    """
    Valida se o valor de reembolso solicitado é válido e não excede o valor efetivamente pago.
    """
    validar_valor_minimo_positivo(valor_reembolso)

    if valor_pagamento is not None:
        reembolso_dec = Decimal(str(valor_reembolso))
        pago_dec = Decimal(str(valor_pagamento))
        if reembolso_dec > pago_dec:
            raise ValidationError(
                _('O valor do reembolso (R$ %(reemb)s) não pode ser superior ao valor pago (R$ %(pago)s).'),
                params={'reemb': str(reembolso_dec), 'pago': str(pago_dec)},
                code='reembolso_superior_ao_pago',
            )


# =============================================================================
# Validações de Cartão de Crédito e Débito (Luhn & Metadados)
# =============================================================================


def validar_numero_cartao(numero: Optional[str]) -> None:
    """
    Valida o número do cartão utilizando o Algoritmo de Luhn (Módulo 10)
    e checa restrições de comprimento internacional (ISO/IEC 7812).
    """
    digitos = limpar_digitos(numero)
    if len(digitos) < TAMANHO_MIN_CARTAO or len(digitos) > TAMANHO_MAX_CARTAO:
        raise ValidationError(
            _('Número de cartão inválido: deve conter entre 13 e 19 dígitos numéricos.'),
            code='cartao_comprimento_invalido',
        )

    # Verificação do Algoritmo de Luhn (Módulo 10)
    soma = 0
    inverter = False
    for char in reversed(digitos):
        d = int(char)
        if inverter:
            d *= 2
            if d > LIMITE_DIGITO_LUHN:
                d -= LIMITE_DIGITO_LUHN
        soma += d
        inverter = not inverter

    if soma % 10 != 0:
        raise ValidationError(
            _('Número de cartão de crédito/débito inválido (dígito verificador incorreto).'),
            code='cartao_luhn_invalido',
        )


def validar_cvv(cvv: Optional[str]) -> None:
    """Valida o código de segurança do cartão (CVV/CVC: 3 ou 4 dígitos numéricos)."""
    digitos = limpar_digitos(cvv)
    if len(digitos) not in TAMANHO_CVV:
        raise ValidationError(
            _('Código de segurança (CVV) inválido. Deve conter 3 ou 4 dígitos numéricos.'),
            code='cvv_invalido',
        )


def validar_validade_cartao(mes: Optional[Union[int, str]], ano: Optional[Union[int, str]]) -> None:
    """Valida o mês e ano de expiração do cartão frente à data corrente."""
    if not mes or not ano:
        raise ValidationError(_('Mês e ano de validade do cartão são obrigatórios.'), code='validade_obrigatoria')

    try:
        mes_int = int(mes)
        ano_int = int(ano)
    except (ValueError, TypeError):
        raise ValidationError(_('Mês e ano de validade devem ser numéricos.'), code='validade_nao_numerica')

    if mes_int < MES_MINIMO or mes_int > MES_MAXIMO:
        raise ValidationError(_('Mês de validade inválido. Deve estar entre 01 e 12.'), code='mes_invalido')

    # Suporta representação em 2 dígitos (ex: 26 -> 2026)
    if ano_int < LIMITE_ANO_DOIS_DIGITOS:
        ano_int += SECULO_BASE

    hoje = timezone.now().date()
    if ano_int < hoje.year or (ano_int == hoje.year and mes_int < hoje.month):
        raise ValidationError(_('O cartão informado encontra-se expirado.'), code='cartao_expirado')


def validar_dados_cartao(dados_cartao: Optional[Dict[str, Any]], exigir_completo: bool = True) -> None:
    """
    Validação agregada do payload de cartão enviado ao gateway de pagamento.
    Permite modo flexível para mocks em ambiente de desenvolvimento quando exigir_completo=False.
    """
    if not dados_cartao or not isinstance(dados_cartao, dict):
        raise ValidationError(_('Os dados do cartão de crédito/débito são obrigatórios.'), code='dados_cartao_ausentes')

    numero_cartao = dados_cartao.get('numero_cartao')
    if not numero_cartao:
        raise ValidationError(_('O número do cartão é obrigatório.'), code='numero_cartao_obrigatorio')

    if exigir_completo:
        validar_numero_cartao(numero_cartao)
        validar_cvv(dados_cartao.get('cvv'))
        validar_validade_cartao(dados_cartao.get('mes_expiracao'), dados_cartao.get('ano_expiracao'))

        nome_titular = str(dados_cartao.get('nome_titular') or '').strip()
        if len(nome_titular) < TAMANHO_MIN_NOME_TITULAR:
            raise ValidationError(
                _('O nome impresso no cartão deve possuir no mínimo 3 caracteres.'),
                code='nome_titular_curto',
            )


# =============================================================================
# Validações de Pix e Gateway / Transação
# =============================================================================


def validar_payload_pix(payload: Optional[str]) -> None:
    """Valida o formato básico do payload copia-e-cola Pix (EMVCo BR Code)."""
    if not payload or not str(payload).strip():
        raise ValidationError(_('O código Pix Copia e Cola não pode ser vazio.'), code='pix_payload_vazio')

    texto = str(payload).strip()
    if not texto.startswith('000201') or 'BR.GOV.BCB.PIX' not in texto.upper():
        raise ValidationError(
            _('Payload do QR Code Pix em formato inválido ou não compatível com o padrão Bacen.'),
            code='pix_formato_invalido',
        )


def validar_transacao_id(transacao_id: Optional[str]) -> None:
    """Valida a consistência do identificador de transação retornado pelo Gateway/PSP."""
    if not transacao_id or not str(transacao_id).strip():
        raise ValidationError(_('O identificador da transação é obrigatório.'), code='transacao_id_obrigatorio')

    texto = str(transacao_id).strip()
    if len(texto) > TAMANHO_MAXIMO_TRANSACAO_ID:
        raise ValidationError(_('O identificador da transação excede o tamanho permitido.'), code='transacao_id_longo')


# =============================================================================
# Validações de Prazos e Regras de Negócio de Estado
# =============================================================================


def validar_cobranca_elegivel_para_pagamento(cobranca) -> None:
    """Valida se uma cobrança possui status elegível e prazo vigente para pagamento."""
    if getattr(cobranca, 'status', None) == 'PAGA':
        raise ValidationError(_('Esta cobrança já foi quitada.'), code='cobranca_ja_paga')
    if getattr(cobranca, 'esta_vencida', False):
        raise ValidationError(_('A data de vencimento desta cobrança expirou.'), code='cobranca_vencida')


def validar_solicitacao_reembolso(pagamento, limite_dias: int = PRAZO_MAXIMO_REEMBOLSO_DIAS) -> None:
    """Valida as condições de elegibilidade para solicitação de estorno/reembolso."""
    if getattr(pagamento, 'status', None) != 'APROVADO':
        raise ValidationError(
            _('Apenas pagamentos aprovados podem ser reembolsados.'),
            code='pagamento_nao_aprovado',
        )

    if hasattr(pagamento, 'reembolso'):
        raise ValidationError(
            _('Já existe um processo de reembolso para este pagamento.'),
            code='reembolso_duplicado',
        )

    data_pag = getattr(pagamento, 'data_pagamento', None)
    if data_pag:
        dias_decorridos = (timezone.now() - data_pag).days
        if dias_decorridos > limite_dias:
            raise ValidationError(
                _('O prazo limite para solicitação de reembolso (%(dias)d dias) foi ultrapassado.'),
                params={'dias': limite_dias},
                code='prazo_reembolso_expirado',
            )
