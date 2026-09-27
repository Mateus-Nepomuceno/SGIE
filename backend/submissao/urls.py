from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'submissao'

router = DefaultRouter()
router.register(r'areas', views.AreaViewSet, basename='sgie_areas')
router.register(r'submissoes', views.SubmissaoViewSet, basename='sgie_submissoes')
router.register(r'autores-submissao', views.SubmissaoAutorViewSet, basename='sgie_autores_submissao')
router.register(r'versoes-submissao', views.SubmissaoVersaoViewSet, basename='sgie_versoes_submissao')
router.register(r'avaliacoes', views.AvaliacaoViewSet, basename='sgie_avaliacoes')
router.register(r'locais-apresentacao', views.LocalViewSet, basename='sgie_locais_apresentacao')
router.register(r'apresentacoes', views.ApresentacaoViewSet, basename='sgie_apresentacoes')

urlpatterns = [
    path('', include(router.urls)),
]
