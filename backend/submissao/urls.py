from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'submissao'

router = DefaultRouter()
router.register(r'submissoes', views.SubmissaoViewSet, basename='sgie_submissoes')

urlpatterns = [
    path('submissao/', views.SubmissaoViewSet.as_view({'get': 'list', 'post': 'create'}), name='submissao'),
    path('', include(router.urls)),
]
