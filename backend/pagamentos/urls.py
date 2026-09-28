from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'pagamentos'

router = DefaultRouter()
router.register(r'pagamentos', views.PagamentoViewSet, basename='sgie_pagamentos')

urlpatterns = [
    path(
        'pagamento/',
        views.PagamentoViewSet.as_view({'get': 'list'}),
        name='pagamento',
    ),
    path('', include(router.urls)),
]
