from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='api_usuarios')
router.register(r'organizadores', views.PerfilOrganizadorViewSet, basename='api_organizadores')
router.register(r'papeis-contextuais', views.PapelContextualViewSet, basename='api_papeis_contextuais')

urlpatterns = [
    # Rotas Web (Django MTV)
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-senha/', views.recuperar_senha_view, name='recuperar_senha'),
    path('redefinir-senha/', views.redefinir_senha_view, name='redefinir_senha'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('login/google/', views.google_login_view, name='google_login'),
    # Rotas de Integração REST e Contratos de Dados (RN06)
    path('api/dados-cadastrais/', views.DadosCadastraisAPIView.as_view(), name='api_dados_cadastrais_me'),
    path('api/dados-cadastrais/<int:pk>/', views.DadosCadastraisAPIView.as_view(), name='api_dados_cadastrais'),
    path('api/', include(router.urls)),
]
