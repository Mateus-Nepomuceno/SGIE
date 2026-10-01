from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from usuarios.views import (
    CustomTokenObtainPairView,
    RedefinirSenhaAPIView,
    SolicitarRecuperacaoSenhaAPIView,
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('recuperar-senha/', SolicitarRecuperacaoSenhaAPIView.as_view(), name='auth_recuperar_senha'),
    path('redefinir-senha/', RedefinirSenhaAPIView.as_view(), name='auth_redefinir_senha'),
]
