from django.db import models
from django.conf import settings
from eventos.models import Evento, CategoriaEvento
from .validators import validar_periodo_inscricao, validar_inscricao_duplicada

class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente_pagamento', 'Pendente de Pagamento'),
        ('confirmada', 'Confirmada'),
        ('lista_espera', 'Lista de Espera'),
        ('cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inscricoes')
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='inscricoes')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente_pagamento')
    comprovante = models.FileField(upload_to='comprovantes/', null=True, blank=True)
    dados_adicionais = models.JSONField(default=dict, blank=True, help_text="Respostas para campos personalizados")

    data_inscricao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'evento')

    def __str__(self):
        return f"{self.usuario.email} - {self.evento.nome} ({self.status})"

    def clean(self):
        super().clean()
        validar_periodo_inscricao(self.evento)
        validar_inscricao_duplicada(self.usuario, self.evento, Inscricao)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
