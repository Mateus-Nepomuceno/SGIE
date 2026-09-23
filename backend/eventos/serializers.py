from typing import Any, Dict

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    CategoriaEvento,
    EquipeOrganizadora,
    Evento,
    LocalTipo,
    RegraSubmissao,
)
from .services import EventoService
from .validators import (
    validar_capacidade,
    validar_titulo_evento,
)


class EquipeOrganizadoraSerializer(serializers.ModelSerializer):

    class Meta:
        model = EquipeOrganizadora
        fields = ['id', 'evento', 'nome', 'email_publico', 'papel_funcao']
        extra_kwargs = {
            'evento': {'required': False},
        }


class RegraSubmissaoSerializer(serializers.ModelSerializer):

    periodo_aberto = serializers.BooleanField(read_only=True)

    class Meta:
        model = RegraSubmissao
        fields = [
            'id','evento','aceita_submissao','data_hora_inicio','data_hora_fim','periodo_aberto',
        ]
        extra_kwargs = {
            'evento': {'required': False},
        }

    def validate(self, attrs):
        aceita = attrs.get('aceita_submissao', getattr(self.instance, 'aceita_submissao', False))
        inicio = attrs.get('data_hora_inicio', getattr(self.instance, 'data_hora_inicio', None))
        fim = attrs.get('data_hora_fim', getattr(self.instance, 'data_hora_fim', None))

        if aceita:
            if not inicio or not fim:
                raise serializers.ValidationError(
                    _('Eventos com submissão de trabalhos exigem definição de data/hora de início e fim.')
                )
            if fim <= inicio:
                raise serializers.ValidationError(
                    {'data_hora_fim': _('A data/hora de término da submissão deve ser posterior ao início.')}
                )
        return attrs


class EventoListSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modalidade_display = serializers.CharField(source='get_modalidade_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    inscricoes_abertas = serializers.BooleanField(source='inscricoes_abertas_status', read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id','nome','descricao','data','hora_inicio','hora_fim','local_tipo','local',
            'modalidade','modalidade_display','capacidade','status','status_display','categoria',
            'categoria_display','categoria_personalizada','e_gratuito','preco','visibilidade',
            'inscricoes_abertas','criado_em',
        ]


class EventoDetailSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modalidade_display = serializers.CharField(source='get_modalidade_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    inscricoes_abertas = serializers.BooleanField(source='inscricoes_abertas_status', read_only=True)
    is_curta_duracao = serializers.BooleanField(read_only=True)

    pode_alterar_data = serializers.BooleanField(read_only=True)
    pode_alterar_detalhes = serializers.BooleanField(read_only=True)
    pode_cancelar = serializers.BooleanField(read_only=True)

    limite_alteracao_data = serializers.DateTimeField(read_only=True)
    limite_alteracao_detalhes = serializers.DateTimeField(read_only=True)
    limite_cancelamento = serializers.DateTimeField(read_only=True)
    limite_encerramento_inscricoes = serializers.DateTimeField(read_only=True)

    usuario_representante_nome = serializers.CharField(source='usuario_representante.nome_completo', read_only=True)
    usuario_representante_email = serializers.CharField(source='usuario_representante.email', read_only=True)

    organizadores = EquipeOrganizadoraSerializer(many=True, read_only=True)
    regra_submissao = RegraSubmissaoSerializer(read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id','usuario_representante','usuario_representante_nome','usuario_representante_email',
            'nome','descricao','data','data_original','hora_inicio','hora_inicio_original','hora_fim',
            'local_tipo','local','modalidade','modalidade_display','capacidade','status','status_display',
            'categoria','categoria_display','categoria_personalizada','e_gratuito','preco','visibilidade',
            'programacao_geral','motivo_cancelamento','cancelado_em','inscricoes_abertas','is_curta_duracao',
            'pode_alterar_data','pode_alterar_detalhes','pode_cancelar','limite_alteracao_data',
            'limite_alteracao_detalhes','limite_cancelamento','limite_encerramento_inscricoes',
            'organizadores','regra_submissao','criado_em','atualizado_em',
        ]


class EventoCreateUpdateSerializer(serializers.ModelSerializer):

    data = serializers.DateField(input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y'])
    hora_inicio = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    hora_fim = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    capacidade = serializers.IntegerField(validators=[validar_capacidade])

    organizadores = EquipeOrganizadoraSerializer(many=True, required=False)
    regra_submissao = RegraSubmissaoSerializer(required=False, allow_null=True)

    class Meta:
        model = Evento
        fields = [
            'id','nome','descricao','data','hora_inicio','hora_fim','local_tipo','local',
            'modalidade', 'capacidade','status','categoria','categoria_personalizada','e_gratuito',
            'preco','visibilidade','programacao_geral','organizadores','regra_submissao',
        ]
        read_only_fields = ['id']

    @staticmethod
    def validate_nome(value):
        validar_titulo_evento(value)
        return value

    def validate(self, attrs):
        hora_inicio = attrs.get('hora_inicio', getattr(self.instance, 'hora_inicio', None))
        hora_fim = attrs.get('hora_fim', getattr(self.instance, 'hora_fim', None))

        if hora_inicio and hora_fim and hora_fim <= hora_inicio:
            raise serializers.ValidationError(
                {'hora_fim': _('O horário de fim deve ser estritamente posterior ao horário de início.')}
            )

        e_gratuito = attrs.get('e_gratuito', getattr(self.instance, 'e_gratuito', True))
        preco = attrs.get('preco', getattr(self.instance, 'preco', 0.00))

        if not e_gratuito and preco <= 0:
            raise serializers.ValidationError(
                {'preco': _('Eventos pagos devem possuir valor de inscrição superior a R$ 0,00.')}
            )

        categoria = attrs.get('categoria', getattr(self.instance, 'categoria', CategoriaEvento.CONGRESSO))
        categoria_pers = attrs.get('categoria_personalizada', getattr(self.instance, 'categoria_personalizada', ''))
        if categoria == CategoriaEvento.OUTRO and not categoria_pers.strip():
            raise serializers.ValidationError(
                {'categoria_personalizada': _('Informe a categoria personalizada quando a opção "Outro" for selecionada.')}
            )

        local_tipo = attrs.get('local_tipo', getattr(self.instance, 'local_tipo', LocalTipo.AUDITORIO))
        local_desc = attrs.get('local', getattr(self.instance, 'local', ''))
        if local_tipo == LocalTipo.OUTRO and not local_desc.strip():
            raise serializers.ValidationError(
                {'local': _('Informe a descrição do local quando a opção "Outro" for selecionada.')}
            )

        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Evento:
        request = self.context.get('request')
        usuario = request.user if request else validated_data.pop('usuario_representante', None)

        organizadores = validated_data.pop('organizadores', None)
        regra_submissao = validated_data.pop('regra_submissao', None)

        try:
            return EventoService.criar_evento(
                usuario=usuario,
                dados_evento=validated_data,
                organizadores=organizadores,
                regra_submissao=regra_submissao,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    def update(self, instance: Evento, validated_data: Dict[str, Any]) -> Evento:
        request = self.context.get('request')
        usuario = request.user

        validated_data.pop('organizadores', None)
        validated_data.pop('regra_submissao', None)

        try:
            return EventoService.alterar_evento(instance, validated_data, usuario)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)


class CancelarEventoSerializer(serializers.Serializer):

    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text=_('Motivo formal do cancelamento do evento.'),
    )
