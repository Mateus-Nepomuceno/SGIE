from datetime import date, timedelta
from io import BytesIO

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .admin import UsuarioCreationForm
from .models import CodigoRecuperacao, Papel, PapelContextual, PerfilOrganizador, Usuario
from .permissions import (
    HasEventRolePermission,
    IsOrganizadorPermission,
    IsPapelContextualManagerOrReadOnly,
    IsSelfOrAdmin,
    organizador_required,
    role_required,
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    PerfilOrganizadorSerializer,
    RedefinirSenhaSerializer,
    SolicitarRecuperacaoSenhaSerializer,
    UsuarioCadastroSerializer,
    UsuarioUpdateSerializer,
)
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


class TestUsuariosSerializers(TestCase):
    """Bateria de testes unitários da camada de serializers do DRF (CT-SER-01 a CT-SER-06)."""

    def setUp(self):
        self.cpf_valido = '52998224725'
        self.usuario = Usuario.objects.create_user(
            nome_completo='Carlos Drumond',
            email='carlos@universidade.edu.br',
            cpf=self.cpf_valido,
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 99999-8888',
            password='SenhaComplexa123@',
        )

    def test_ct_ser_01_validar_cpf_invalido(self):
        """CT-SER-01: Serializer de cadastro rejeita CPF com dígito incorreto."""
        dados = {
            'nome_completo': 'Novo Participante',
            'email': 'novo@universidade.edu.br',
            'cpf': '12345678900',
            'data_nascimento': '2000-01-01',
            'telefone': '(71) 99999-8888',
            'password': 'SenhaComplexa123@',
            'confirmacao_senha': 'SenhaComplexa123@',
        }
        serializer = UsuarioCadastroSerializer(data=dados)
        self.assertFalse(serializer.is_valid())
        self.assertIn('cpf', serializer.errors)

    def test_ct_ser_02_rejeitar_senhas_divergentes(self):
        """CT-SER-02: Serializer de cadastro rejeita confirmação de senha divergente."""
        dados = {
            'nome_completo': 'Novo Participante',
            'email': 'novo@universidade.edu.br',
            'cpf': '11144477735',
            'data_nascimento': '2000-01-01',
            'telefone': '(71) 99999-8888',
            'password': 'SenhaUm12345@',
            'confirmacao_senha': 'SenhaDois12345@',
        }
        serializer = UsuarioCadastroSerializer(data=dados)
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirmacao_senha', serializer.errors)

    def test_ct_ser_03_login_com_email_e_cpf_no_serializer_jwt(self):
        """CT-SER-03: Serializer JWT valida login tanto por e-mail quanto por CPF."""
        # 1. Por email
        serializer_email = CustomTokenObtainPairSerializer(data={'identificador': self.usuario.email, 'password': 'SenhaComplexa123@'})
        self.assertTrue(serializer_email.is_valid(), serializer_email.errors)
        data = serializer_email.validated_data
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertEqual(data['usuario']['id'], self.usuario.id)

        # 2. Por CPF
        serializer_cpf = CustomTokenObtainPairSerializer(data={'identificador': self.usuario.cpf_formatado, 'password': 'SenhaComplexa123@'})
        self.assertTrue(serializer_cpf.is_valid(), serializer_cpf.errors)

    def test_ct_ser_04_validar_arquivos_no_perfil_organizador(self):
        """CT-SER-04: Serializer de organizador rejeita extensão não permitida."""
        arquivo_invalido = SimpleUploadedFile('script.exe', b'conteudo_binario', content_type='application/x-msdownload')
        serializer = PerfilOrganizadorSerializer(data={'bio_do_organizador': 'Bio teste', 'banner': arquivo_invalido})
        self.assertFalse(serializer.is_valid())
        self.assertIn('banner', serializer.errors)

    def test_ct_ser_05_redefinir_senha_serializer_validacoes(self):
        """CT-SER-05: Validação do serializer de redefinição de senha."""
        UsuarioService.gerar_codigo_recuperacao(self.usuario.email)
        codigo_obj = CodigoRecuperacao.objects.get(usuario=self.usuario, utilizado=False)

        # Senhas divergentes
        s_divergente = RedefinirSenhaSerializer(
            data={
                'email': self.usuario.email,
                'codigo': codigo_obj.codigo,
                'nova_senha': 'NovaSenhaSegura123@',
                'confirmacao_senha': 'OutraSenhaSegura123@',
            }
        )
        self.assertFalse(s_divergente.is_valid())
        self.assertIn('confirmacao_senha', s_divergente.errors)

        # Sucesso
        s_valido = RedefinirSenhaSerializer(
            data={
                'email': self.usuario.email,
                'codigo': codigo_obj.codigo,
                'nova_senha': 'NovaSenhaSegura123@',
                'confirmacao_senha': 'NovaSenhaSegura123@',
            }
        )
        self.assertTrue(s_valido.is_valid(), s_valido.errors)
        s_valido.save()
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NovaSenhaSegura123@'))

    def test_ct_ser_06_usuario_update_serializer(self):
        """CT-SER-06: Validação de atualização de dados cadastrais."""
        serializer = UsuarioUpdateSerializer(
            instance=self.usuario,
            data={'nome_completo': 'AB', 'telefone': '123', 'data_nascimento': '1990-01-01'},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('nome_completo', serializer.errors)
        self.assertIn('telefone', serializer.errors)

    def test_ct_ser_07_solicitar_recuperacao_senha_serializer(self):
        """CT-SER-07: Serializer de solicitação de recuperação de senha por e-mail."""
        serializer = SolicitarRecuperacaoSenhaSerializer(data={'email': self.usuario.email})
        self.assertTrue(serializer.is_valid())
        email_gerado = serializer.save()
        self.assertEqual(email_gerado, self.usuario.email)


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
        UsuarioService.atribuir_papel_evento(usuario_ou_id=self.usuario, evento_id=101, papel=Papel.AUTOR)
        self.assertTrue(UsuarioService.verificar_papel_evento(self.usuario, 101, Papel.AUTOR))
        self.assertFalse(UsuarioService.verificar_papel_evento(self.usuario, 101, Papel.AVALIADOR))

    def test_ct_srv_05_isolamento_de_papel_entre_eventos(self):
        """CT-SRV-05: Papéis contextuais devem ser rigorosamente isolados por evento (RN03)."""
        UsuarioService.atribuir_papel_evento(self.usuario, evento_id=101, papel=Papel.AUTOR)
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
        """Participante comum sem homologação recebe PermissionDenied em view restrita."""

        @organizador_required
        def view_exclusiva_organizador(request):
            return HttpResponse('OK Organizador')

        request = self.factory.get('/eventos/criar/')
        request.user = self.usuario

        with self.assertRaises(PermissionDenied):
            view_exclusiva_organizador(request)

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
    """Bateria de testes de integração da API REST (DRF) e Autenticação JWT."""

    def setUp(self):
        self.client = APIClient()
        self.cpf_valido_1 = '52998224725'
        self.cpf_valido_2 = '11144477735'
        self.cpf_valido_3 = '22233344405'
        self.senha_padrao = 'SenhaValida1@2026'

        self.user_1 = Usuario.objects.create_user(
            nome_completo='Usuario Um',
            email='user1@universidade.edu.br',
            cpf=self.cpf_valido_1,
            data_nascimento=date(1991, 1, 1),
            telefone='(71) 91111-1111',
            password=self.senha_padrao,
        )
        self.user_2 = Usuario.objects.create_user(
            nome_completo='Usuario Dois',
            email='user2@universidade.edu.br',
            cpf=self.cpf_valido_2,
            data_nascimento=date(1992, 2, 2),
            telefone='(71) 92222-2222',
            password=self.senha_padrao,
        )
        self.admin_user = Usuario.objects.create_superuser(
            nome_completo='Admin User',
            email='admin@universidade.edu.br',
            cpf=self.cpf_valido_3,
            data_nascimento=date(1985, 5, 5),
            telefone='(71) 93333-3333',
            password=self.senha_padrao,
        )

    def test_jwt_obter_token_por_email(self):
        """Login com obtenção de par de tokens JWT via e-mail."""
        payload = {'identificador': self.user_1.email, 'password': self.senha_padrao}
        response = self.client.post('/api/sgie/v1/auth/token/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['usuario']['email'], self.user_1.email)

    def test_jwt_obter_token_por_cpf(self):
        """Login com obtenção de tokens JWT via CPF formatado ou numérico."""
        payload = {'identificador': self.user_1.cpf_formatado, 'password': self.senha_padrao}
        response = self.client.post('/api/sgie/v1/auth/token/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_jwt_login_com_senha_invalida(self):
        """Tentativa de login com senha incorreta retorna 400 Bad Request."""
        payload = {'identificador': self.user_1.email, 'password': 'SenhaIncorreta!'}
        response = self.client.post('/api/sgie/v1/auth/token/', payload)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_jwt_token_refresh(self):
        """Renovação de access token via endpoint de refresh com refresh token válido."""
        refresh = RefreshToken.for_user(self.user_1)
        response = self.client.post('/api/sgie/v1/auth/token/refresh/', {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_jwt_autenticacao_com_bearer_token(self):
        """Acesso a endpoint protegido utilizando cabeçalho Authorization: Bearer."""
        refresh = RefreshToken.for_user(self.user_1)
        access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/sgie/v1/usuarios/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_1.email)

    def test_endpoint_recuperacao_e_redefinicao_de_senha(self):
        """Fluxo completo de recuperação e redefinição de senha via endpoints REST."""
        # 1. Solicitar código
        response_solicitar = self.client.post('/api/sgie/v1/auth/recuperar-senha/', {'email': self.user_1.email})
        self.assertEqual(response_solicitar.status_code, status.HTTP_200_OK)

        codigo_obj = CodigoRecuperacao.objects.get(usuario=self.user_1, utilizado=False)
        self.assertIsNotNone(codigo_obj)

        # 2. Redefinir com código
        nova_senha = 'NovaSenhaSuperForte@2026'
        response_redefinir = self.client.post(
            '/api/sgie/v1/auth/redefinir-senha/',
            {'email': self.user_1.email, 'codigo': codigo_obj.codigo, 'nova_senha': nova_senha, 'confirmacao_senha': nova_senha},
        )
        self.assertEqual(response_redefinir.status_code, status.HTTP_200_OK)

        # 3. Testar novo login com a nova senha
        response_login = self.client.post(
            '/api/sgie/v1/auth/token/',
            {'identificador': self.user_1.email, 'password': nova_senha},
        )
        self.assertEqual(response_login.status_code, status.HTTP_200_OK)

    def test_endpoint_usuario_me_patch(self):
        """Atualização de dados cadastrais através de /usuarios/me/."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch('/api/sgie/v1/usuarios/me/', {'nome_completo': 'Nome Alterado Via Me'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.nome_completo, 'Nome Alterado Via Me')

    def test_endpoint_organizadores_me(self):
        """Consulta e atualização do perfil de organizador do próprio usuário através de /organizadores/me/."""
        self.client.force_authenticate(user=self.user_1)
        # Inicialmente 404
        r_get = self.client.get('/api/sgie/v1/organizadores/me/')
        self.assertEqual(r_get.status_code, status.HTTP_404_NOT_FOUND)

        # Criar perfil via me
        r_post = self.client.post('/api/sgie/v1/organizadores/me/', {'bio_do_organizador': 'Bio do organizador via me'})
        self.assertIn(r_post.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # Agora GET retorna 200
        r_get2 = self.client.get('/api/sgie/v1/organizadores/me/')
        self.assertEqual(r_get2.status_code, status.HTTP_200_OK)
        self.assertEqual(r_get2.data['bio_do_organizador'], 'Bio do organizador via me')

    def test_listar_usuarios_anonimo_retorna_401(self):
        """Acesso anônimo à listagem de usuários deve ser rejeitado com 401 ou 403."""
        response = self.client.get('/api/sgie/v1/usuarios/')
        self.assertIn(response.status_code, [401, 403])

    def test_cadastro_anonimo_via_api_retorna_201(self):
        """Cadastro de novo usuário anônimo via POST /api/sgie/v1/usuarios/ é permitido."""
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

    def test_is_self_or_admin_permission(self):
        perm = IsSelfOrAdmin()
        request = self.factory.get('/')
        request.user = self.usuario

        class DummyView:
            action = 'retrieve'

        view = DummyView()
        self.assertTrue(perm.has_permission(request, view))
        self.assertTrue(perm.has_object_permission(request, view, self.usuario))

        outro = Usuario.objects.create_user(
            nome_completo='Outro Perm',
            email='outro_p@universidade.edu.br',
            cpf='11144477735',
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 98888-0001',
            password='SenhaValida@1',
        )
        self.assertFalse(perm.has_object_permission(request, view, outro))

    def test_is_papel_contextual_manager_or_read_only(self):
        perm = IsPapelContextualManagerOrReadOnly()
        request_get = self.factory.get('/')
        request_get.user = self.usuario

        class DummyView:
            action = 'list'

        view = DummyView()
        self.assertTrue(perm.has_permission(request_get, view))
        request_del = self.factory.delete('/')
        request_del.user = self.usuario
        view.action = 'destroy'
        self.assertFalse(perm.has_permission(request_del, view))


class TestCorrecoesEValidacoesAvancadas(TestCase):
    """Bateria de testes para as correções e mitigações de segurança aplicadas."""

    def setUp(self):
        self.client = APIClient()
        self.factory = RequestFactory()
        self.cpf_valido_1 = '52998224725'
        self.cpf_valido_2 = '11144477735'
        self.senha_padrao = 'SenhaForteSGIE@2026'

        self.user_1 = Usuario.objects.create_user(
            nome_completo='Alice Silva',
            email='alice@universidade.edu.br',
            cpf=self.cpf_valido_1,
            data_nascimento=date(1995, 5, 10),
            telefone='(71) 98888-1111',
            password=self.senha_padrao,
        )
        self.user_2 = Usuario.objects.create_user(
            nome_completo='Bob Santos',
            email='bob@universidade.edu.br',
            cpf=self.cpf_valido_2,
            data_nascimento=date(1996, 6, 20),
            telefone='(71) 97777-2222',
            password=self.senha_padrao,
        )

    def test_tentativas_recuperacao_bloqueio_apos_tres_falhas(self):
        """RF03: Código de recuperação é invalidado após 3 tentativas incorretas."""
        UsuarioService.gerar_codigo_recuperacao(self.user_1.email)
        codigo_obj = CodigoRecuperacao.objects.get(usuario=self.user_1, utilizado=False)

        # 1ª tentativa com código errado
        with self.assertRaises(ValidationError):
            UsuarioService.redefinir_senha_com_codigo(self.user_1.email, '000000', 'NovaSenha123@')
        codigo_obj.refresh_from_db()
        self.assertEqual(codigo_obj.tentativas, 1)
        self.assertTrue(codigo_obj.is_valido())

        # 2ª tentativa com código errado
        with self.assertRaises(ValidationError):
            UsuarioService.redefinir_senha_com_codigo(self.user_1.email, '000001', 'NovaSenha123@')
        codigo_obj.refresh_from_db()
        self.assertEqual(codigo_obj.tentativas, 2)

        # 3ª tentativa com código errado -> bloqueia o código
        with self.assertRaises(ValidationError):
            UsuarioService.redefinir_senha_com_codigo(self.user_1.email, '000002', 'NovaSenha123@')
        codigo_obj.refresh_from_db()
        self.assertEqual(codigo_obj.tentativas, 3)
        self.assertTrue(codigo_obj.utilizado)
        self.assertFalse(codigo_obj.is_valido())

        # Mesmo com código correto, tentativa subsequente deve falhar
        with self.assertRaises(ValidationError):
            UsuarioService.redefinir_senha_com_codigo(self.user_1.email, codigo_obj.codigo, 'NovaSenha123@')

    def test_last_login_atualizado_apos_jwt_login(self):
        """Metadado last_login é atualizado no login JWT quando UPDATE_LAST_LOGIN está habilitado."""
        self.assertIsNone(self.user_1.last_login)
        response = self.client.post(
            '/api/sgie/v1/auth/token/',
            {'identificador': self.user_1.email, 'password': self.senha_padrao},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_1.refresh_from_db()
        self.assertIsNotNone(self.user_1.last_login)

    def test_idor_perfil_organizador_bloqueado(self):
        """PerfilOrganizadorViewSet impede IDOR: usuário não altera perfil de outro usuário."""
        perfil_1 = PerfilOrganizador.objects.create(usuario=self.user_1, bio_do_organizador='Bio Alice')
        self.client.force_authenticate(user=self.user_2)

        # Tentativa de alteração por terceiro
        response = self.client.patch(
            f'/api/sgie/v1/organizadores/{perfil_1.id}/',
            {'bio_do_organizador': 'Hacked by Bob'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        perfil_1.refresh_from_db()
        self.assertEqual(perfil_1.bio_do_organizador, 'Bio Alice')

        # Dono pode alterar
        self.client.force_authenticate(user=self.user_1)
        response_owner = self.client.patch(
            f'/api/sgie/v1/organizadores/{perfil_1.id}/',
            {'bio_do_organizador': 'Bio Atualizada Alice'},
        )
        self.assertEqual(response_owner.status_code, status.HTTP_200_OK)
        perfil_1.refresh_from_db()
        self.assertEqual(perfil_1.bio_do_organizador, 'Bio Atualizada Alice')

    def test_duplicidade_perfil_organizador_retorna_400(self):
        """Criação duplicada de perfil de organizador para o mesmo usuário retorna 400 sem erro 500."""
        PerfilOrganizador.objects.create(usuario=self.user_1)
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post('/api/sgie/v1/organizadores/', {'bio_do_organizador': 'Segunda Bio'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papel_contextual_privilegio_escalation_bloqueado(self):
        """Participante comum não pode se auto-atribuir papel de ORGANIZADOR ou AVALIADOR."""
        self.client.force_authenticate(user=self.user_1)
        r = self.client.post('/api/sgie/v1/papeis-contextuais/', {'usuario': self.user_1.id, 'evento_id': 100, 'papel': Papel.ORGANIZADOR})
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

        # Participante comum não pode atribuir papel a outro usuário
        r_other = self.client.post('/api/sgie/v1/papeis-contextuais/', {'usuario': self.user_2.id, 'evento_id': 100, 'papel': Papel.PARTICIPANTE})
        self.assertEqual(r_other.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papel_contextual_auto_inscricao_participante_permitida(self):
        """Participante comum pode se inscrever como PARTICIPANTE em evento (RF06)."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post('/api/sgie/v1/papeis-contextuais/', {'usuario': self.user_1.id, 'evento_id': 200, 'papel': Papel.PARTICIPANTE})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PapelContextual.objects.filter(usuario=self.user_1, evento_id=200, papel=Papel.PARTICIPANTE).exists())

    def test_dados_cadastrais_uuid_invalido_retorna_404(self):
        """Consulta a dados cadastrais com identificador não-UUID retorna 404 limpo (sem crash 500)."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get('/api/sgie/v1/usuarios/dados-cadastrais/nao-e-um-uuid/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_papeis_contextuais_filtros_invalidos_retornam_lista_vazia(self):
        """Filtros não-numéricos ou não-UUID em papeis contextuais retornam lista vazia sem crash 500."""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get('/api/sgie/v1/papeis-contextuais/?evento_id=invalido')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_usuario_inativo_nao_mantem_privilegios(self):
        """Usuário inativo perde status de organizador e permissões contextuais de evento."""
        self.user_1.is_active = False
        self.user_1.save()
        PerfilOrganizador.objects.create(usuario=self.user_1, homologado=True)
        self.assertFalse(self.user_1.is_organizador())

        UsuarioService.atribuir_papel_evento(self.user_1, evento_id=300, papel=Papel.AUTOR)
        self.assertFalse(self.user_1.has_role(300, Papel.AUTOR))
        self.assertFalse(UsuarioService.verificar_papel_evento(self.user_1, 300, Papel.AUTOR))

    def test_validacao_data_nascimento_futura_rejeitada(self):
        """Serializer de cadastro rejeita data de nascimento futura."""
        dados = {
            'nome_completo': 'Novo Usuario Valido',
            'email': 'futuro@universidade.edu.br',
            'cpf': '22233344405',
            'data_nascimento': (timezone.now().date() + timedelta(days=1)).isoformat(),
            'telefone': '(71) 98888-1111',
            'password': 'SenhaValida@2026',
        }
        serializer = UsuarioCadastroSerializer(data=dados)
        self.assertFalse(serializer.is_valid())
        self.assertIn('data_nascimento', serializer.errors)

    def test_validacao_nome_sem_sobrenome_rejeitado(self):
        """Serializer de cadastro exige nome e sobrenome (mínimo duas palavras)."""
        dados = {
            'nome_completo': 'ApenasNomeSemSobrenome',
            'email': 'sobrenome@universidade.edu.br',
            'cpf': '22233344405',
            'data_nascimento': '1995-01-01',
            'telefone': '(71) 98888-1111',
            'password': 'SenhaValida@2026',
        }
        serializer = UsuarioCadastroSerializer(data=dados)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nome_completo', serializer.errors)

    def test_admin_usuario_creation_form_valido(self):
        """Formulário de criação no Django Admin valida dados e salva usuário com senha criptografada."""
        form = UsuarioCreationForm(
            data={
                'email': 'novo_admin@universidade.edu.br',
                'cpf': '22233344405',
                'nome_completo': 'Admin Teste Dois',
                'data_nascimento': '1990-01-01',
                'telefone': '(71) 98888-1111',
                'password1': 'SenhaValida@2026',
                'password2': 'SenhaValida@2026',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        usuario_criado = form.save()
        self.assertTrue(usuario_criado.check_password('SenhaValida@2026'))

    def test_role_required_com_evento_id_invalido_lanca_permission_denied(self):
        """Decorator role_required lança PermissionDenied em caso de identificador não numérico."""

        @role_required(papel_esperado=Papel.AUTOR, evento_param='evento_id')
        def view_dummy(request, evento_id):
            return HttpResponse('OK')

        request = self.factory.get('/eventos/abc/submeter/')
        request.user = self.user_1

        with self.assertRaises(PermissionDenied):
            view_dummy(request, evento_id='abc')

    def test_cors_preflight_headers(self):
        """API retorna cabeçalhos de CORS adequados para frontends desacoplados."""
        response = self.client.options(
            '/api/sgie/v1/auth/token/',
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), 'http://localhost:3000')
        self.assertEqual(response.headers.get('Access-Control-Allow-Credentials'), 'true')
