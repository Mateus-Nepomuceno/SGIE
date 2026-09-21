from django.urls import include, path
from rest_framework.routers import DefaultRouter

from usuarios.views import (
    DadosCadastraisAPIView,
    PapelContextualViewSet,
    PerfilOrganizadorViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='sgie_usuarios')
router.register(r'organizadores', PerfilOrganizadorViewSet, basename='sgie_organizadores')
router.register(r'papeis-contextuais', PapelContextualViewSet, basename='sgie_papeis')

urlpatterns = [
    path('usuarios/dados-cadastrais/', DadosCadastraisAPIView.as_view(), name='api_v1_dados_cadastrais_me'),
    path('usuarios/dados-cadastrais/<int:pk>/', DadosCadastraisAPIView.as_view(), name='api_v1_dados_cadastrais'),
    path('', include(router.urls)),
]
