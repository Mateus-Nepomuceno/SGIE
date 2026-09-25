from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'inscricoes', views.InscricaoViewSet, basename='sgie_inscricoes')

urlpatterns = [
    path('eventos/<int:evento_id>/inscritos/', views.ListaInscritosView.as_view(), name='lista-inscritos-evento'),
    path('credenciamento/buscar/', views.BuscarParticipanteCredenciamentoView.as_view(), name='credenciamento_buscar'),
    path('credenciamento/<int:inscricao_id>/confirmar/', views.RegistrarPresencaView.as_view(), name='registrar_presenca'),
    path('', include(router.urls)),
]
