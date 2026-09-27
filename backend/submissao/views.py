from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Area,
    Apresentacao,
    Avaliacao,
    Local,
    StatusSubmissao,
    Submissao,
    SubmissaoAutor,
    SubmissaoVersao,
)
from .permissions import (
    CanCreateSubmissaoPermission,
    IsAvaliadorOrReadOnly,
    IsOrganiadorEventoOrReadOnly,
    IsSubmissaoAutorOrReadOnly,
)
from .serializers import (
    AprovarSubmissaoSerializer,
    ApresentacaoSerializer,
    AreaSerializer,
    AvaliacaoSerializer,
    RejeitarSubmissaoSerializer,
    SolicitarCorrecaoSerializer,
    SubmeterSubmissaoSerializer,
    SubmissaoAutorSerializer,
    SubmissaoCreateUpdateSerializer,
    SubmissaoDetailSerializer,
    SubmissaoListSerializer,
    SubmissaoVersaoSerializer,
    LocalSerializer,
)
from .services import SubmissaoService


class AreaViewSet(viewsets.ModelViewSet):

    permission_classes = [IsOrganiadorEventoOrReadOnly]
    parser_classes = [JSONParser, FormParser]
    queryset = Area.objects.all()
    serializer_class = AreaSerializer

    def get_queryset(self):
        return Area.objects.all().order_by('nome')


class SubmissaoViewSet(viewsets.ModelViewSet):

    permission_classes = [IsSubmissaoAutorOrReadOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return SubmissaoListSerializer
        if self.action in {'create', 'update', 'partial_update'}:
            return SubmissaoCreateUpdateSerializer
        if self.action == 'submeter':
            return SubmeterSubmissaoSerializer
        if self.action == 'aprovar':
            return AprovarSubmissaoSerializer
        if self.action == 'rejeitar':
            return RejeitarSubmissaoSerializer
        if self.action == 'solicitar_correcao':
            return SolicitarCorrecaoSerializer
        return SubmissaoDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Submissao.objects.all().select_related(
            'evento',
            'area',
            'autor_principal',
        ).prefetch_related(
            'autores',
            'versoes',
            'avaliacoes',
            'apresentacoes',
        )

        if not (user and user.is_authenticated):
            return queryset.none()

        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(autor_principal=user) | Q(evento__usuario_representante=user)
        ).distinct()

    def perform_create(self, serializer):
        try:
            submissao = SubmissaoService.criar_submissao(
                usuario=self.request.user,
                evento_id=serializer.validated_data['evento'].id,
                area_id=serializer.validated_data['area'].id,
                dados_submissao=serializer.validated_data,
            )
            serializer.instance = submissao
        except Exception as exc:
            raise ValidationError(str(exc))

    def perform_update(self, serializer):
        try:
            submissao = SubmissaoService.atualizar_submissao(
                submissao=self.get_object(),
                dados_submissao=serializer.validated_data,
                usuario=self.request.user,
            )
            serializer.instance = submissao
        except Exception as exc:
            raise ValidationError(str(exc))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submeter(self, request, pk=None):
        """Submeter trabalho com arquivo anexado."""
        submissao = self.get_object()
        serializer = SubmeterSubmissaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            versao = SubmissaoService.submeter_trabalho(
                submissao=submissao,
                arquivo=request.FILES['arquivo'],
                usuario=request.user,
            )
            return Response(
                SubmissaoVersaoSerializer(versao).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def aprovar(self, request, pk=None):
        """Aprovar submissão."""
        submissao = self.get_object()
        serializer = AprovarSubmissaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            submissao_atualizada = SubmissaoService.aprovar_submissao(
                submissao=submissao,
                usuario=request.user,
                observacoes=serializer.validated_data.get('observacoes', ''),
            )
            return Response(
                SubmissaoDetailSerializer(submissao_atualizada).data,
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rejeitar(self, request, pk=None):
        """Rejeitar submissão."""
        submissao = self.get_object()
        serializer = RejeitarSubmissaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            submissao_atualizada = SubmissaoService.rejeitar_submissao(
                submissao=submissao,
                usuario=request.user,
                motivo=serializer.validated_data['observacoes'],
            )
            return Response(
                SubmissaoDetailSerializer(submissao_atualizada).data,
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def solicitar_correcao(self, request, pk=None):
        """Solicitar correção na submissão."""
        submissao = self.get_object()
        serializer = SolicitarCorrecaoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            submissao_atualizada = SubmissaoService.solicitar_correcao(
                submissao=submissao,
                usuario=request.user,
                observacoes=serializer.validated_data['observacoes'],
            )
            return Response(
                SubmissaoDetailSerializer(submissao_atualizada).data,
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SubmissaoAutorViewSet(viewsets.ModelViewSet):

    permission_classes = [IsSubmissaoAutorOrReadOnly]
    parser_classes = [JSONParser, FormParser]
    serializer_class = SubmissaoAutorSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = SubmissaoAutor.objects.all().select_related('submissao', 'usuario')

        if not (user and user.is_authenticated):
            return queryset.none()

        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(submissao__autor_principal=user) | Q(submissao__evento__usuario_representante=user)
        ).distinct()


class SubmissaoVersaoViewSet(viewsets.ReadOnlyModelViewSet):

    parser_classes = [JSONParser, FormParser]
    serializer_class = SubmissaoVersaoSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = SubmissaoVersao.objects.all().select_related('submissao')

        if not (user and user.is_authenticated):
            return queryset.none()

        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(submissao__autor_principal=user) | Q(submissao__evento__usuario_representante=user)
        ).distinct()


class AvaliacaoViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAvaliadorOrReadOnly]
    parser_classes = [JSONParser, FormParser]
    serializer_class = AvaliacaoSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Avaliacao.objects.all().select_related('submissao', 'avaliador')

        if not (user and user.is_authenticated):
            return queryset.none()

        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(submissao__evento__usuario_representante=user)
            | Q(avaliador=user)
        ).distinct()


class LocalViewSet(viewsets.ModelViewSet):

    permission_classes = [IsOrganiadorEventoOrReadOnly]
    parser_classes = [JSONParser, FormParser]
    serializer_class = LocalSerializer

    def get_queryset(self):
        return Local.objects.all().select_related('evento')


class ApresentacaoViewSet(viewsets.ModelViewSet):

    permission_classes = [IsOrganiadorEventoOrReadOnly]
    parser_classes = [JSONParser, FormParser]
    serializer_class = ApresentacaoSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Apresentacao.objects.all().select_related('submissao', 'local')

        if not (user and user.is_authenticated):
            return queryset.none()

        if user.is_staff or user.is_superuser:
            return queryset

        return queryset.filter(
            Q(submissao__autor_principal=user) | Q(submissao__evento__usuario_representante=user)
        ).distinct()

