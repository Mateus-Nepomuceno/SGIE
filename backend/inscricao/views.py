from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from eventos.models import Evento
from .models import Inscricao
from .serializers import InscricaoSerializer
from .permissions import IsDonoDaInscricao
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

class ListaInscritosView(generics.ListAPIView):
    serializer_class = InscricaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        evento_id = self.kwargs['evento_id']
        status_param = self.request.query_params.get('status', None)

        queryset = Inscricao.objects.filter(evento_id=evento_id).order_by('data_inscricao')

        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset
