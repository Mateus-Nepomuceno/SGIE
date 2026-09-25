from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Papel, PapelContextual, PerfilOrganizador, Usuario
from .permissions import IsPapelContextualManagerOrReadOnly, IsSelfOrAdmin
from .serializers import (
    CustomTokenObtainPairSerializer,
    DadosCadastraisSerializer,
    PapelContextualSerializer,
    PerfilOrganizadorSerializer,
    RedefinirSenhaSerializer,
    SolicitarRecuperacaoSenhaSerializer,
    UsuarioCadastroSerializer,
    UsuarioSerializer,
    UsuarioUpdateSerializer,
)
from .services import UsuarioService


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint de emissão de tokens JWT com suporte a login híbrido (E-mail ou CPF) (RF02).
    Retorna access token, refresh token e os dados essenciais do usuário.
    """

    serializer_class = CustomTokenObtainPairSerializer


class SolicitarRecuperacaoSenhaAPIView(APIView):
    """
    Endpoint para solicitação de código de 6 dígitos para recuperação de senha (RF03).
    Acesso público (AllowAny).
    """

    permission_classes = [AllowAny]

    @staticmethod
    def post(request):
        serializer = SolicitarRecuperacaoSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': _('Se o e-mail informado constar em nossa base de dados, um código de verificação de 6 dígitos foi enviado.')},
            status=status.HTTP_200_OK,
        )


class RedefinirSenhaAPIView(APIView):
    """
    Endpoint para validação do código de 6 dígitos e definição da nova senha (RF03).
    Acesso público (AllowAny).
    """

    permission_classes = [AllowAny]

    @staticmethod
    def post(request):
        serializer = RedefinirSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': _('Senha atualizada com sucesso! Efetue login com sua nova senha.')},
            status=status.HTTP_200_OK,
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    API REST para consulta, cadastro e gerenciamento de usuários (RF01, RN01).
    Permite cadastro anônimo (create) e operações restritas ao próprio usuário ou admin.
    """

    queryset = Usuario.objects.all().order_by('id')
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsSelfOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCadastroSerializer
        if self.action in {'update', 'partial_update'}:
            return UsuarioUpdateSerializer
        return UsuarioSerializer

    @action(detail=False, methods=['get', 'put', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Consulta e atualização do perfil do usuário atualmente autenticado via JWT."""
        usuario = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)

        partial = request.method == 'PATCH'
        serializer = UsuarioUpdateSerializer(usuario, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(usuario).data, status=status.HTTP_200_OK)


class PerfilOrganizadorViewSet(viewsets.ModelViewSet):
    """
    API REST para perfis estendidos de organizadores (RF04, RN04).
    Suporta envio multipart/form-data para upload de foto de perfil e banner visual.
    """

    queryset = PerfilOrganizador.objects.select_related('usuario').all().order_by('id')
    serializer_class = PerfilOrganizadorSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        if PerfilOrganizador.objects.filter(usuario=self.request.user).exists():
            raise serializers.ValidationError({'detail': _('Usuário já possui um perfil de organizador cadastrado.')})
        serializer.save(usuario=self.request.user)

    @action(
        detail=False,
        methods=['get', 'post', 'put', 'patch'],
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def me(self, request):
        """Consulta, criação ou atualização do perfil de organizador do usuário autenticado."""
        perfil = getattr(request.user, 'perfil_organizador', None)

        if request.method == 'GET':
            if not perfil:
                return Response(
                    {'detail': _('Perfil de organizador ainda não preenchido.')},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = self.get_serializer(perfil)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if perfil:
            serializer = self.get_serializer(perfil, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PapelContextualViewSet(viewsets.ModelViewSet):
    """API REST para verificação e concessão de papéis contextuais por evento (RN03, RN05)."""

    queryset = PapelContextual.objects.select_related('usuario').all().order_by('id')
    serializer_class = PapelContextualSerializer
    permission_classes = [IsAuthenticated, IsPapelContextualManagerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        evento_id = self.request.query_params.get('evento_id')
        if evento_id:
            try:
                ev_id = int(evento_id)
                qs = qs.filter(evento_id=ev_id)
            except (ValueError, TypeError):
                return qs.none()
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            try:
                qs = qs.filter(usuario_id=usuario_id)
            except (ValueError, TypeError):
                return qs.none()
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        solicitado_usuario = serializer.validated_data.get('usuario')
        solicitado_papel = serializer.validated_data.get('papel')

        if not (user.is_staff or user.is_superuser or user.is_organizador()):
            if solicitado_usuario != user:
                raise serializers.ValidationError({'usuario': _('Você só pode solicitar papéis para sua própria conta.')})
            if solicitado_papel not in {Papel.PARTICIPANTE, Papel.VOLUNTARIO, Papel.SUPORTE}:
                raise serializers.ValidationError({'papel': _('Papéis de Organizador, Avaliador e Autor exigem homologação.')})

        serializer.save()


class DadosCadastraisAPIView(APIView):
    """
    Endpoint de integração para consulta de dados cadastrais conforme contrato RN06.
    Acessível por Squad 2, Squad 3, Submissões e Financeiro.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        self.check_permissions(request)
        usuario_id = pk or request.user.id
        dados = UsuarioService.obter_dados_cadastrais(usuario_id)
        if not dados:
            return Response({'detail': _('Usuário não encontrado.')}, status=status.HTTP_404_NOT_FOUND)
        serializer = DadosCadastraisSerializer(dados)
        return Response(serializer.data, status=status.HTTP_200_OK)
