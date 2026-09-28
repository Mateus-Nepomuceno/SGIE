import json
from typing import Any, Dict

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import (
    Apresentacao,
    Area,
    Avaliacao,
    Local,
    Submissao,
    SubmissaoAutor,
    SubmissaoVersao,
    TipoSubmissao,
    Avaliador
)
from .services import SubmissaoService
from .validators import (
    validar_abstract,
    validar_arquivo_submissao,
    validar_palavras_chave,
    validar_titulo_submissao,
    validar_url,
)


class AreaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Area
        fields = ['id', 'nome', 'descricao', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_em', 'atualizado_em']


class SubmissaoVersaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubmissaoVersao
        fields = ['id', 'submissao', 'numero_versao', 'caminho_arquivo', 'criado_em']
        read_only_fields = ['id', 'criado_em']
        extra_kwargs = {
            'submissao': {'required': False},
        }


class SubmissaoAutorSerializer(serializers.ModelSerializer):

    submissao = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=Submissao.objects.all(),
    )
    usuario_nome = serializers.CharField(source='usuario.nome_completo', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = SubmissaoAutor
        fields = [
            'id',
            'submissao',
            'usuario',
            'usuario_nome',
            'usuario_email',
            'tipo_participacao',
            'ordem_autoria',
            'lattes_url',
            'linkedin_url',
            'afiliacao_institucional',
            'maiór_titulacao',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        validators = []

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'maior_titulacao' in data and 'maiór_titulacao' not in data:
            data['maiór_titulacao'] = data['maior_titulacao']
        return super().to_internal_value(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['maior_titulacao'] = ret.get('maiór_titulacao', '')
        return ret

    def validate_lattes_url(self, value):
        if value:
            validar_url(value)
        return value

    def validate_linkedin_url(self, value):
        if value:
            validar_url(value)
        return value


class AvaliacaoSerializer(serializers.ModelSerializer):

    avaliador_nome = serializers.CharField(source='avaliador.nome_completo', read_only=True)
    avaliador_email = serializers.CharField(source='avaliador.email', read_only=True)
    status_parecer_display = serializers.CharField(source='get_status_parecer_display', read_only=True)

    class Meta:
        model = Avaliacao
        fields = [
            'id',
            'submissao',
            'avaliador',
            'avaliador_nome',
            'avaliador_email',
            'status_parecer',
            'status_parecer_display',
            'observacoes',
            'pontuacao',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'submissao': {'required': False},
        }


class LocalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Local
        fields = [
            'id',
            'evento',
            'nome',
            'descricao',
            'capacidade',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'evento': {'required': False},
        }


class ApresentacaoSerializer(serializers.ModelSerializer):

    local_nome = serializers.CharField(source='local.nome', read_only=True)
    fim = serializers.SerializerMethodField()

    class Meta:
        model = Apresentacao
        fields = [
            'id',
            'submissao',
            'local',
            'local_nome',
            'inicio',
            'fim',
            'duracao_minutos',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'submissao': {'required': False},
        }

    def get_fim(self, obj):
        return obj.fim.isoformat() if obj.fim else None


class SubmissaoListSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    area_nome = serializers.CharField(source='area.nome', read_only=True)
    autor_nome = serializers.CharField(source='autor_principal.nome_completo', read_only=True)
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)

    class Meta:
        model = Submissao
        fields = [
            'id',
            'evento',
            'evento_nome',
            'titulo',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'area',
            'area_nome',
            'autor_principal',
            'autor_nome',
            'criado_em',
            'atualizado_em',
        ]


class SubmissaoDetailSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    area_nome = serializers.CharField(source='area.nome', read_only=True)
    autor_nome = serializers.CharField(source='autor_principal.nome_completo', read_only=True)
    autor_email = serializers.CharField(source='autor_principal.email', read_only=True)
    evento_nome = serializers.CharField(source='evento.nome', read_only=True)

    pode_editar = serializers.BooleanField(read_only=True)
    pode_submeter = serializers.BooleanField(read_only=True)

    autores = SubmissaoAutorSerializer(many=True, read_only=True)
    versoes = SubmissaoVersaoSerializer(many=True, read_only=True)
    avaliacoes = AvaliacaoSerializer(many=True, read_only=True)
    apresentacoes = ApresentacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Submissao
        fields = [
            'id',
            'evento',
            'evento_nome',
            'autor_principal',
            'autor_nome',
            'autor_email',
            'titulo',
            'descricao',
            'abstract',
            'resumo',
            'palavras_chave',
            'tipo',
            'tipo_display',
            'status',
            'status_display',
            'area',
            'area_nome',
            'pode_editar',
            'pode_submeter',
            'autores',
            'versoes',
            'avaliacoes',
            'apresentacoes',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em', 'evento', 'autor_principal']


class SubmissaoCreateUpdateSerializer(serializers.ModelSerializer):

    autores = SubmissaoAutorSerializer(many=True, required=False)
    arquivo = serializers.FileField(
        required=False,
        write_only=True,
        help_text=_('Arquivo PDF ou DOCX da submissão.'),
    )
    lattes_url = serializers.URLField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text=_('Currículo Lattes do autor principal.'),
    )
    linkedin_url = serializers.URLField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text=_('LinkedIn do autor principal.'),
    )
    afiliacao_institucional = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        write_only=True,
        help_text=_('Afiliação institucional do autor principal.'),
    )
    maior_titulacao = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        write_only=True,
        help_text=_('Maior titulação do autor principal.'),
    )
    maiór_titulacao = serializers.CharField(  # noqa: PLC2401
        required=False,
        allow_blank=True,
        max_length=100,
        write_only=True,
    )

    class Meta:
        model = Submissao
        fields = [
            'id',
            'evento',
            'titulo',
            'descricao',
            'abstract',
            'resumo',
            'palavras_chave',
            'tipo',
            'status',
            'area',
            'autores',
            'arquivo',
            'lattes_url',
            'linkedin_url',
            'afiliacao_institucional',
            'maior_titulacao',
            'maiór_titulacao',
        ]
        read_only_fields = ['id', 'status']

    @staticmethod
    def validate_titulo(value):
        validar_titulo_submissao(value)
        return value

    @staticmethod
    def validate_abstract(value):
        validar_abstract(value)
        return value

    @staticmethod
    def validate_palavras_chave(value):
        validar_palavras_chave(value)
        return value

    def validate_arquivo(self, value):
        if value:
            try:
                validar_arquivo_submissao(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
                )
        return value

    def validate_lattes_url(self, value):
        if value:
            try:
                validar_url(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
                )
        return value

    def validate_linkedin_url(self, value):
        if value:
            try:
                validar_url(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
                )
        return value

    def validate(self, attrs):
        tipo = attrs.get('tipo', getattr(self.instance, 'tipo', TipoSubmissao.ARTIGO))
        if tipo == TipoSubmissao.OUTRO:
            raise serializers.ValidationError(
                _('O tipo "Outro" ainda não é suportado nesta versão do sistema.')
            )
        return attrs

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
        else:
            data = dict(data)

        if 'autores' in data and isinstance(data['autores'], str):
            try:
                data['autores'] = json.loads(data['autores'])
            except (json.JSONDecodeError, TypeError):
                pass

        return super().to_internal_value(data)

    def create(self, validated_data: Dict[str, Any]) -> Submissao:
        request = self.context.get('request')
        usuario = request.user if request else validated_data.pop('usuario', None)

        arquivo = validated_data.pop('arquivo', None)
        autores = validated_data.pop('autores', None)

        dados_perfil = {
            'lattes_url': validated_data.pop('lattes_url', ''),
            'linkedin_url': validated_data.pop('linkedin_url', ''),
            'afiliacao_institucional': validated_data.pop('afiliacao_institucional', ''),
            'maior_titulacao': (
                validated_data.pop('maior_titulacao', '')
                or validated_data.pop('maiór_titulacao', '')
            ),
        }

        evento = validated_data.get('evento')
        evento_id = evento.id if hasattr(evento, 'id') else evento
        area = validated_data.get('area')
        area_id = area.id if hasattr(area, 'id') else area

        try:
            submissao = SubmissaoService.criar_submissao(
                usuario=usuario,
                evento_id=evento_id,
                area_id=area_id,
                dados_submissao=validated_data,
                arquivo=arquivo,
                autores_dados=autores,
                dados_autor_principal=dados_perfil,
            )
            return submissao
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )
        except Exception as exc:
            raise serializers.ValidationError(str(exc))

    def update(self, instance: Submissao, validated_data: Dict[str, Any]) -> Submissao:
        validated_data.pop('autores', None)
        validated_data.pop('evento', None)
        validated_data.pop('arquivo', None)
        validated_data.pop('lattes_url', None)
        validated_data.pop('linkedin_url', None)
        validated_data.pop('afiliacao_institucional', None)
        validated_data.pop('maior_titulacao', None)
        validated_data.pop('maiór_titulacao', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )

        instance.save()
        return instance


class SubmeterSubmissaoSerializer(serializers.Serializer):

    arquivo = serializers.FileField(required=True, help_text=_('Arquivo PDF ou DOCX da submissão.'))

    def validate_arquivo(self, value):
        try:
            validar_arquivo_submissao(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )
        return value


class AprovarSubmissaoSerializer(serializers.Serializer):

    observacoes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text=_('Observações da aprovação.'),
    )


class RejeitarSubmissaoSerializer(serializers.Serializer):

    observacoes = serializers.CharField(
        required=True,
        max_length=500,
        help_text=_('Motivo da rejeição.'),
    )


class SolicitarCorrecaoSerializer(serializers.Serializer):

    observacoes = serializers.CharField(
        required=True,
        max_length=1000,
        help_text=_('Observações e correções solicitadas.'),
    )

    prazo_dias = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        default=7,
        help_text=_('Prazo em dias para o autor enviar a nova versão.'),
    )



class AvaliadorSerializer(serializers.ModelSerializer):

    usuario_nome = serializers.CharField(source='usuario.nome_completo', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    areas_nomes = serializers.SerializerMethodField()

    class Meta:
        model = Avaliador
        fields = [
            'id',
            'usuario',
            'usuario_nome',
            'usuario_email',
            'areas',
            'areas_nomes',
            'lattes_url',
            'linkedin_url',
            'afiliacao_institucional',
            'maior_titulacao',
            'ativo',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def get_areas_nomes(self, obj):
        return list(obj.areas.values_list('nome', flat=True))

    def validate_lattes_url(self, value):
        if value:
            validar_url(value)
        return value

    def validate_linkedin_url(self, value):
        if value:
            validar_url(value)
        return value

    def validate_areas(self, value):
        if not value:
            raise serializers.ValidationError(_('Informe ao menos uma área de atuação.'))
        return value