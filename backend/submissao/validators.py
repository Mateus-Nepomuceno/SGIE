from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TAMANHO_MAXIMO_TITULO_SUBMISSAO = 300
TAMANHO_MAXIMO_KEYWORDS = 500
TAMANHO_MAXIMO_URL = 500
PONTUACAO_MINIMA = 0
PONTUACAO_MAXIMA = 100
DURACAO_MAXIMA_MINUTOS = 1440


def validar_titulo_submissao(valor: Optional[str]) -> None:
    if not valor or not valor.strip():
        raise ValidationError(_('O título da submissão é obrigatório.'))

    texto = valor.strip()
    if len(texto) > TAMANHO_MAXIMO_TITULO_SUBMISSAO:
        raise ValidationError(
            _(
                'O título da submissão deve possuir no máximo %(maximo)d caracteres. '
                'Tamanho atual: %(tamanho)d.'
            ),
            params={'maximo': TAMANHO_MAXIMO_TITULO_SUBMISSAO, 'tamanho': len(texto)},
        )


def validar_abstract(valor: Optional[str]) -> None:
    if not valor or not valor.strip():
        raise ValidationError(_('O abstract/resumo da submissão é obrigatório.'))


def validar_palavras_chave(valor: Optional[str]) -> None:
    if not valor or not valor.strip():
        raise ValidationError(_('As palavras-chave são obrigatórias.'))

    if len(valor) > TAMANHO_MAXIMO_KEYWORDS:
        raise ValidationError(
            _(
                'As palavras-chave devem ter no máximo %(maximo)d caracteres. '
                'Tamanho atual: %(tamanho)d.'
            ),
            params={'maximo': TAMANHO_MAXIMO_KEYWORDS, 'tamanho': len(valor)},
        )


def validar_url(valor: Optional[str]) -> None:
    if not valor:
        return

    if not (valor.startswith('http://') or valor.startswith('https://')):
        raise ValidationError(_('A URL deve começar com http:// ou https://.'))

    if len(valor) > TAMANHO_MAXIMO_URL:
        raise ValidationError(
            _('A URL não pode ter mais de %(maximo)d caracteres. Tamanho atual: %(tamanho)d.'),
            params={'maximo': TAMANHO_MAXIMO_URL, 'tamanho': len(valor)},
        )


def validar_numero_versao(numero: Optional[int]) -> None:
    if numero is None:
        raise ValidationError(_('O número da versão é obrigatório.'))

    try:
        num_int = int(numero)
    except (ValueError, TypeError):
        raise ValidationError(_('O número da versão deve ser um inteiro válido.'))

    if num_int <= 0:
        raise ValidationError(_('O número da versão deve ser superior a zero.'))


def validar_pontuacao(valor: Optional[float]) -> None:
    if valor is None:
        return

    try:
        pontuacao_float = float(valor)
    except (ValueError, TypeError):
        raise ValidationError(_('A pontuação deve ser um número válido.'))

    if pontuacao_float < PONTUACAO_MINIMA or pontuacao_float > PONTUACAO_MAXIMA:
        raise ValidationError(_('A pontuação deve estar entre 0 e 100.'))


def validar_capacidade_local(valor: Optional[int]) -> None:
    if valor is None:
        return

    try:
        capacidade_int = int(valor)
    except (ValueError, TypeError):
        raise ValidationError(_('A capacidade deve ser um número inteiro válido.'))

    if capacidade_int <= 0:
        raise ValidationError(_('A capacidade deve ser superior a zero.'))


def validar_duracao_minutos(valor: Optional[int]) -> None:
    if valor is None:
        raise ValidationError(_('A duração em minutos é obrigatória.'))

    try:
        duracao_int = int(valor)
    except (ValueError, TypeError):
        raise ValidationError(_('A duração deve ser um número inteiro válido.'))

    if duracao_int <= 0:
        raise ValidationError(_('A duração deve ser superior a zero.'))

    if duracao_int > DURACAO_MAXIMA_MINUTOS:  # 24 horas em minutos
        raise ValidationError(_('A duração não pode ser superior a 24 horas (1440 minutos).'))


EXTENSOES_PERMITIDAS_SUBMISSAO = ['pdf', 'doc', 'docx']
TAMANHO_MAXIMO_ARQUIVO_SUBMISSAO_MB = 20
TAMANHO_MAXIMO_ARQUIVO_SUBMISSAO_BYTES = TAMANHO_MAXIMO_ARQUIVO_SUBMISSAO_MB * 1024 * 1024


def validar_arquivo_submissao(arquivo) -> None:
    """Valida se o arquivo de submissão possui extensão permitida e tamanho adequado."""
    if not arquivo:
        raise ValidationError(_('O arquivo da submissão é obrigatório.'))

    nome = getattr(arquivo, 'name', str(arquivo))
    ext = nome.split('.')[-1].lower() if '.' in nome else ''
    if ext not in EXTENSOES_PERMITIDAS_SUBMISSAO:
        raise ValidationError(
            _('Extensão de arquivo não permitida. Envie arquivos PDF, DOC ou DOCX.'),
            code='arquivo_extensao_invalida',
        )

    tamanho = getattr(arquivo, 'size', None)
    if tamanho and tamanho > TAMANHO_MAXIMO_ARQUIVO_SUBMISSAO_BYTES:
        raise ValidationError(
            _(
                'O arquivo excede o tamanho máximo permitido de %(max_mb)d MB.'
            ),
            params={'max_mb': TAMANHO_MAXIMO_ARQUIVO_SUBMISSAO_MB},
            code='arquivo_tamanho_excedido',
        )
