from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import (
    AtualizarUsuarioForm,
    AutenticacaoForm,
    CadastroUsuarioForm,
    PerfilOrganizadorForm,
    RecuperarSenhaForm,
    RedefinirSenhaForm,
)
from .models import PapelContextual, PerfilOrganizador, Usuario
from .permissions import IsSelfOrAdmin
from .serializers import (
    DadosCadastraisSerializer,
    PapelContextualSerializer,
    PerfilOrganizadorSerializer,
    UsuarioCadastroSerializer,
    UsuarioSerializer,
)
from .services import UsuarioService

# ==========================================
# Views Web Tradicionais (Django MTV)
# ==========================================


def cadastro_view(request: HttpRequest) -> HttpResponse:
    """Tela e processamento de cadastro de novos usuários (RF01, RN01)."""
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Cadastro realizado com sucesso! Faça login para acessar o sistema.'))
            return redirect('usuarios:login')
    else:
        form = CadastroUsuarioForm()

    return render(request, 'usuarios/cadastro.html', {'form': form})


def login_view(request: HttpRequest) -> HttpResponse:
    """Tela e processamento de login híbrido por E-mail ou CPF (RF02)."""
    if request.user.is_authenticated:
        return redirect('usuarios:perfil')

    next_url = request.POST.get('next') or request.GET.get('next') or 'usuarios:perfil'

    if request.method == 'POST':
        form = AutenticacaoForm(request.POST)
        if form.is_valid():
            identificador = form.cleaned_data['identificador']
            password = form.cleaned_data['password']

            usuario = UsuarioService.autenticar_usuario(request, identificador, password)
            if usuario is not None:
                auth_login(request, usuario)
                messages.success(request, _('Bem-vindo(a), %(nome)s!') % {'nome': usuario.nome_completo})
                return redirect(next_url)
            else:
                messages.error(request, _('Identificador (E-mail ou CPF) ou senha inválidos.'))
    else:
        form = AutenticacaoForm()

    return render(request, 'usuarios/login.html', {'form': form, 'next': next_url})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Encerra a sessão HTTP autenticada."""
    auth_logout(request)
    messages.info(request, _('Você encerrou sua sessão com segurança.'))
    return redirect('usuarios:login')


def recuperar_senha_view(request: HttpRequest) -> HttpResponse:
    """Etapa 1 da recuperação de acesso: envio de código de 6 dígitos por e-mail (RF03)."""
    if request.method == 'POST':
        form = RecuperarSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            UsuarioService.gerar_codigo_recuperacao(email)
            request.session['recuperacao_email'] = email
            messages.info(request, _('Se o e-mail informado constar em nossa base de dados, um código de verificação de 6 dígitos foi enviado.'))
            return redirect('usuarios:redefinir_senha')
    else:
        form = RecuperarSenhaForm()

    return render(request, 'usuarios/recuperar_senha.html', {'form': form, 'etapa': 'solicitar'})


def redefinir_senha_view(request: HttpRequest) -> HttpResponse:
    """Etapa 2 da recuperação de acesso: validação do código e nova senha (RF03)."""
    email_sessao = request.session.get('recuperacao_email', '')

    if request.method == 'POST':
        form = RedefinirSenhaForm(request.POST)
        email = request.POST.get('email', email_sessao).strip().lower()

        if form.is_valid():
            codigo = form.cleaned_data['codigo']
            nova_senha = form.cleaned_data['nova_senha']
            try:
                UsuarioService.redefinir_senha_com_codigo(email, codigo, nova_senha)
                messages.success(request, _('Senha atualizada com sucesso! Efetue login com sua nova senha.'))
                request.session.pop('recuperacao_email', None)
                return redirect('usuarios:login')
            except ValidationError as e:
                msg = e.message if hasattr(e, 'message') else str(e)
                messages.error(request, msg)
    else:
        form = RedefinirSenhaForm()

    return render(
        request,
        'usuarios/recuperar_senha.html',
        {'form': form, 'etapa': 'redefinir', 'email': email_sessao},
    )


@login_required
def perfil_view(request: HttpRequest) -> HttpResponse:
    """
    Painel de perfil do usuário (RF04, RN04, RN06).
    Exibe dados cadastrais e permite requisição e edição do perfil de organizador.
    """
    usuario = request.user
    perfil_org = getattr(usuario, 'perfil_organizador', None)

    form_usuario = AtualizarUsuarioForm(instance=usuario)
    form_org = PerfilOrganizadorForm(instance=perfil_org)

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'salvar_dados':
            form_usuario = AtualizarUsuarioForm(request.POST, instance=usuario)
            if form_usuario.is_valid():
                form_usuario.save()
                messages.success(request, _('Seus dados cadastrais foram atualizados com sucesso.'))
                return redirect('usuarios:perfil')
        elif acao == 'salvar_organizador':
            form_org = PerfilOrganizadorForm(request.POST, request.FILES, instance=perfil_org)
            if form_org.is_valid():
                org = form_org.save(commit=False)
                org.usuario = usuario
                org.save()
                messages.success(request, _('Perfil de organizador salvo com sucesso!'))
                return redirect('usuarios:perfil')

    return render(
        request,
        'usuarios/perfil.html',
        {
            'usuario': usuario,
            'perfil_org': perfil_org,
            'form_usuario': form_usuario,
            'form_org': form_org,
        },
    )


def google_login_view(request: HttpRequest) -> HttpResponse:
    """
    Ponto de entrada / simulação de autenticação Google OAuth2 (RF02).
    Em ambiente de desenvolvimento e testes, fornece uma rota estável para o fluxo federado.
    """
    messages.info(request, _('Autenticação Google OAuth2: Redirecionando para login seguro...'))
    # Fluxo federado: direciona para login ou formulário complementar conforme RF02
    return redirect('usuarios:login')


# ==========================================
# ViewSets e Endpoints API REST (DRF)
# ==========================================


class UsuarioViewSet(viewsets.ModelViewSet):
    """API REST para consulta e gerenciamento de usuários."""

    queryset = Usuario.objects.all().order_by('id')
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated(), IsSelfOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCadastroSerializer
        return UsuarioSerializer


class PerfilOrganizadorViewSet(viewsets.ModelViewSet):
    """API REST para perfis de organizadores."""

    queryset = PerfilOrganizador.objects.select_related('usuario').all().order_by('id')
    serializer_class = PerfilOrganizadorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class PapelContextualViewSet(viewsets.ModelViewSet):
    """API REST para verificação e concessão de papéis contextuais por evento (RN03)."""

    queryset = PapelContextual.objects.select_related('usuario').all().order_by('id')
    serializer_class = PapelContextualSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        evento_id = self.request.query_params.get('evento_id')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        return qs


class DadosCadastraisAPIView(APIView):
    """
    Endpoint de integração para consulta de dados cadastrais conforme contrato RN06.
    Acessível por Squad 2, Squad 3, Submissões e Financeiro.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        self.check_permissions(request)
        usuario_id = pk or request.user.id
        dados = UsuarioService.obter_dados_cadastrais(int(usuario_id))
        if not dados:
            return Response({'detail': _('Usuário não encontrado.')}, status=status.HTTP_404_NOT_FOUND)
        serializer = DadosCadastraisSerializer(dados)
        return Response(serializer.data, status=status.HTTP_200_OK)
