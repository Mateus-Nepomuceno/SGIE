from django.db import transaction
from rest_framework.exceptions import ValidationError
from .validators import validar_periodo_inscricao
from .models import Inscricao

@transaction.atomic
def criar_inscricao_servico(usuario, evento, comprovante=None, dados_adicionais=None):
    validar_periodo_inscricao(evento)
    validar_inscricao_duplicada(usuario, evento, Inscricao)

    inscricoes_ocupadas = Inscricao.objects.filter(
        evento=evento,
        status__in=['confirmada', 'pendente_pagamento']
    ).count()

    status_inscricao = 'confirmada'

    if inscricoes_ocupadas >= evento.capacidade:
        status_inscricao = 'lista_espera'
    elif not getattr(evento, 'e_gratuito'):
        status_inscricao = 'pendente_pagamento'

    inscricao = Inscricao(
        usuario=usuario,
        evento=evento,
        status=status_inscricao,
        dados_adicionais=dados_adicionais or {}
    )

    if comprovante:
        inscricao.comprovante = comprovante

    inscricao.save()
    return inscricao

def processar_fila_espera(evento):
    vagas_ocupadas = Inscricao.objects.filter(
        evento=evento,
        status__in=['confirmada', 'pendente_pagamento']
    ).count()

    vagas_livres = evento.capacidade - vagas_ocupadas

    if vagas_livres > 0:
        proximos = Inscricao.objects.filter(
            evento=evento,
            status='lista_espera'
        ).order_by('data_inscricao')[:vagas_livres]

        for inscricao in proximos:
            inscricao.status = 'confirmada' if getattr(evento, 'e_gratuito') else 'pendente_pagamaneto'
            inscricao.save()
