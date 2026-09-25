from django.conf import settings
from django.db import models

from eventos.models import Evento

from .validators import validar_inscricao_duplicada, validar_periodo_inscricao


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

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not self.pk:
            validar_periodo_inscricao(self.evento)
        validar_inscricao_duplicada(self.usuario, self.evento, Inscricao, instance=self)
