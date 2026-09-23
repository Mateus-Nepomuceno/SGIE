from rest_framework.exceptions import ValidationError
from django.utils import timezone

def validar_periodo_inscricao(evento):
    if not evento.inscricoes_abertas_status():
        raise ValidationError("As inscrições para este evento ainda não começou.")

def validar_inscricao_duplicada(usuario, evento, modelo_inscricao):
    if modelo_inscricao.objects.filter(usuario=usuario, evento=evento).exists():
        raise ValidationError("Já existe uma inscrição sua para este evento.")
