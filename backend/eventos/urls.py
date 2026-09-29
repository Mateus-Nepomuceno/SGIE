from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'eventos'

router = DefaultRouter()
router.register(r'eventos', views.EventoViewSet, basename='sgie_eventos')
router.register(r'organizadores-evento', views.EquipeOrganizadoraViewSet, basename='sgie_organizadores_evento')
router.register(r'regras-submissao', views.RegraSubmissaoViewSet, basename='sgie_regras_submissao')

urlpatterns = [
    path('eventos/meus/', views.EventoViewSet.as_view({'get': 'meus_eventos'}), name='api_v1_meus_eventos_alias'),
    path('', include(router.urls)),
]
