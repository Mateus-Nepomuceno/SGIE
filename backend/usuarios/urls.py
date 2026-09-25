from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='sgie_usuarios')
router.register(r'organizadores', views.PerfilOrganizadorViewSet, basename='sgie_organizadores')
router.register(r'papeis-contextuais', views.PapelContextualViewSet, basename='sgie_papeis')

urlpatterns = [
    path('usuarios/cadastro/', views.UsuarioViewSet.as_view({'post': 'create'}), name='api_v1_cadastro'),
    path('usuarios/perfil/', views.UsuarioViewSet.as_view({'get': 'me', 'put': 'me', 'patch': 'me'}), name='api_v1_perfil'),
    path('usuarios/recuperar-senha/', views.SolicitarRecuperacaoSenhaAPIView.as_view(), name='api_v1_recuperar_senha'),
    path('usuarios/redefinir-senha/', views.RedefinirSenhaAPIView.as_view(), name='api_v1_redefinir_senha'),
    path('usuarios/dados-cadastrais/', views.DadosCadastraisAPIView.as_view(), name='api_v1_dados_cadastrais_me'),
    path('usuarios/dados-cadastrais/<str:pk>/', views.DadosCadastraisAPIView.as_view(), name='api_v1_dados_cadastrais'),
    path('', include(router.urls)),
]
