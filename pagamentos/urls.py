from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaPrecoViewSet,
    CertificadoViewSet,
    CobrancaViewSet,
    LoteViewSet,
    PagamentoViewSet,
    ReembolsoViewSet,
    RelatorioFinanceiroEventoView,
    WebhookPagamentoView,
)

router = DefaultRouter()
router.register(r'categorias-preco', CategoriaPrecoViewSet, basename='sgie_categorias_preco')
router.register(r'lotes', LoteViewSet, basename='sgie_lotes')
router.register(r'cobrancas', CobrancaViewSet, basename='sgie_cobrancas')
router.register(r'pagamentos', PagamentoViewSet, basename='sgie_pagamentos')
router.register(r'reembolsos', ReembolsoViewSet, basename='sgie_reembolsos')
router.register(r'certificados', CertificadoViewSet, basename='sgie_certificados')

urlpatterns = [
    path('pagamentos/webhook/', WebhookPagamentoView.as_view(), name='pagamento_webhook'),
    path(
        'eventos/<int:evento_id>/relatorio-financeiro/',
        RelatorioFinanceiroEventoView.as_view(),
        name='evento_relatorio_financeiro',
    ),
    path('', include(router.urls)),
]
