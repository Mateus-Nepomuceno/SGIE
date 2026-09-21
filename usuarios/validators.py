import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

TAMANHO_CPF = 11
TAMANHO_MIN_TELEFONE = 10
TAMANHO_MAX_TELEFONE = 11
PESO_BASE_DV1 = 10
PESO_BASE_DV2 = 11
MODULO_ONZE = 11
VALOR_CORTE_RESTO = 10


def limpar_cpf(valor: str) -> str:
    """Remove caracteres não numéricos do CPF."""
    if not valor:
        return ''
    return re.sub(r'\D', '', str(valor))


def formatar_cpf(valor: str) -> str:
    """Formata uma sequência de 11 dígitos no padrão 000.000.000-00."""
    digitos = limpar_cpf(valor)
    if len(digitos) != TAMANHO_CPF:
        return valor
    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


def validar_cpf(valor: str) -> None:
    """
    Valida matematicamente os dígitos verificadores do CPF (RF01, RN01).
    Lança ValidationError se o formato ou os cálculos dos dígitos forem inválidos.
    """
    cpf = limpar_cpf(valor)

    if len(cpf) != TAMANHO_CPF:
        raise ValidationError(_('O CPF deve conter exatamente 11 dígitos numéricos.'), code='cpf_tamanho_invalido')

    # Rejeita CPFs com todos os dígitos iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * TAMANHO_CPF:
        raise ValidationError(_('CPF inválido: sequência com dígitos repetidos.'), code='cpf_sequencia_invalida')

    # Validação do primeiro dígito verificador
    soma_1 = sum(int(cpf[i]) * (PESO_BASE_DV1 - i) for i in range(9))
    resto_1 = (soma_1 * 10) % MODULO_ONZE
    digito_esperado_1 = 0 if resto_1 >= VALOR_CORTE_RESTO else resto_1

    if int(cpf[9]) != digito_esperado_1:
        raise ValidationError(_('CPF inválido: primeiro dígito verificador incorreto.'), code='cpf_digito1_invalido')

    # Validação do segundo dígito verificador
    soma_2 = sum(int(cpf[i]) * (PESO_BASE_DV2 - i) for i in range(10))
    resto_2 = (soma_2 * 10) % MODULO_ONZE
    digito_esperado_2 = 0 if resto_2 >= VALOR_CORTE_RESTO else resto_2

    if int(cpf[10]) != digito_esperado_2:
        raise ValidationError(_('CPF inválido: segundo dígito verificador incorreto.'), code='cpf_digito2_invalido')


def validar_telefone(valor: str) -> None:
    """Valida formato mínimo de telefone com DDD."""
    digitos = re.sub(r'\D', '', str(valor))
    if len(digitos) < TAMANHO_MIN_TELEFONE or len(digitos) > TAMANHO_MAX_TELEFONE:
        raise ValidationError(_('O telefone informado deve conter DDD e número válido com 10 ou 11 dígitos.'), code='telefone_invalido')


def validar_extensao_imagem(arquivo) -> None:
    """Valida se o arquivo possui extensão de imagem suportada."""
    if not arquivo:
        return
    extensoes_permitidas = ['jpg', 'jpeg', 'png', 'webp']
    nome = getattr(arquivo, 'name', '')
    ext = nome.split('.')[-1].lower() if '.' in nome else ''
    if ext not in extensoes_permitidas:
        raise ValidationError(_('Extensão de arquivo não permitida. Envie imagens JPG, PNG ou WebP.'), code='imagem_extensao_invalida')
