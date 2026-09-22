from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import Usuario


class UsuarioCreationForm(UserCreationForm):
    """Formulário para criação de novos usuários no Django Admin com suporte a campos customizados."""

    class Meta:
        model = Usuario
        fields = ('email', 'cpf', 'nome_completo', 'data_nascimento', 'telefone')


class UsuarioChangeForm(UserChangeForm):
    """Formulário para edição de usuários no Django Admin."""

    class Meta:
        model = Usuario
        fields = '__all__'