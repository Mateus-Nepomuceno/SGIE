from typing import override

from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings

from .models import PapelContextual, PerfilOrganizador, Usuario
from .services import UsuarioService
from .validators import (
    limpar_cpf,
    validar_cpf,
    validar_data_nascimento,
    validar_extensao_imagem,
    validar_telefone,
)

TAMANHO_MIN_NOME = 3
MIN_PALAVRAS_NOME = 2
MAX_FOTO_SIZE = 5 * 1024 * 1024
MAX_BANNER_SIZE = 10 * 1024 * 1024


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer completo para a entidade Usuario com campos traduzidos para o português."""

    cpf_formatado = serializers.CharField(read_only=True)
    organizador = serializers.BooleanField(source='is_organizador', read_only=True)
    ativo = serializers.BooleanField(source='is_active')
    acesso_admin = serializers.BooleanField(source='is_staff', read_only=True)
    superusuario = serializers.BooleanField(source='is_superuser', read_only=True)
    data_cadastro = serializers.DateTimeField(source='date_joined', read_only=True)
    ultimo_acesso = serializers.DateTimeField(source='last_login', read_only=True)

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
            'organizador',
            'ativo',
            'acesso_admin',
            'superusuario',
            'data_cadastro',
            'ultimo_acesso',
        ]
        read_only_fields = [
            'id',
            'cpf_formatado',
            'organizador',
            'acesso_admin',
            'superusuario',
            'data_cadastro',
            'ultimo_acesso',
        ]


class UsuarioCadastroSerializer(serializers.ModelSerializer):
    """Serializer para cadastro de usuários via API REST (RF01, RN01)."""

    senha = serializers.CharField(source='password', write_only=True, min_length=8)
    confirmacao_senha = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome_completo',
            'email',
            'cpf',
            'data_nascimento',
            'telefone',
            'senha',
            'confirmacao_senha',
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        # Suporta tanto 'senha' quanto o identificador original 'password'
        if isinstance(data, dict):
            data = data.copy()
            if 'password' in data and 'senha' not in data:
                data['senha'] = data['password']
            if 'password_confirm' in data and 'confirmacao_senha' not in data:
                data['confirmacao_senha'] = data['password_confirm']
        return super().to_internal_value(data)

    @staticmethod
    def validate_nome_completo(value):
        nome = value.strip()
        if len(nome) < TAMANHO_MIN_NOME:
            raise serializers.ValidationError(_('O nome completo deve conter no mínimo 3 caracteres.'))
        if len(nome.split()) < MIN_PALAVRAS_NOME:
            raise serializers.ValidationError(_('Informe seu nome e sobrenome.'))
        return nome

    @staticmethod
    def validate_data_nascimento(value):
        try:
            validar_data_nascimento(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    @staticmethod
    def validate_cpf(value):
        try:
            validar_cpf(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        cpf_limpo = limpar_cpf(value)
        if Usuario.objects.filter(cpf=cpf_limpo).exists():
            raise serializers.ValidationError(_('Já existe um usuário cadastrado com este CPF.'))
        return cpf_limpo

    @staticmethod
    def validate_email(value):
        email_limpo = value.lower().strip()
        if Usuario.objects.filter(email__iexact=email_limpo).exists():
            raise serializers.ValidationError(_('Já existe um usuário cadastrado com este e-mail.'))
        return email_limpo

    @staticmethod
    def validate_telefone(value):
        tel = value.strip()
        try:
            validar_telefone(tel)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return tel

    @override
    def validate(self, attrs):
        password = attrs.get('password')
        confirmacao = attrs.get('confirmacao_senha')
        if confirmacao and password != confirmacao:
            raise serializers.ValidationError({'confirmacao_senha': _('As senhas não coincidem.')})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    @override
    def create(self, validated_data):
        validated_data.pop('confirmacao_senha', None)
        password = validated_data.pop('password')
        return Usuario.objects.create_user(password=password, **validated_data)


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de dados pessoais pelo próprio usuário."""

    class Meta:
        model = Usuario
        fields = ['nome_completo', 'telefone', 'data_nascimento']

    @staticmethod
    def validate_nome_completo(value):
        nome = value.strip()
        if len(nome) < TAMANHO_MIN_NOME:
            raise serializers.ValidationError(_('O nome completo deve conter no mínimo 3 caracteres.'))
        if len(nome.split()) < MIN_PALAVRAS_NOME:
            raise serializers.ValidationError(_('Informe seu nome e sobrenome.'))
        return nome

    @staticmethod
    def validate_data_nascimento(value):
        try:
            validar_data_nascimento(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    @staticmethod
    def validate_telefone(value):
        tel = value.strip()
        try:
            validar_telefone(tel)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return tel


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer de autenticação JWT híbrido (E-mail ou CPF).
    Retorna tokens de acesso e refresh, além dos metadados do usuário autenticado.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identificador'] = serializers.CharField(
            required=False,
            help_text=_('E-mail ou CPF do usuário'),
        )
        self.fields['senha'] = serializers.CharField(
            source='password',
            required=False,
            write_only=True,
            help_text=_('Senha do usuário'),
        )
        if 'email' in self.fields:
            self.fields['email'].required = False
        if 'username' in self.fields:
            self.fields['username'].required = False

    @override
    def validate(self, attrs):
        identificador = (
            attrs.get('identificador')
            or attrs.get('email')
            or attrs.get('username')
            or attrs.get('cpf')
            or (self.initial_data.get('identificador') if hasattr(self, 'initial_data') else None)
        )
        password = (
            attrs.get('password')
            or attrs.get('senha')
            or (self.initial_data.get('senha') if hasattr(self, 'initial_data') else None)
            or (self.initial_data.get('password') if hasattr(self, 'initial_data') else None)
        )

        if not identificador or not password:
            raise serializers.ValidationError(_('Identificador (E-mail ou CPF) e senha são obrigatórios.'))

        request = self.context.get('request')
        usuario = UsuarioService.autenticar_usuario(request, identificador=identificador, senha=password)

        if not usuario:
            raise serializers.ValidationError(_('Identificador (E-mail ou CPF) ou senha inválidos.'))

        if not usuario.is_active:
            raise serializers.ValidationError(_('Conta de usuário inativa.'))

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, usuario)

        refresh = self.get_token(usuario)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'usuario': {
                'id': usuario.id,
                'nome_completo': usuario.nome_completo,
                'email': usuario.email,
                'cpf': usuario.cpf_formatado,
                'is_organizador': usuario.is_organizador(),
            },
        }


class SolicitarRecuperacaoSenhaSerializer(serializers.Serializer):
    """Serializer para solicitação de código de recuperação de senha por e-mail (RF03)."""

    email = serializers.EmailField(required=True)

    def save(self):
        email = self.validated_data['email']
        UsuarioService.gerar_codigo_recuperacao(email)
        return email


class RedefinirSenhaSerializer(serializers.Serializer):
    """Serializer para redefinição de senha com código de 6 dígitos (RF03)."""

    email = serializers.EmailField(required=True)
    codigo = serializers.CharField(required=True, min_length=6, max_length=6)
    nova_senha = serializers.CharField(required=True, min_length=8, write_only=True)
    confirmacao_senha = serializers.CharField(required=True, min_length=8, write_only=True)

    @override
    def validate(self, attrs):
        if attrs['nova_senha'] != attrs['confirmacao_senha']:
            raise serializers.ValidationError({'confirmacao_senha': _('As senhas não coincidem.')})
        try:
            validate_password(attrs['nova_senha'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'nova_senha': list(exc.messages)}) from exc
        return attrs

    def save(self):
        email = self.validated_data['email']
        codigo = self.validated_data['codigo']
        nova_senha = self.validated_data['nova_senha']
        try:
            UsuarioService.redefinir_senha_com_codigo(email, codigo, nova_senha)
        except DjangoValidationError as exc:
            msg = exc.message if hasattr(exc, 'message') else str(exc)
            raise serializers.ValidationError({'codigo': msg}) from exc
        return True


class PerfilOrganizadorSerializer(serializers.ModelSerializer):
    """Serializer para o perfil estendido de organizador (RF04, RN04)."""

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
        read_only_fields = ['id', 'usuario', 'usuario_nome', 'homologado', 'atualizado_em']

    @staticmethod
    def validate_foto_de_perfil(value):
        if value:
            try:
                validar_extensao_imagem(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(list(exc.messages)) from exc
            if hasattr(value, 'size') and value.size > MAX_FOTO_SIZE:
                raise serializers.ValidationError(_('A foto de perfil não pode exceder 5 MB.'))
        return value

    @staticmethod
    def validate_banner(value):
        if value:
            try:
                validar_extensao_imagem(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(list(exc.messages)) from exc
            if hasattr(value, 'size') and value.size > MAX_BANNER_SIZE:
                raise serializers.ValidationError(_('O banner não pode exceder 10 MB.'))
        return value


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

    id = serializers.CharField()
    nome_completo = serializers.CharField()
    email = serializers.EmailField()
    cpf = serializers.CharField()
    cpf_limpo = serializers.CharField()
    data_nascimento = serializers.DateField()
    telefone = serializers.CharField()
    organizador = serializers.BooleanField(source='is_organizador')
