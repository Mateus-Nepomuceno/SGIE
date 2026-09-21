from datetime import date, timedelta
from io import BytesIO

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from .forms import (
    AutenticacaoForm,
    CadastroUsuarioForm,
    PerfilOrganizadorForm,
)
from .models import CodigoRecuperacao, Papel, PerfilOrganizador, Usuario
from .permissions import HasEventRolePermission, IsOrganizadorPermission, organizador_required, role_required
from .services import UsuarioService
from .validators import formatar_cpf


def gerar_imagem_teste(nome='teste.jpg', formato='JPEG'):
    """Gera um arquivo de imagem válido em memória para testes de upload."""
    arquivo = BytesIO()
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(arquivo, format=formato)
    arquivo.seek(0)
    return SimpleUploadedFile(nome, arquivo.read(), content_type=f'image/{formato.lower()}')


class TestUsuarioModel(TestCase):
    """Bateria de testes unitários da camada de modelos (CT-MOD-01 a CT-MOD-06)."""

    def setUp(self):
        # CPF válido gerado matematicamente
        self.cpf_valido = '52998224725'
        self.cpf_valido_2 = '11144477735'
        self.usuario_data = {
            'nome_completo': 'Ana Maria Braga',
            'email': 'ana.maria@universidade.edu.br',
            'cpf': self.cpf_valido,
            'data_nascimento': date(1995, 4, 1),
            'telefone': '(71) 98888-1111',
            'password': 'SenhaForteSGIE@2026',
        }

    def test_ct_mod_01_criar_usuario_com_dados_validos(self):
        """CT-MOD-01: Criar usuário com dados válidos e senha criptografada."""
        usuario = Usuario.objects.create_user(**self.usuario_data)
        self.assertIsNotNone(usuario.id)
        self.assertEqual(usuario.email, 'ana.maria@universidade.edu.br')
        self.assertEqual(usuario.cpf, self.cpf_valido)
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        # Senha nunca deve ser armazenada em texto puro
        self.assertNotEqual(usuario.password, self.usuario_data['password'])
        self.assertTrue(usuario.check_password(self.usuario_data['password']))
        self.assertEqual(usuario.cpf_formatado, formatar_cpf(self.cpf_valido))

    def test_ct_mod_02_bloquear_duplicidade_de_email(self):
        """CT-MOD-02: Bloquear duplicidade de e-mail (RN01)."""
        Usuario.objects.create_user(**self.usuario_data)
        dados_duplicados = self.usuario_data.copy()
        dados_duplicados['cpf'] = self.cpf_valido_2

        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(**dados_duplicados)

    def test_ct_mod_03_bloquear_duplicidade_de_cpf(self):
        """CT-MOD-03: Bloquear duplicidade de CPF (RN01)."""
        Usuario.objects.create_user(**self.usuario_data)
        dados_duplicados = self.usuario_data.copy()
        dados_duplicados['email'] = 'outro.email@universidade.edu.br'

        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(**dados_duplicados)

    def test_ct_mod_04_criar_superusuario(self):
        """CT-MOD-04: Criar superusuário com privilégios administrativos."""
        admin = Usuario.objects.create_superuser(**self.usuario_data)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_organizador())

    def test_ct_mod_05_expiracao_de_codigo_de_recuperacao(self):
        """CT-MOD-05: Código emitido há mais de 15 minutos deve ser inválido (RF03)."""
        usuario = Usuario.objects.create_user(**self.usuario_data)
        codigo = CodigoRecuperacao.objects.create(
            usuario=usuario,
            codigo='654321',
            expira_em=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(codigo.is_valido())

    def test_ct_mod_06_consumo_unico_de_codigo(self):
        """CT-MOD-06: Código consumido deve ser considerado inválido para reutilização (RF03)."""
        usuario = Usuario.objects.create_user(**self.usuario_data)
        codigo = CodigoRecuperacao.objects.create(
            usuario=usuario,
            codigo='123456',
            expira_em=timezone.now() + timedelta(minutes=15),
        )
        self.assertTrue(codigo.is_valido())
        codigo.marcar_como_usado()
        self.assertTrue(codigo.utilizado)
        self.assertFalse(codigo.is_valido())


class TestUsuariosForms(TestCase):
    """Bateria de testes unitários da camada de formulários (CT-FRM-01 a CT-FRM-05)."""

    def setUp(self):
        self.cpf_valido = '52998224725'

    def test_ct_frm_01_validar_cpf_com_digitos_invalidos(self):
        """CT-FRM-01: Formulário deve rejeitar CPF com dígito verificador incorreto."""
        dados = {
            'nome_completo': 'Carlos Drumond',
            'email': 'carlos@universidade.edu.br',
            'cpf': '12345678900',  # DV inválido
            'data_nascimento': '2000-01-01',
            'telefone': '(71) 99999-8888',
            'password1': 'SenhaComplexa123',
            'password2': 'SenhaComplexa123',
        }
        form = CadastroUsuarioForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('cpf', form.errors)

    def test_ct_frm_02_rejeitar_senhas_divergentes(self):
        """CT-FRM-02: Formulário de cadastro deve rejeitar confirmação de senha divergente."""
        dados = {
            'nome_completo': 'Carlos Drumond',
            'email': 'carlos@universidade.edu.br',
            'cpf': self.cpf_valido,
            'data_nascimento': '2000-01-01',
            'telefone': '(71) 99999-8888',
            'password1': 'SenhaUm12345',
            'password2': 'SenhaDois12345',
        }
        form = CadastroUsuarioForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_ct_frm_03_aceitar_login_com_formato_de_email(self):
        """CT-FRM-03: Formulário de login aceita e-mail como identificador."""
        form = AutenticacaoForm(data={'identificador': 'usuario@teste.com', 'password': 'qualquer_senha'})
        self.assertTrue(form.is_valid())

    def test_ct_frm_04_aceitar_login_com_formato_de_cpf(self):
        """CT-FRM-04: Formulário de login aceita CPF como identificador."""
        form = AutenticacaoForm(data={'identificador': self.cpf_valido, 'password': 'qualquer_senha'})
        self.assertTrue(form.is_valid())

    def test_ct_frm_05_validar_arquivos_no_perfil_organizador(self):
        """CT-FRM-05: Rejeitar upload de extensões não permitidas no perfil de organizador."""
        arquivo_invalido = SimpleUploadedFile('script.exe', b'conteudo_binario', content_type='application/x-msdownload')
        form = PerfilOrganizadorForm(
            data={'bio_do_organizador': 'Bio teste'},
            files={'banner': arquivo_invalido},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('banner', form.errors)


class TestUsuariosServices(TestCase):
    """Bateria de testes unitários da camada de serviços (CT-SRV-01 a CT-SRV-05)."""

    def setUp(self):
        self.cpf_valido = '52998224725'
        self.usuario = UsuarioService.cadastrar_usuario(
            nome_completo='Luciano de Souza',
            email='luciano.souza@universidade.edu.br',
            cpf=self.cpf_valido,
            data_nascimento=date(1990, 5, 20),
            telefone='(71) 98765-4321',
            password='SenhaSegura@123',
        )

    def test_ct_srv_01_geracao_e_despacho_de_codigo(self):
        """CT-SRV-01: Geração e despacho de código numérico de 6 dígitos via e-mail."""
        sucesso = UsuarioService.gerar_codigo_recuperacao(self.usuario.email)
        self.assertTrue(sucesso)
        codigo = CodigoRecuperacao.objects.filter(usuario=self.usuario, utilizado=False).first()
        self.assertIsNotNone(codigo)
        self.assertEqual(len(codigo.codigo), 6)
        self.assertTrue(codigo.is_valido())

    def test_ct_srv_02_solicitacao_para_email_inexistente(self):
        """CT-SRV-02: Solicitação para e-mail não cadastrado retorna resposta neutra sem exceções."""
        sucesso = UsuarioService.gerar_codigo_recuperacao('inexistente@universidade.edu.br')
        self.assertTrue(sucesso)
        # Nenhum código deve ter sido emitido
        self.assertEqual(CodigoRecuperacao.objects.count(), 0)

    def test_ct_srv_03_redefinicao_bem_sucedida_de_senha(self):
        """CT-SRV-03: Redefinição de senha com código válido atualiza credencial e consome código."""
        UsuarioService.gerar_codigo_recuperacao(self.usuario.email)
        codigo_obj = CodigoRecuperacao.objects.get(usuario=self.usuario, utilizado=False)

        nova_senha = 'NovaSenhaSegura@2026'
        sucesso = UsuarioService.redefinir_senha_com_codigo(
            email=self.usuario.email,
            codigo=codigo_obj.codigo,
            nova_senha=nova_senha,
        )
        self.assertTrue(sucesso)

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(nova_senha))
        codigo_obj.refresh_from_db()
        self.assertTrue(codigo_obj.utilizado)

    def test_ct_srv_04_verificacao_de_papel_em_evento(self):
        """CT-SRV-04: Verificar que usuário possui papel concedido em determinado evento (RN03, RN05)."""
        UsuarioService.atribuir_papel_evento(
            usuario_ou_id=self.usuario,
            evento_id=101,
            papel=Papel.AUTOR,
        )
        self.assertTrue(UsuarioService.verificar_papel_evento(self.usuario, 101, Papel.AUTOR))
        self.assertFalse(UsuarioService.verificar_papel_evento(self.usuario, 101, Papel.AVALIADOR))

    def test_ct_srv_05_isolamento_de_papel_entre_eventos(self):
        """CT-SRV-05: Papéis contextuais devem ser rigorosamente isolados por evento (RN03)."""
        # Luciano é AUTOR no evento 101
        UsuarioService.atribuir_papel_evento(self.usuario, evento_id=101, papel=Papel.AUTOR)

        # No evento 202, Luciano NÃO é autor
        self.assertFalse(UsuarioService.verificar_papel_evento(self.usuario, evento_id=202, papel=Papel.AUTOR))

    def test_obter_dados_cadastrais_rn06(self):
        """Validação do contrato de compartilhamento de dados cadastrais (RN06)."""
        dados = UsuarioService.obter_dados_cadastrais(self.usuario.id)
        self.assertIsNotNone(dados)
        self.assertEqual(dados['nome_completo'], self.usuario.nome_completo)
        self.assertEqual(dados['email'], self.usuario.email)
        self.assertEqual(dados['cpf_limpo'], self.usuario.cpf)
        self.assertEqual(dados['telefone'], self.usuario.telefone)

    def test_qualificacao_organizador_rn04(self):
        """Validação do fluxo de qualificação para Organizador de eventos (RN04)."""
        self.assertFalse(self.usuario.is_organizador())
        perfil = UsuarioService.atualizar_perfil_organizador(
            usuario=self.usuario,
            bio_do_organizador='Professor coordenador do laboratório.',
            homologado=True,
        )
        self.assertTrue(perfil.homologado)
        self.assertTrue(self.usuario.is_organizador())
        self.assertTrue(UsuarioService.is_organizador_homologado(self.usuario.id))


class TestUsuariosViews(TestCase):
    """Bateria de testes de integração da camada de views e rotas HTTP (CT-VIW-01 a CT-VIW-06)."""

    def setUp(self):
        self.client = Client()
        self.cpf_valido = '52998224725'
        self.senha_padrao = 'SenhaForte123@'
        self.usuario = Usuario.objects.create_user(
            nome_completo='Letícia Vitorino',
            email='leticia.vitorino@universidade.edu.br',
            cpf=self.cpf_valido,
            data_nascimento=date(1998, 8, 15),
            telefone='(71) 97777-2222',
            password=self.senha_padrao,
        )

    def test_ct_viw_01_acesso_get_tela_cadastro(self):
        """CT-VIW-01: Acesso GET à tela de cadastro retorna status 200."""
        response = self.client.get(reverse('usuarios:cadastro'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/cadastro.html')

    def test_ct_viw_02_submissao_post_valida_cadastro(self):
        """CT-VIW-02: Submissão válida de cadastro redireciona para login."""
        novo_cpf = '11144477735'
        dados = {
            'nome_completo': 'Novo Participante',
            'email': 'novo.participante@universidade.edu.br',
            'cpf': novo_cpf,
            'data_nascimento': '2001-10-10',
            'telefone': '(71) 99111-2222',
            'password1': 'NovaSenhaSegura@123',
            'password2': 'NovaSenhaSegura@123',
        }
        response = self.client.post(reverse('usuarios:cadastro'), data=dados)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('usuarios:login'))
        self.assertTrue(Usuario.objects.filter(email=dados['email']).exists())

    def test_ct_viw_03_login_com_credenciais_validas_email_e_cpf(self):
        """CT-VIW-03: Login com sucesso tanto informando e-mail quanto CPF (RF02)."""
        # 1. Login por E-mail
        response_email = self.client.post(
            reverse('usuarios:login'),
            data={'identificador': self.usuario.email, 'password': self.senha_padrao},
        )
        self.assertEqual(response_email.status_code, 302)
        self.assertRedirects(response_email, reverse('usuarios:perfil'))
        self.client.logout()

        # 2. Login por CPF
        response_cpf = self.client.post(
            reverse('usuarios:login'),
            data={'identificador': self.usuario.cpf_formatado, 'password': self.senha_padrao},
        )
        self.assertEqual(response_cpf.status_code, 302)
        self.assertRedirects(response_cpf, reverse('usuarios:perfil'))

    def test_ct_viw_04_login_com_credenciais_invalidas(self):
        """CT-VIW-04: Login com senha incorreta mantém na página e exibe mensagem de erro."""
        response = self.client.post(
            reverse('usuarios:login'),
            data={'identificador': self.usuario.email, 'password': 'SenhaErrada123'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/login.html')

    def test_ct_viw_05_acesso_anonimo_a_pagina_protegida(self):
        """CT-VIW-05: Usuário não autenticado tentando acessar perfil é redirecionado ao login."""
        response = self.client.get(reverse('usuarios:perfil'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('usuarios:login'), response.url)

    def test_ct_viw_06_logout_de_usuario_autenticado(self):
        """CT-VIW-06: Logout destrói a sessão e redireciona para a tela de login."""
        self.client.login(username=self.usuario.email, password=self.senha_padrao)
        response = self.client.get(reverse('usuarios:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('usuarios:login'))


class TestUsuariosPermissionsAndDecorators(TestCase):
    """Testes dos decorators de segurança @organizador_required e @role_required."""

    def setUp(self):
        self.factory = RequestFactory()
        self.cpf_valido = '52998224725'
        self.usuario = Usuario.objects.create_user(
            nome_completo='Membro Teste',
            email='membro@universidade.edu.br',
            cpf=self.cpf_valido,
            data_nascimento=date(1992, 3, 10),
            telefone='(71) 98888-3333',
            password='SenhaSegura@123',
        )

    def test_decorator_organizador_required_bloqueia_participante(self):
        """Participante comum sem homologação deve ser redirecionado de view restrita."""

        @organizador_required
        def view_exclusiva_organizador(request):
            return HttpResponse('OK Organizador')

        request = self.factory.get('/eventos/criar/')
        request.user = self.usuario
        # Mocking session and messages
        request._messages = []

        response = view_exclusiva_organizador(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('usuarios:perfil'))

    def test_decorator_organizador_required_permite_homologado(self):
        """Organizador homologado deve acessar com sucesso a view protegida."""
        PerfilOrganizador.objects.create(usuario=self.usuario, homologado=True)

        @organizador_required
        def view_exclusiva_organizador(request):
            return HttpResponse('OK Organizador')

        request = self.factory.get('/eventos/criar/')
        request.user = self.usuario
        response = view_exclusiva_organizador(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'OK Organizador')

    def test_decorator_role_required_bloqueia_sem_papel_contextual(self):
        """Usuário sem o papel de AUTOR no evento deve receber PermissionDenied."""

        @role_required(papel_esperado=Papel.AUTOR, evento_param='evento_id')
        def view_submissao(request, evento_id):
            return HttpResponse('Submissão Autorizada')

        request = self.factory.get('/eventos/10/submeter/')
        request.user = self.usuario

        with self.assertRaises(PermissionDenied):
            view_submissao(request, evento_id=10)

    def test_decorator_role_required_permite_com_papel_contextual(self):
        """Usuário com o papel de AUTOR ativo no evento acessa com sucesso."""
        UsuarioService.atribuir_papel_evento(self.usuario, evento_id=10, papel=Papel.AUTOR)

        @role_required(papel_esperado=Papel.AUTOR, evento_param='evento_id')
        def view_submissao(request, evento_id):
            return HttpResponse('Submissão Autorizada')

        request = self.factory.get('/eventos/10/submeter/')
        request.user = self.usuario
        response = view_submissao(request, evento_id=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Submissão Autorizada')


class TestUsuariosAPI(TestCase):
    """Bateria de testes de integração da API REST (DRF)."""

    def setUp(self):
        self.client = APIClient()
        self.cpf_valido_1 = '52998224725'
        self.cpf_valido_2 = '11144477735'
        self.cpf_valido_3 = '78508492080'

        self.user_1 = Usuario.objects.create_user(
            nome_completo='Usuario Um',
            email='user1@universidade.edu.br',
            cpf=self.cpf_valido_1,
            data_nascimento=date(1991, 1, 1),
            telefone='(71) 91111-1111',
            password='SenhaValida1@',
        )
        self.user_2 = Usuario.objects.create_user(
            nome_completo='Usuario Dois',
            email='user2@universidade.edu.br',
            cpf=self.cpf_valido_2,
            data_nascimento=date(1992, 2, 2),
            telefone='(71) 92222-2222',
            password='SenhaValida2@',
        )
        self.admin_user = Usuario.objects.create_superuser(
            nome_completo='Admin User',
            email='admin@universidade.edu.br',
            cpf=self.cpf_valido_3,
            data_nascimento=date(1985, 5, 5),
            telefone='(71) 93333-3333',
            password='SenhaValidaAdmin1@',
        )

    def test_listar_usuarios_anonimo_retorna_401(self):
        """Acesso anônimo à listagem de usuários deve ser rejeitado com 401 ou 403."""
        response = self.client.get('/api/sgie/v1/usuarios/')
        self.assertIn(response.status_code, [401, 403])

    def test_cadastro_anonimo_via_api_retorna_201(self):
        """Cadastro de novo usuário anônimo via POST /api/sgie/v1/usuarios/ é permitido."""
        # CPF válido calculado: 10000000019
        payload = {
            'nome_completo': 'Novo Usuario API',
            'email': 'novo.api@universidade.edu.br',
            'cpf': '10000000019',
            'data_nascimento': '1995-10-10',
            'telefone': '(71) 99999-0000',
            'password': 'SenhaSuperForte@2026',
        }
        response = self.client.post('/api/sgie/v1/usuarios/', payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Usuario.objects.filter(email='novo.api@universidade.edu.br').exists())

    def test_listar_usuarios_autenticado_retorna_200(self):
        """Usuário autenticado pode consultar listagem."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get('/api/sgie/v1/usuarios/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 2)

    def test_atualizar_proprio_usuario_retorna_200(self):
        """Usuário autenticado pode atualizar seu próprio perfil."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch(f'/api/sgie/v1/usuarios/{self.user_1.id}/', {'nome_completo': 'Nome Alterado'})
        self.assertEqual(response.status_code, 200)
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.nome_completo, 'Nome Alterado')

    def test_atualizar_usuario_de_terceiro_retorna_403(self):
        """Usuário autenticado NÃO pode atualizar cadastro de outro usuário (IsSelfOrAdmin)."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch(f'/api/sgie/v1/usuarios/{self.user_2.id}/', {'nome_completo': 'Hack Alterado'})
        self.assertEqual(response.status_code, 403)
        self.user_2.refresh_from_db()
        self.assertNotEqual(self.user_2.nome_completo, 'Hack Alterado')

    def test_deletar_usuario_por_nao_staff_retorna_403(self):
        """Tentativa de deletar conta por usuário comum retorna 403 Forbidden."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(f'/api/sgie/v1/usuarios/{self.user_1.id}/')
        self.assertEqual(response.status_code, 403)

    def test_deletar_usuario_por_admin_retorna_204(self):
        """Administrador tem permissão para deletar conta."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/sgie/v1/usuarios/{self.user_2.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Usuario.objects.filter(id=self.user_2.id).exists())

    def test_perfil_organizador_api_list_and_create(self):
        """Criação e consulta autenticada de perfil de organizador."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post('/api/sgie/v1/organizadores/', {'bio_do_organizador': 'Bio via API'})
        self.assertEqual(response.status_code, 201)

        response_list = self.client.get('/api/sgie/v1/organizadores/')
        self.assertEqual(response_list.status_code, 200)

    def test_papel_contextual_api_e_filtros(self):
        """Consulta e filtro de papéis contextuais."""
        self.client.force_authenticate(user=self.user_1)
        UsuarioService.atribuir_papel_evento(self.user_1, evento_id=50, papel=Papel.AVALIADOR)

        response = self.client.get('/api/sgie/v1/papeis-contextuais/?evento_id=50')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['papel'], Papel.AVALIADOR)

    def test_dados_cadastrais_endpoint_rn06(self):
        """Consulta do contrato de dados cadastrais para integrações."""
        self.client.force_authenticate(user=self.user_1)
        response_me = self.client.get('/api/sgie/v1/usuarios/dados-cadastrais/')
        self.assertEqual(response_me.status_code, 200)
        self.assertEqual(response_me.data['email'], self.user_1.email)

        response_other = self.client.get(f'/api/sgie/v1/usuarios/dados-cadastrais/{self.user_2.id}/')
        self.assertEqual(response_other.status_code, 200)
        self.assertEqual(response_other.data['email'], self.user_2.email)


class TestDRFPermissions(TestCase):
    """Testes unitários das classes de permissão do DRF."""

    def setUp(self):
        self.factory = RequestFactory()
        self.usuario = Usuario.objects.create_user(
            nome_completo='Perm Test',
            email='perm@universidade.edu.br',
            cpf='52998224725',
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 98888-0000',
            password='SenhaValida@1',
        )

    def test_is_organizador_permission(self):
        perm = IsOrganizadorPermission()
        request = self.factory.get('/')
        request.user = self.usuario
        self.assertFalse(perm.has_permission(request, None))

        PerfilOrganizador.objects.create(usuario=self.usuario, homologado=True)
        self.assertTrue(perm.has_permission(request, None))

    def test_has_event_role_permission(self):
        perm = HasEventRolePermission()
        request = self.factory.get('/?evento_id=99')
        request.user = self.usuario

        class DummyView:
            required_role = Papel.AVALIADOR
            kwargs = {}

        view = DummyView()
        self.assertFalse(perm.has_permission(request, view))

        UsuarioService.atribuir_papel_evento(self.usuario, evento_id=99, papel=Papel.AVALIADOR)
        self.assertTrue(perm.has_permission(request, view))
