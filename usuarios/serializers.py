from typing import override

from rest_framework import serializers

from .models import PapelContextual, PerfilOrganizador, Usuario
from .validators import limpar_cpf, validar_cpf


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo para a entidade Usuario."""

    cpf_formatado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome_completo',
            'email',
            'cpf',
            'cpf_formatado',
            'data_nascimento',
            'telefone',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id', 'is_staff', 'is_superuser', 'date_joined', 'last_login']

    @staticmethod
    def get_cpf_formatado(obj: Usuario) -> str:
        return obj.cpf_formatado


class UsuarioCadastroSerializer(serializers.ModelSerializer):
    """Serializer para cadastro de usuários via API REST (RF01)."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome_completo',
            'email',
            'cpf',
            'data_nascimento',
            'telefone',
            'password',
        ]
        read_only_fields = ['id']

    @staticmethod
    def validate_cpf(value):
        validar_cpf(value)
        cpf_limpo = limpar_cpf(value)
        if Usuario.objects.filter(cpf=cpf_limpo).exists():
            raise serializers.ValidationError('Já existe um usuário cadastrado com este CPF.')
        return cpf_limpo

    @staticmethod
    def validate_email(value):
        email_limpo = value.lower().strip()
        if Usuario.objects.filter(email__iexact=email_limpo).exists():
            raise serializers.ValidationError('Já existe um usuário cadastrado com este e-mail.')
        return email_limpo

    @override
    def create(self, validated_data):
        password = validated_data.pop('password')
        return Usuario.objects.create_user(password=password, **validated_data)


class PerfilOrganizadorSerializer(serializers.ModelSerializer):
    """Serializer para o perfil estendido de organizador (RF04)."""

    usuario_nome = serializers.CharField(source='usuario.nome_completo', read_only=True)

    class Meta:
        model = PerfilOrganizador
        fields = [
            'id',
            'usuario',
            'usuario_nome',
            'foto_de_perfil',
            'banner',
            'bio_do_organizador',
            'homologado',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'usuario', 'atualizado_em']


class PapelContextualSerializer(serializers.ModelSerializer):
    """Serializer para papéis contextuais associados a eventos (RN03)."""

    usuario_nome = serializers.CharField(source='usuario.nome_completo', read_only=True)
    papel_descricao = serializers.CharField(source='get_papel_display', read_only=True)

    class Meta:
        model = PapelContextual
        fields = [
            'id',
            'usuario',
            'usuario_nome',
            'evento_id',
            'papel',
            'papel_descricao',
            'ativo',
            'atribuido_em',
        ]
        read_only_fields = ['id', 'atribuido_em']


class DadosCadastraisSerializer(serializers.Serializer):
    """Serializer do contrato público de dados de usuário (RN06)."""

    id = serializers.IntegerField()
    nome_completo = serializers.CharField()
    email = serializers.EmailField()
    cpf = serializers.CharField()
    cpf_limpo = serializers.CharField()
    data_nascimento = serializers.DateField()
    telefone = serializers.CharField()
    is_organizador = serializers.BooleanField()
