from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

CAPACIDADE_MAXIMA_EVENTO = 10000
TAMANHO_MAXIMO_TITULO = 100


def validar_titulo_evento(valor: Optional[str]) -> None:
    if not valor or not valor.strip():
        raise ValidationError(_('O título do evento é obrigatório.'))

    texto = valor.strip()
    if len(texto) > TAMANHO_MAXIMO_TITULO:
        raise ValidationError(
            _('O título do evento deve possuir no máximo 100 caracteres. Tamanho atual: %(tamanho)d.'),
            params={'tamanho': len(texto)},
        )

    palavras = texto.split()
    for palavra in palavras:
        caractere_inicial = palavra[0]
        if caractere_inicial.isalpha() and not caractere_inicial.isupper():
            raise ValidationError(
                _('A letra inicial de todas as palavras do título deve ser maiúscula. Palavra inválida: "%(palavra)s".'),
                params={'palavra': palavra},
            )


def formatar_titulo_evento(valor: Optional[str]) -> str:
    if not valor:
        return ''
    palavras = valor.strip().split()
    return ' '.join(p[0].upper() + p[1:] if len(p) > 1 else p.upper() for p in palavras)


def validar_capacidade(valor: Optional[int]) -> None:
    if valor is None:
        raise ValidationError(_('A capacidade do evento é obrigatória.'))

    try:
        capacidade_int = int(valor)
    except (ValueError, TypeError):
        raise ValidationError(_('A capacidade deve ser um número inteiro válido.'))

    if capacidade_int <= 0:
        raise ValidationError(_('A capacidade deve ser superior a zero.'))

    if capacidade_int > CAPACIDADE_MAXIMA_EVENTO:
        raise ValidationError(
            _('A capacidade do evento não pode ultrapassar %(maximo)d inscritos.'),
            params={'maximo': CAPACIDADE_MAXIMA_EVENTO},
        )
