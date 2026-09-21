from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import PerfilOrganizador, Usuario
from .validators import limpar_cpf, validar_cpf, validar_extensao_imagem, validar_telefone

TAMANHO_MIN_NOME = 3


class CadastroUsuarioForm(forms.ModelForm):
    """
    Formulário padrão para registro de novos usuários (RF01, RN01).
    Valida obrigatoriedade, unicidade de e-mail/CPF e integridade matemática de documento.
    """

    password1 = forms.CharField(
        label=_('Senha'),
        widget=forms.PasswordInput(attrs={'minlength': '8', 'required': 'required'}),
        help_text=_('A senha deve conter no mínimo 8 caracteres.'),
    )
    password2 = forms.CharField(
        label=_('Confirmação de Senha'),
        widget=forms.PasswordInput(attrs={'minlength': '8', 'required': 'required'}),
    )

    class Meta:
        model = Usuario
        fields = ['nome_completo', 'email', 'cpf', 'data_nascimento', 'telefone']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'maxlength': '150', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'required': 'required'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00', 'maxlength': '14', 'required': 'required'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'required': 'required'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(71) 99999-9999', 'maxlength': '20', 'required': 'required'}),
        }

    def clean_nome_completo(self):
        nome = self.cleaned_data.get('nome_completo', '').strip()
        if len(nome) < TAMANHO_MIN_NOME:
            raise ValidationError(_('O nome completo deve conter no mínimo 3 caracteres.'), code='nome_curto')
        return nome

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '').strip()
        validar_cpf(cpf)
        cpf_limpo = limpar_cpf(cpf)

        qs = Usuario.objects.filter(cpf=cpf_limpo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(_('Já existe um usuário cadastrado com este CPF.'), code='cpf_duplicado')

        return cpf_limpo

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError(_('O e-mail é obrigatório.'))

        qs = Usuario.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(_('Já existe um usuário cadastrado com este e-mail.'), code='email_duplicado')

        return email

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '').strip()
        validar_telefone(telefone)
        return telefone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        if p1 and p2:
            if p1 != p2:
                self.add_error('password2', ValidationError(_('As senhas não coincidem.'), code='senhas_divergentes'))
            else:
                validate_password(p1)

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
        return usuario


class AutenticacaoForm(forms.Form):
    """
    Formulário de login tradicional por identificador (E-mail ou CPF) e senha (RF02).
    """

    identificador = forms.CharField(
        label=_('E-mail ou CPF'),
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu E-mail ou CPF', 'required': 'required'}),
    )
    password = forms.CharField(
        label=_('Senha'),
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha', 'required': 'required'}),
    )


class RecuperarSenhaForm(forms.Form):
    """
    Etapa 1 da recuperação de senha: solicitação de código para o e-mail cadastrado (RF03).
    """

    email = forms.EmailField(
        label=_('E-mail cadastrado'),
        widget=forms.EmailInput(attrs={'placeholder': 'seu.email@universidade.edu.br', 'required': 'required'}),
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


class RedefinirSenhaForm(forms.Form):
    """
    Etapa 2 da recuperação de senha: validação do código de 6 dígitos e definição da nova senha (RF03).
    """

    codigo = forms.CharField(
        label=_('Código de Verificação'),
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': '123456', 'maxlength': '6', 'required': 'required'}),
    )
    nova_senha = forms.CharField(
        label=_('Nova Senha'),
        widget=forms.PasswordInput(attrs={'minlength': '8', 'required': 'required'}),
    )
    confirmacao_senha = forms.CharField(
        label=_('Confirmação da Nova Senha'),
        widget=forms.PasswordInput(attrs={'minlength': '8', 'required': 'required'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        s1 = cleaned_data.get('nova_senha')
        s2 = cleaned_data.get('confirmacao_senha')

        if s1 and s2:
            if s1 != s2:
                self.add_error('confirmacao_senha', ValidationError(_('As senhas não coincidem.'), code='senhas_divergentes'))
            else:
                validate_password(s1)

        return cleaned_data


class PerfilOrganizadorForm(forms.ModelForm):
    """
    Formulário para preenchimento de perfil estendido de organizador (RF04, RN04).
    """

    class Meta:
        model = PerfilOrganizador
        fields = ['foto_de_perfil', 'banner', 'bio_do_organizador']
        widgets = {
            'foto_de_perfil': forms.FileInput(attrs={'accept': 'image/*'}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
            'bio_do_organizador': forms.Textarea(
                attrs={
                    'rows': 4,
                    'cols': 50,
                    'maxlength': '1000',
                    'placeholder': 'Escreva sobre sua experiência e atuação acadêmica...',
                }
            ),
        }

    def clean_foto_de_perfil(self):
        arquivo = self.cleaned_data.get('foto_de_perfil')
        if arquivo:
            validar_extensao_imagem(arquivo)
            if hasattr(arquivo, 'size') and arquivo.size > 5 * 1024 * 1024:
                raise ValidationError(_('A foto de perfil não pode exceder 5 MB.'))
        return arquivo

    def clean_banner(self):
        arquivo = self.cleaned_data.get('banner')
        if arquivo:
            validar_extensao_imagem(arquivo)
            if hasattr(arquivo, 'size') and arquivo.size > 10 * 1024 * 1024:
                raise ValidationError(_('O banner não pode exceder 10 MB.'))
        return arquivo


class AtualizarUsuarioForm(forms.ModelForm):
    """
    Formulário para edição dos dados cadastrais permitidos pelo usuário.
    """

    class Meta:
        model = Usuario
        fields = ['nome_completo', 'telefone', 'data_nascimento']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'maxlength': '150', 'required': 'required'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(71) 99999-9999', 'maxlength': '20', 'required': 'required'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'required': 'required'}),
        }

    def clean_telefone(self):
        tel = self.cleaned_data.get('telefone', '').strip()
        validar_telefone(tel)
        return tel
