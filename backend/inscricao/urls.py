from django.urls import path
from .views import RealizarInscricaoView, InscricaoDetailView, ListaInscritosView, MinhasInscricoesView

urlpatterns = [
    path('inscricao/', RealizarInscricaoView.as_view(), name='realizar-inscricao'),
    path('inscricao/<int:pk>/', InscricaoDetailView.as_view(), name='inscricao-detail'),
    path('inscricoes/minhas/', MinhasInscricoesView.as_view(), name='minhas-inscricoes'),
    path('eventos/<int:evento_id>/inscritos/', ListaInscritosView.as_view(), name='lista-inscritos-evento'),
]
