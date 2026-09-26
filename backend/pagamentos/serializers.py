from decimal import Decimal
from typing import override

from rest_framework import serializers

from inscricao.models import Inscricao
from pagamentos.models import (
    CategoriaPreco,
    Certificado,
    Cobranca,
    IsencaoPagamento,
    Lote,
    MetodoPagamento,
    Pagamento,
    Reembolso,
    StatusPagamento,
    TipoIsencao,
)


class CategoriaPrecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaPreco
        fields = [
            'id',
            'evento',
            'nome',
            'descricao',
            'ativo',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class LoteSerializer(serializers.ModelSerializer):
    esta_vigente = serializers.BooleanField(read_only=True)
    tem_vagas = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id',
            'categoria_preco',
            'nome',
            'numero',
            'preco',
            'quantidade_total',
            'quantidade_disponivel',
            'data_inicio',
            'data_fim',
            'ativo',
            'esta_vigente',
            'tem_vagas',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'quantidade_disponivel', 'criado_em', 'atualizado_em']

    @override
    def validate(self, attrs):
        data_inicio = attrs.get('data_inicio') or getattr(self.instance, 'data_inicio', None)
        data_fim = attrs.get('data_fim') or getattr(self.instance, 'data_fim', None)

        if data_inicio and data_fim and data_inicio >= data_fim:
            raise serializers.ValidationError({'data_fim': 'A data de término deve ser posterior à data de início.'})

        quantidade_total = attrs.get('quantidade_total') or getattr(self.instance, 'quantidade_total', None)
        quantidade_disponivel = attrs.get('quantidade_disponivel') or getattr(self.instance, 'quantidade_disponivel', None)

        if quantidade_disponivel is not None and quantidade_total is not None and quantidade_disponivel > quantidade_total:
            raise serializers.ValidationError({'quantidade_disponivel': 'A quantidade disponível não pode ser maior do que a total.'})

        return attrs


class IsencaoPagamentoSerializer(serializers.ModelSerializer):
    aprovado_por_nome = serializers.ReadOnlyField(source='aprovado_por.nome_completo')

    class Meta:
        model = IsencaoPagamento
        fields = [
            'id',
            'cobranca',
            'tipo',
            'desconto_percentual',
            'desconto_valor',
            'motivo',
            'aprovado_por',
            'aprovado_por_nome',
            'criado_em',
        ]
        read_only_fields = ['id', 'aprovado_por', 'criado_em']


class CobrancaSerializer(serializers.ModelSerializer):
    isencao = IsencaoPagamentoSerializer(read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)
    evento_nome = serializers.ReadOnlyField(source='inscricao.evento.nome')
    participante_nome = serializers.ReadOnlyField(source='inscricao.usuario.nome_completo')
    lote_nome = serializers.ReadOnlyField(source='lote.nome')

    class Meta:
        model = Cobranca
        fields = [
            'id',
            'inscricao',
            'evento_nome',
            'participante_nome',
            'lote',
            'lote_nome',
            'valor_original',
            'valor_final',
            'status',
            'data_vencimento',
            'esta_vencida',
            'isencao',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = [
            'id',
            'valor_original',
            'valor_final',
            'status',
            'data_vencimento',
            'criado_em',
            'atualizado_em',
        ]


class CriarCobrancaInputSerializer(serializers.Serializer):
    inscricao_id = serializers.PrimaryKeyRelatedField(
        queryset=Inscricao.objects.all(),
        source='inscricao',
    )
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaPreco.objects.all(),
        source='categoria',
        required=False,
        allow_null=True,
    )
    lote_id = serializers.PrimaryKeyRelatedField(
        queryset=Lote.objects.all(),
        source='lote',
        required=False,
        allow_null=True,
    )
    dias_vencimento = serializers.IntegerField(default=3, min_value=1)


class ConcederIsencaoInputSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoIsencao.choices)
    motivo = serializers.CharField(max_length=500)
    desconto_percentual = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
    )
    desconto_valor = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
    )

    @override
    def validate(self, attrs):
        tipo = attrs.get('tipo')
        percentual = attrs.get('desconto_percentual', Decimal('0.00'))
        valor = attrs.get('desconto_valor', Decimal('0.00'))

        if tipo == TipoIsencao.PARCIAL and percentual <= Decimal('0.00') and valor <= Decimal('0.00'):
            raise serializers.ValidationError('Para isenção parcial, informe um percentual ou valor de desconto maior que zero.')
        return attrs


class ProcessarPagamentoInputSerializer(serializers.Serializer):
    metodo = serializers.ChoiceField(choices=MetodoPagamento.choices)
    dados_cartao = serializers.DictField(required=False, default=dict)
    retorno_url = serializers.URLField(required=False, allow_blank=True, default='')


class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = [
            'id',
            'cobranca',
            'valor',
            'metodo',
            'status',
            'transacao_id',
            'gateway_nome',
            'qr_code_pix',
            'url_pagamento',
            'data_criacao',
            'data_pagamento',
            'atualizado_em',
        ]
        read_only_fields = [
            'id',
            'cobranca',
            'valor',
            'status',
            'transacao_id',
            'gateway_nome',
            'qr_code_pix',
            'url_pagamento',
            'data_criacao',
            'data_pagamento',
            'atualizado_em',
        ]


class SolicitarReembolsoInputSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=500)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class ReembolsoSerializer(serializers.ModelSerializer):
    solicitado_por_nome = serializers.ReadOnlyField(source='solicitado_por.nome_completo')
    analisado_por_nome = serializers.ReadOnlyField(source='analisado_por.nome_completo')

    class Meta:
        model = Reembolso
        fields = [
            'id',
            'pagamento',
            'valor',
            'motivo',
            'status',
            'solicitado_por',
            'solicitado_por_nome',
            'analisado_por',
            'analisado_por_nome',
            'transacao_reembolso_id',
            'data_solicitacao',
            'data_conclusao',
            'atualizado_em',
        ]
        read_only_fields = [
            'id',
            'status',
            'solicitado_por',
            'analisado_por',
            'transacao_reembolso_id',
            'data_solicitacao',
            'data_conclusao',
            'atualizado_em',
        ]


class WebhookPagamentoSerializer(serializers.Serializer):
    transacao_id = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(choices=StatusPagamento.choices)
    detalhes = serializers.DictField(required=False, default=dict)


class CertificadoSerializer(serializers.ModelSerializer):
    evento_nome = serializers.ReadOnlyField(source='inscricao.evento.nome')
    participante_nome = serializers.ReadOnlyField(source='inscricao.usuario.nome_completo')

    class Meta:
        model = Certificado
        fields = [
            'id',
            'codigo_autenticacao',
            'inscricao',
            'evento_nome',
            'participante_nome',
            'arquivo',
            'disponivel',
            'carga_horaria',
            'emitido_em',
        ]
        read_only_fields = ['id', 'codigo_autenticacao', 'emitido_em']
