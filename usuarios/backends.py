from typing import override

from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from .models import Usuario
from .validators import TAMANHO_CPF, limpar_cpf


class EmailOrCPFBackend(ModelBackend):
    """
    Backend de autenticação customizado do SGIE.
    Permite que o usuário efetue login indistintamente através de seu E-mail OU CPF (RF02, RN01).
    """

    @override
    def authenticate(self, request, username=None, password=None, identificador=None, **kwargs):
        identificador = identificador or username or kwargs.get('email')
        if not identificador or not password:
            return None

        identificador_str = str(identificador).strip()
        email_cand = identificador_str.lower()
        cpf_cand = limpar_cpf(identificador_str)

        criterios = Q(email__iexact=email_cand)
        if len(cpf_cand) == TAMANHO_CPF:
            criterios |= Q(cpf=cpf_cand)

        usuario = Usuario.objects.filter(criterios).first()

        if usuario and usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario

        return None

    @override
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except (Usuario.DoesNotExist, DjangoValidationError, ValueError):
            return None
