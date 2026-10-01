from django.contrib import admin

from .models import (
    CategoriaPreco,
    Certificado,
    Cobranca,
    Comunicacao,
    IsencaoPagamento,
    Lote,
    Pagamento,
    Reembolso,
)


class LoteInline(admin.TabularInline):
    model = Lote
    extra = 1


class IsencaoPagamentoInline(admin.StackedInline):
    model = IsencaoPagamento
    extra = 0


class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0
    readonly_fields = ('data_criacao', 'data_pagamento')


@admin.register(CategoriaPreco)
class CategoriaPrecoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'evento', 'ativo', 'criado_em')
    list_filter = ('ativo', 'evento')
    search_fields = ('nome', 'evento__nome')
    inlines = [LoteInline]


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria_preco', 'preco', 'quantidade_total', 'quantidade_disponivel', 'data_inicio', 'data_fim', 'ativo')
    list_filter = ('ativo', 'categoria_preco__evento')
    search_fields = ('nome', 'categoria_preco__nome', 'categoria_preco__evento__nome')


@admin.register(Cobranca)
class CobrancaAdmin(admin.ModelAdmin):
    list_display = ('id', 'inscricao', 'lote', 'valor_original', 'valor_final', 'status', 'data_vencimento', 'criado_em')
    list_filter = ('status', 'criado_em')
    search_fields = ('id', 'inscricao__usuario__email', 'inscricao__usuario__nome_completo')
    inlines = [IsencaoPagamentoInline, PagamentoInline]


@admin.register(IsencaoPagamento)
class IsencaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cobranca', 'tipo', 'desconto_percentual', 'desconto_valor', 'aprovado_por', 'criado_em')
    list_filter = ('tipo', 'criado_em')
    search_fields = ('cobranca__id', 'cobranca__inscricao__usuario__email')


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cobranca', 'valor', 'metodo', 'status', 'transacao_id', 'gateway_nome', 'data_criacao', 'data_pagamento')
    list_filter = ('status', 'metodo', 'gateway_nome', 'data_criacao')
    search_fields = ('id', 'transacao_id', 'cobranca__id', 'cobranca__inscricao__usuario__email')


@admin.register(Reembolso)
class ReembolsoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pagamento', 'valor', 'status', 'solicitado_por', 'analisado_por', 'data_solicitacao', 'data_conclusao')
    list_filter = ('status', 'data_solicitacao')
    search_fields = ('id', 'pagamento__id', 'solicitado_por__email')


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('codigo_autenticacao', 'inscricao', 'disponivel', 'carga_horaria', 'emitido_em')
    list_filter = ('disponivel', 'emitido_em')
    search_fields = ('codigo_autenticacao', 'inscricao__usuario__email', 'inscricao__evento__nome')


@admin.register(Comunicacao)
class ComunicacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'destinatario', 'canal', 'assunto', 'enviado', 'data_envio', 'criado_em')
    list_filter = ('canal', 'enviado', 'criado_em')
    search_fields = ('destinatario__email', 'assunto')
