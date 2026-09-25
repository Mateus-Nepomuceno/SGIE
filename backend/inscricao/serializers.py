from rest_framework import serializers
from .models import Inscricao

class InscricaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscricao
        fields = ['id', 'evento', 'comprovante', 'dados_adicionais', 'status']
        read_only_fields = ['status', 'id']


class MinhaInscricaoSerializer(serializers.ModelSerializer):
    """
    Serializer usado pela página "Minhas inscrições e ingresso".
    Reúne os dados da inscrição do participante autenticado com as
    informações do evento relacionado, já formatadas para exibição,
    e alguns campos derivados (ingresso, posição na fila, permissões
    de ação) que a tela consome diretamente, sem lógica extra no front.
    """

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    evento_nome = serializers.CharField(source='evento.nome', read_only=True)
    evento_data = serializers.DateField(source='evento.data', read_only=True)
    evento_hora_inicio = serializers.TimeField(source='evento.hora_inicio', read_only=True)
    evento_local = serializers.CharField(source='evento.local', read_only=True)
    evento_modalidade = serializers.CharField(source='evento.get_modalidade_display', read_only=True)
    evento_categoria = serializers.CharField(source='evento.get_categoria_display', read_only=True)
    evento_status = serializers.CharField(source='evento.status', read_only=True)
    evento_status_display = serializers.CharField(source='evento.get_status_display', read_only=True)
    evento_e_gratuito = serializers.BooleanField(source='evento.e_gratuito', read_only=True)
    evento_preco = serializers.DecimalField(source='evento.preco', max_digits=10, decimal_places=2, read_only=True)
    evento_necessita_comprovante = serializers.BooleanField(source='evento.necessita_comprovante', read_only=True)

    posicao_lista_espera = serializers.SerializerMethodField()
    codigo_ingresso = serializers.SerializerMethodField()
    pode_cancelar = serializers.SerializerMethodField()

    class Meta:
        model = Inscricao
        fields = [
            'id', 'status', 'status_display', 'comprovante', 'dados_adicionais', 'data_inscricao',
            'evento', 'evento_nome', 'evento_data', 'evento_hora_inicio', 'evento_local',
            'evento_modalidade', 'evento_categoria', 'evento_status', 'evento_status_display',
            'evento_e_gratuito', 'evento_preco', 'evento_necessita_comprovante',
            'posicao_lista_espera', 'codigo_ingresso', 'pode_cancelar',
        ]

    def get_posicao_lista_espera(self, obj):
        if obj.status != 'lista_espera':
            return None
        posicao = Inscricao.objects.filter(
            evento=obj.evento,
            status='lista_espera',
            data_inscricao__lte=obj.data_inscricao,
        ).count()
        return posicao

    def get_codigo_ingresso(self, obj):
        if obj.status != 'confirmada':
            return None
        return f"SGIE-{obj.evento_id:04d}-{obj.id:06d}"

    def get_pode_cancelar(self, obj):
        if obj.status not in ('confirmada', 'pendente_pagamento', 'lista_espera'):
            return False
        evento = obj.evento
        if evento.status in ('Finalizado', 'Arquivado', 'Cancelado'):
            return False
        return True


class ParticipanteSerializer(serializers.ModelSerializer):
    """
    Serializer usado pela página "Consulta de participantes" (visão do
    organizador, em ListaInscritosView). Reúne os dados do participante
    e da inscrição necessários para a listagem e os filtros do
    organizador. Somente leitura.
    """

    participante_nome = serializers.CharField(source='usuario.nome_completo', read_only=True)
    participante_email = serializers.CharField(source='usuario.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Inscricao
        fields = [
            'id', 'status', 'status_display',
            'participante_nome', 'participante_email',
            'comprovante', 'dados_adicionais', 'data_inscricao',
        ]
        read_only_fields = fields
