from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    Apresentacao,
    Area,
    AtribuicaoAvaliacao,  # NOVO
    Avaliacao,
    Avaliador,  # já deve estar
    AvaliadorEvento,  # NOVO
    Local,
    Submissao,
    SubmissaoAutor,
    SubmissaoVersao,
)


class SubmissaoAutorInline(admin.TabularInline):
    model = SubmissaoAutor
    extra = 1
    fields = [
        'usuario',
        'tipo_participacao',
        'ordem_autoria',
        'lattes_url',
        'linkedin_url',
        'afiliacao_institucional',
        'maiór_titulacao',
    ]


class SubmissaoVersaoInline(admin.TabularInline):
    model = SubmissaoVersao
    extra = 0
    fields = ['numero_versao', 'caminho_arquivo', 'criado_em']
    readonly_fields = ['numero_versao', 'criado_em']
    can_delete = False


class AvaliacaoInline(admin.TabularInline):
    model = Avaliacao
    extra = 0
    fields = ['avaliador', 'status_parecer', 'pontuacao', 'criado_em']
    readonly_fields = ['criado_em']


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = [
        (
            _('Informações Básicas'),
            {'fields': ['nome', 'descricao']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(Submissao)
class SubmissaoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'titulo',
        'evento',
        'area',
        'tipo',
        'status',
        'autor_principal',
        'criado_em',
    ]
    list_filter = ['status', 'tipo', 'area', 'evento', 'criado_em']
    search_fields = ['titulo', 'abstract', 'autor_principal__nome_completo', 'autor_principal__email']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [SubmissaoAutorInline, SubmissaoVersaoInline, AvaliacaoInline]
    fieldsets = [
        (
            _('Informações Básicas'),
            {
                'fields': [
                    'evento',
                    'titulo',
                    'descricao',
                    'abstract',
                    'resumo',
                    'palavras_chave',
                ]
            },
        ),
        (
            _('Classificação'),
            {'fields': ['tipo', 'area', 'status']},
        ),
        (
            _('Autoria'),
            {'fields': ['autor_principal']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(SubmissaoAutor)
class SubmissaoAutorAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'usuario',
        'submissao',
        'tipo_participacao',
        'ordem_autoria',
        'criado_em',
    ]
    list_filter = ['tipo_participacao', 'criado_em']
    search_fields = [
        'usuario__nome_completo',
        'usuario__email',
        'submissao__titulo',
    ]
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = [
        (
            _('Vinculação'),
            {'fields': ['submissao', 'usuario', 'tipo_participacao', 'ordem_autoria']},
        ),
        (
            _('Perfil Profissional'),
            {
                'fields': [
                    'lattes_url',
                    'linkedin_url',
                    'afiliacao_institucional',
                    'maiór_titulacao',
                ]
            },
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(SubmissaoVersao)
class SubmissaoVersaoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'submissao',
        'numero_versao',
        'caminho_arquivo',
        'criado_em',
    ]
    list_filter = ['numero_versao', 'criado_em']
    search_fields = ['submissao__titulo']
    readonly_fields = ['criado_em']
    fieldsets = [
        (
            _('Versão de Submissão'),
            {'fields': ['submissao', 'numero_versao', 'caminho_arquivo']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em']},
        ),
    ]


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'submissao',
        'avaliador',
        'status_parecer',
        'pontuacao',
        'criado_em',
    ]
    list_filter = ['status_parecer', 'criado_em']
    search_fields = [
        'submissao__titulo',
        'avaliador__nome_completo',
        'avaliador__email',
    ]
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = [
        (
            _('Avaliação'),
            {'fields': ['submissao', 'avaliador', 'status_parecer', 'pontuacao']},
        ),
        (
            _('Observações'),
            {'fields': ['observacoes']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'evento', 'capacidade', 'criado_em']
    list_filter = ['evento', 'criado_em']
    search_fields = ['nome', 'descricao', 'evento__nome']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = [
        (
            _('Informações do Local'),
            {'fields': ['evento', 'nome', 'descricao', 'capacidade']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(Apresentacao)
class ApresentacaoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'submissao',
        'local',
        'inicio',
        'duracao_minutos',
        'criado_em',
    ]
    list_filter = ['local', 'inicio', 'criado_em']
    search_fields = ['submissao__titulo', 'local__nome']
    readonly_fields = ['criado_em', 'atualizado_em', 'fim']
    fieldsets = [
        (
            _('Apresentação'),
            {'fields': ['submissao', 'local', 'inicio', 'duracao_minutos', 'fim']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(Avaliador)
class AvaliadorAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'ativo', 'criado_em']
    list_filter = ['ativo', 'areas', 'criado_em']
    search_fields = ['usuario__nome_completo', 'usuario__email']
    readonly_fields = ['criado_em', 'atualizado_em']
    filter_horizontal = ['areas']
    fieldsets = [
        (
            _('Vinculação'),
            {'fields': ['usuario', 'areas', 'ativo']},
        ),
        (
            _('Perfil Profissional'),
            {
                'fields': [
                    'lattes_url',
                    'linkedin_url',
                    'afiliacao_institucional',
                    'maior_titulacao',
                ]
            },
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]


@admin.register(AvaliadorEvento)
class AvaliadorEventoAdmin(admin.ModelAdmin):
    list_display = ['id', 'evento', 'avaliador', 'criado_em']
    list_filter = ['evento', 'criado_em']
    search_fields = [
        'evento__nome',
        'avaliador__usuario__nome_completo',
        'avaliador__usuario__email',
    ]
    readonly_fields = ['criado_em']
    fieldsets = [
        (
            _('Vínculo'),
            {'fields': ['evento', 'avaliador']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em']},
        ),
    ]


@admin.register(AtribuicaoAvaliacao)
class AtribuicaoAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'submissao', 'avaliador', 'status', 'criado_em']
    list_filter = ['status', 'criado_em']
    search_fields = [
        'submissao__titulo',
        'avaliador__usuario__nome_completo',
        'avaliador__usuario__email',
    ]
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = [
        (
            _('Atribuição'),
            {'fields': ['submissao', 'avaliador', 'status']},
        ),
        (
            _('Datas'),
            {'fields': ['criado_em', 'atualizado_em']},
        ),
    ]
