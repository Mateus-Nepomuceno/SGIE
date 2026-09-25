from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    EquipeOrganizadora,
    Evento,
    RegraSubmissao,
)


class EquipeOrganizadoraInline(admin.TabularInline):
    model = EquipeOrganizadora
    extra = 1


class RegraSubmissaoInline(admin.StackedInline):
    model = RegraSubmissao
    can_delete = False
    max_num = 1


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'nome',
        'categoria',
        'modalidade',
        'data',
        'hora_inicio',
        'status',
        'visibilidade',
        'e_gratuito',
        'capacidade',
        'usuario_representante',
    ]
    list_filter = ['status', 'modalidade', 'categoria', 'visibilidade', 'e_gratuito', 'data']
    search_fields = ['nome', 'descricao', 'local', 'usuario_representante__nome_completo', 'usuario_representante__email']
    readonly_fields = ['data_original', 'hora_inicio_original', 'cancelado_em', 'criado_em', 'atualizado_em']
    inlines = [
        EquipeOrganizadoraInline,
        RegraSubmissaoInline,
    ]
    fieldsets = [
        (
            _('Informações Básicas'),
            {
                'fields': [
                    'usuario_representante',
                    'nome',
                    'descricao',
                    'categoria',
                    'categoria_personalizada',
                    'modalidade',
                    'capacidade',
                    'visibilidade',
                ]
            },
        ),
        (
            _('Data, Horários e Local'),
            {
                'fields': [
                    'data',
                    'data_original',
                    'hora_inicio',
                    'hora_inicio_original',
                    'hora_fim',
                    'local_tipo',
                    'local',
                ]
            },
        ),
        (
            _('Cobrança e Preço'),
            {
                'fields': [
                    'e_gratuito',
                    'preco',
                    'necessita_comprovante',
                ]
            },
        ),
        (
            _('Ciclo de Vida e Programação Geral'),
            {
                'fields': [
                    'status',
                    'programacao_geral',
                    'motivo_cancelamento',
                    'cancelado_em',
                    'criado_em',
                    'atualizado_em',
                ]
            },
        ),
    ]


@admin.register(EquipeOrganizadora)
class EquipeOrganizadoraAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'email_publico', 'papel_funcao', 'evento']
    search_fields = ['nome', 'email_publico', 'evento__nome']


@admin.register(RegraSubmissao)
class RegraSubmissaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'evento', 'aceita_submissao', 'data_hora_inicio', 'data_hora_fim']
    list_filter = ['aceita_submissao']
