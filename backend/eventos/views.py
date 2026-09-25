from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from usuarios.models import Papel

from .models import (
    EquipeOrganizadora,
    Evento,
    RegraSubmissao,
    StatusEvento,
    VisibilidadeEvento,
)
from .permissions import (
    IsEventoOrganizadorOrReadOnly,
    IsEventoSubResourceOrganizadorOrReadOnly,
)
from .serializers import (
    CancelarEventoSerializer,
    EquipeOrganizadoraSerializer,
    EventoCreateUpdateSerializer,
    EventoDetailSerializer,
    EventoListSerializer,
    RegraSubmissaoSerializer,
)
from .services import EventoService


class EventoViewSet(viewsets.ModelViewSet):

    permission_classes = [IsEventoOrganizadorOrReadOnly]
    parser_classes = [JSONParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return EventoListSerializer
        if self.action in {'create', 'update', 'partial_update'}:
            return EventoCreateUpdateSerializer
        if self.action == 'cancelar':
            return CancelarEventoSerializer
        return EventoDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Evento.objects.all().select_related(
            'usuario_representante',
            'regra_submissao',
        ).prefetch_related(
            'organizadores',
        )

        if not (user and user.is_authenticated):
            queryset = queryset.filter(
                visibilidade=VisibilidadeEvento.PUBLICO,
            ).exclude(status__in=[StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO])
        elif not (user.is_staff or user.is_superuser):
            papeis_evento_ids = user.papeis_contextuais.filter(
                papel=Papel.ORGANIZADOR,
                ativo=True,
            ).values_list('evento_id', flat=True)

            queryset = queryset.filter(
                Q(visibilidade=VisibilidadeEvento.PUBLICO)
                & ~Q(status__in=[StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO])
                | Q(usuario_representante=user)
                | Q(id__in=papeis_evento_ids)
            ).distinct()

        params = self.request.query_params

        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        modalidade = params.get('modalidade')
        if modalidade:
            queryset = queryset.filter(modalidade=modalidade)

        status_param = params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        visibilidade = params.get('visibilidade')
        if visibilidade:
            queryset = queryset.filter(visibilidade=visibilidade)

        e_gratuito = params.get('e_gratuito')
        if e_gratuito is not None:
            if e_gratuito.lower() in {'true', '1'}:
                queryset = queryset.filter(e_gratuito=True)
            elif e_gratuito.lower() in {'false', '0'}:
                queryset = queryset.filter(e_gratuito=False)

        busca = params.get('search')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) | Q(descricao__icontains=busca) | Q(local__icontains=busca)
            )

        data_inicio = params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(data__gte=data_inicio)

        data_fim = params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(data__lte=data_fim)

        return queryset.order_by('-data', '-hora_inicio')

    @action(detail=False, methods=['get'], url_path='meus-eventos', permission_classes=[IsAuthenticated])
    def meus_eventos(self, request):
        user = request.user
        papeis_evento_ids = user.papeis_contextuais.filter(
            papel=Papel.ORGANIZADOR,
            ativo=True,
        ).values_list('evento_id', flat=True)

        eventos = self.get_queryset().filter(
            Q(usuario_representante=user) | Q(id__in=papeis_evento_ids)
        ).distinct().order_by('-criado_em')

        serializer = EventoListSerializer(eventos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def publicar(self, request, pk=None):
        evento = self.get_object()
        try:
            evento_publicado = EventoService.publicar_evento(evento, request.user)
            serializer = EventoDetailSerializer(evento_publicado, context={'request': request})
            return Response(
                {'detail': _('Evento publicado com sucesso.'), 'evento': serializer.data},
                status=status.HTTP_200_OK,
            )
        except (DjangoValidationError, ValidationError) as exc:
            return Response({'detail': exc.message if hasattr(exc, 'message') else str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='abrir-inscricoes')
    def abrir_inscricoes(self, request, pk=None):
        evento = self.get_object()
        try:
            evento_aberto = EventoService.abrir_inscricoes(evento, request.user)
            serializer = EventoDetailSerializer(evento_aberto, context={'request': request})
            return Response(
                {'detail': _('Inscrições abertas com sucesso.'), 'evento': serializer.data},
                status=status.HTTP_200_OK,
            )
        except (DjangoValidationError, ValidationError) as exc:
            return Response({'detail': exc.message if hasattr(exc, 'message') else str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        evento = self.get_object()
        serializer = CancelarEventoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo = serializer.validated_data.get('motivo', '')

        try:
            evento_cancelado = EventoService.cancelar_evento(evento, request.user, motivo)
            detail_serializer = EventoDetailSerializer(evento_cancelado, context={'request': request})
            return Response(
                {'detail': _('Evento cancelado com sucesso.'), 'evento': detail_serializer.data},
                status=status.HTTP_200_OK,
            )
        except (DjangoValidationError, ValidationError) as exc:
            return Response({'detail': exc.message if hasattr(exc, 'message') else str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        evento = self.get_object()
        try:
            evento_finalizado = EventoService.finalizar_evento(evento, request.user)
            serializer = EventoDetailSerializer(evento_finalizado, context={'request': request})
            return Response(
                {'detail': _('Evento finalizado com sucesso.'), 'evento': serializer.data},
                status=status.HTTP_200_OK,
            )
        except (DjangoValidationError, ValidationError) as exc:
            return Response({'detail': exc.message if hasattr(exc, 'message') else str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def arquivar(self, request, pk=None):
        evento = self.get_object()
        try:
            evento_arquivado = EventoService.arquivar_evento(evento, request.user)
            serializer = EventoDetailSerializer(evento_arquivado, context={'request': request})
            return Response(
                {'detail': _('Evento arquivado com sucesso.'), 'evento': serializer.data},
                status=status.HTTP_200_OK,
            )
        except (DjangoValidationError, ValidationError) as exc:
            return Response({'detail': exc.message if hasattr(exc, 'message') else str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='status-inscricoes')
    def status_inscricoes(self, request, pk=None):
        evento = self.get_object()
        encerradas = EventoService.verificar_inscricoes_encerradas(evento)
        return Response(
            {
                'evento_id': evento.id,
                'inscricoes_abertas': not encerradas,
                'inscricoes_encerradas': encerradas,
                'limite_encerramento': evento.limite_encerramento_inscricoes,
                'status_atual': evento.status,
            },
            status=status.HTTP_200_OK,
        )


class EquipeOrganizadoraViewSet(viewsets.ModelViewSet):

    queryset = EquipeOrganizadora.objects.all()
    serializer_class = EquipeOrganizadoraSerializer
    permission_classes = [IsEventoSubResourceOrganizadorOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        evento_id = self.request.query_params.get('evento_id')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return qs


class RegraSubmissaoViewSet(viewsets.ModelViewSet):

    queryset = RegraSubmissao.objects.all()
    serializer_class = RegraSubmissaoSerializer
    permission_classes = [IsEventoSubResourceOrganizadorOrReadOnly]
