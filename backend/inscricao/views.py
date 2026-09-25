from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from eventos.models import Evento

from .models import Inscricao
from .permissions import IsDonoDaInscricao, IsOrganizadorDoEvento
from .serializers import InscricaoSerializer, MinhaInscricaoSerializer, ParticipanteSerializer
from .services import processar_fila_espera


class InscricaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet RESTful para o gerenciamento de inscrições no SGIE.
    Unifica a criação, cancelamento e consulta pessoal (minhas inscrições).
    """
    queryset = Inscricao.objects.all()
    serializer_class = InscricaoSerializer

    def get_permissions(self):
        if self.action in {'retrieve', 'destroy', 'update', 'partial_update'}:
            permission_classes = [IsAuthenticated, IsDonoDaInscricao]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'minhas':
            return MinhaInscricaoSerializer
        return InscricaoSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Inscricao.objects.none()
        if self.action in {'retrieve', 'destroy', 'update', 'partial_update'}:
            return Inscricao.objects.all().select_related('evento', 'usuario')
        if user.is_staff or user.is_superuser:
            return Inscricao.objects.all().select_related('evento', 'usuario')
        return Inscricao.objects.filter(usuario=user).select_related('evento', 'usuario')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            evento = serializer.validated_data['evento']

            inscricoes_ocupadas = Inscricao.objects.filter(
                evento=evento,
                status__in=['confirmada', 'pendente_pagamento']
            ).count()

            status_inscricao = 'confirmada'

            if inscricoes_ocupadas >= evento.capacidade:
                status_inscricao = 'lista_espera'
            elif not evento.e_gratuito:
                status_inscricao = 'pendente_pagamento'

            inscricao = serializer.save(
                usuario=request.user,
                status=status_inscricao
            )

            return Response({
                "mensagem": "Inscrição processada com sucesso.",
                "status": inscricao.status,
                "inscricao_id": inscricao.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        instance.status = 'cancelada'
        instance.save()
        processar_fila_espera(instance.evento)

    @action(detail=False, methods=['get'], url_path='minhas')
    def minhas(self, request):
        """
        Lista as inscrições do participante autenticado (página
        "Minhas inscrições e ingresso" do módulo de Inscrições).
        Suporta filtro opcional por status via ?status=confirmada
        e busca opcional pelo nome do evento via ?busca=termo.
        """
        queryset = Inscricao.objects.filter(
            usuario=request.user
        ).select_related('evento').order_by('-data_inscricao')

        status_param = request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        busca = request.query_params.get('busca', None)
        if busca:
            queryset = queryset.filter(evento__nome__icontains=busca)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ListaInscritosView(generics.ListAPIView):
    """
    Lista os participantes inscritos em um evento (página "Consulta de
    participantes" do módulo de Inscrições). Restrita ao organizador do
    evento. Suporta filtro opcional por status via ?status=confirmada e
    busca opcional por nome/e-mail do participante via ?busca=termo.
    """
    serializer_class = ParticipanteSerializer
    permission_classes = [IsAuthenticated, IsOrganizadorDoEvento]

    def get_evento(self):
        evento = get_object_or_404(Evento, pk=self.kwargs['evento_id'])
        self.check_object_permissions(self.request, evento)
        return evento

    def get_queryset(self):
        evento = self.get_evento()
        status_param = self.request.query_params.get('status', None)
        busca = self.request.query_params.get('busca', None)

        queryset = Inscricao.objects.filter(
            evento=evento
        ).select_related('usuario').order_by('data_inscricao')

        if status_param:
            queryset = queryset.filter(status=status_param)

        if busca:
            queryset = queryset.filter(
                Q(usuario__nome_completo__icontains=busca) | Q(usuario__email__icontains=busca)
            )

        return queryset


class BuscarParticipanteCredenciamentoView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizadorDoEvento]

    def get(self, request, *args, **kwargs):
        evento_id = request.query_params.get('evento_id')
        query = request.query_params.get('query', '').strip()

        if not evento_id:
            return Response({'error': 'Selecione um evento.'}, status=status.HTTP_400_BAD_REQUEST)

        evento = get_object_or_404(Evento, id=evento_id)

        self.check_object_permissions(request, evento)

        inscricoes = Inscricao.objects.filter(evento=evento).select_related('usuario')

        if query:
            inscricoes = inscricoes.filter(
                Q(id__exact=query if query.isdigit() else None) |
                Q(usuario__nome_completo__icontains=query) |
                Q(usuario__email__icontains=query)
            )

        data = [
            {
                'id': inc.id,
                'usuario_nome': inc.usuario.nome_completo or inc.usuario.email,
                'usuario_email': inc.usuario.email,
                'status': inc.status,
                'presenca_registrada': getattr(inc, 'presenca_registrada', False) or (
                    inc.dados_adicionais.get('presenca_registrada', False)
                    if isinstance(inc.dados_adicionais, dict) else False
                )
            }
            for inc in inscricoes
        ]

        return Response({'participantes': data}, status=status.HTTP_200_OK)


class RegistrarPresencaView(APIView):
    permission_classes = [IsAuthenticated, IsOrganizadorDoEvento]

    def post(self, request, inscricao_id, *args, **kwargs):
        inscricao = get_object_or_404(Inscricao, id=inscricao_id)

        self.check_object_permissions(request, inscricao.evento)

        if inscricao.status != 'confirmada':
            return Response(
                {'error': 'Inscrição não apta para credenciamento!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ja_registrada = getattr(inscricao, 'presenca_registrada', False)
        if isinstance(inscricao.dados_adicionais, dict) and inscricao.dados_adicionais.get('presenca_registrada'):
            ja_registrada = True

        if ja_registrada:
            return Response(
                {'warning': 'Presença já havia sido registrada anteriormente!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        inscricao.presenca_registrada = True
        if not isinstance(inscricao.dados_adicionais, dict):
            inscricao.dados_adicionais = {}
        inscricao.dados_adicionais['presenca_registrada'] = True
        inscricao.save()

        nome_usuario = inscricao.usuario.nome_completo or inscricao.usuario.email

        return Response(
            {'success': f'Presença de {nome_usuario} registrada com sucesso!'},
            status=status.HTTP_200_OK
        )
