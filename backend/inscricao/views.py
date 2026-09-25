from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from eventos.models import Evento

from .models import Inscricao
from .permissions import IsDonoDaInscricao, IsOrganizadorDoEvento
from .serializers import InscricaoSerializer, MinhaInscricaoSerializer, ParticipanteSerializer
from .services import processar_fila_espera

class RealizarInscricaoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = InscricaoSerializer(data=request.data)

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

class InscricaoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inscricao.objects.all()
    serializer_class = InscricaoSerializer

    permission_classes = [IsAuthenticated, IsDonoDaInscricao]

    def perform_destroy(self, instance):
        instance.status = 'cancelada'
        instance.save()
        processar_fila_espera(instance.evento)

class MinhasInscricoesView(generics.ListAPIView):
    """
    Lista as inscrições do participante autenticado (página
    "Minhas inscrições e ingresso" do módulo de Inscrições).
    Suporta filtro opcional por status via ?status=confirmada
    e busca opcional pelo nome do evento via ?busca=termo.
    """
    serializer_class = MinhaInscricaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Inscricao.objects.filter(
            usuario=self.request.user
        ).select_related('evento').order_by('-data_inscricao')

        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)

        busca = self.request.query_params.get('busca', None)
        if busca:
            queryset = queryset.filter(evento__nome__icontains=busca)

        return queryset

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
