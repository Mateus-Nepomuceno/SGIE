from django.urls import path
from .views import RealizarInscricaoView, InscricaoDetailView, ListaInscritosView, MinhasInscricoesView, BuscarParticipanteCredenciamentoView, RegistrarPresencaView

urlpatterns = [
    path('inscricao/', RealizarInscricaoView.as_view(), name='realizar-inscricao'),
    path('inscricao/<int:pk>/', InscricaoDetailView.as_view(), name='inscricao-detail'),
    path('inscricoes/minhas/', MinhasInscricoesView.as_view(), name='minhas-inscricoes'),
    path('eventos/<int:evento_id>/inscritos/', ListaInscritosView.as_view(), name='lista-inscritos-evento'),
    path('credenciamento/buscar/', BuscarParticipanteCredenciamentoView.as_view(), name='credenciamento_buscar'),
    path('credenciamento/<int:inscricao_id>/confirmar/', RegistrarPresencaView.as_view(), name='registrar_presenca'),
]
