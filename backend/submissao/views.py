from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class SubmissaoViewSet(viewsets.ViewSet):
    """
    ViewSet para o módulo de submissão do SGIE.
    Retorna status indicando a disponibilidade do módulo.
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        return Response(
            {
                'status': 'disponivel',
                'modulo': 'submissao',
                'mensagem': 'Módulo de submissão disponível.',
                'disponivel': True,
            },
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, pk=None, *args, **kwargs):
        return Response(
            {
                'status': 'disponivel',
                'modulo': 'submissao',
                'mensagem': 'Módulo de submissão disponível.',
                'disponivel': True,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        return Response(
            {
                'status': 'disponivel',
                'modulo': 'submissao',
                'mensagem': 'Módulo de submissão disponível.',
                'disponivel': True,
            },
            status=status.HTTP_200_OK,
        )
