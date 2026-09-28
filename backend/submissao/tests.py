from datetime import date, time, timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from eventos.models import CategoriaEvento, Evento, RegraSubmissao, StatusEvento
from usuarios.models import Usuario

from .models import (
    Area,
    Local,
    StatusSubmissao,
    Submissao,
    SubmissaoAutor,
    SubmissaoVersao,
    TipoParticipacaoAutor,
    TipoSubmissao,
    Avaliador
)
from .services import SubmissaoService


def gerar_arquivo_pdf_teste(nome='trabalho.pdf', conteudo=b'%PDF-1.4 teste submissao sgie'):
    """Gera um arquivo PDF em memória para testes de upload."""
    return SimpleUploadedFile(nome, conteudo, content_type='application/pdf')


def gerar_arquivo_invalido_teste(nome='script.sh', conteudo=b'#!/bin/bash\necho hello'):
    """Gera um arquivo com extensão não permitida para testes."""
    return SimpleUploadedFile(nome, conteudo, content_type='text/x-shellscript')


class SubmissaoBaseTestCase(TestCase):
    """Base com dados comuns para testes de submissão acadêmica."""

    def setUp(self):
        self.senha_padrao = 'SenhaForteSGIE@2026'

        # Usuários
        self.autor = Usuario.objects.create_user(
            nome_completo='Dr. Lucas Pesquisador',
            email='lucas.pesquisador@universidade.edu.br',
            cpf='52998224725',
            data_nascimento=date(1990, 5, 10),
            telefone='(71) 98888-1111',
            password=self.senha_padrao,
        )

        self.coautor = Usuario.objects.create_user(
            nome_completo='Dra. Marina Santos',
            email='marina.santos@universidade.edu.br',
            cpf='11144477735',
            data_nascimento=date(1992, 8, 20),
            telefone='(71) 98888-2222',
            password=self.senha_padrao,
        )

        self.organizador = Usuario.objects.create_user(
            nome_completo='Prof. Roberto Organizador',
            email='roberto.organizador@universidade.edu.br',
            cpf='22233344405',
            data_nascimento=date(1980, 2, 15),
            telefone='(71) 98888-3333',
            password=self.senha_padrao,
        )

        self.outro_usuario = Usuario.objects.create_user(
            nome_completo='Outro Aluno',
            email='outro.aluno@universidade.edu.br',
            cpf='33344455516',
            data_nascimento=date(1998, 11, 25),
            telefone='(71) 98888-4444',
            password=self.senha_padrao,
        )

        # Área temática
        self.area_ti = Area.objects.create(
            nome='Inteligência Artificial E Sistemas Inteligentes',
            descricao='Área de pesquisa focada em IA, aprendizado de máquina e visão computacional.',
        )

        self.area_saude = Area.objects.create(
            nome='Biotecnologia E Saúde Integrada',
            descricao='Área focada em aplicações biotecnológicas na saúde.',
        )

        # Evento que aceita submissões com período aberto
        self.evento_aceita = Evento.objects.create(
            usuario_representante=self.organizador,
            nome='Congresso Brasileiro De Inteligencia Artificial 2026',
            descricao='Congresso de ponta em inteligência artificial e suas aplicações.',
            data=timezone.now().date() + timedelta(days=60),
            hora_inicio=time(9, 0),
            hora_fim=time(18, 0),
            local='Auditório Principal',
            capacidade=1000,
            categoria=CategoriaEvento.CONGRESSO,
            status=StatusEvento.PUBLICADO,
        )

        self.regra_aceita = RegraSubmissao.objects.create(
            evento=self.evento_aceita,
            aceita_submissao=True,
            data_hora_inicio=timezone.now() - timedelta(days=5),
            data_hora_fim=timezone.now() + timedelta(days=30),
        )

        # Evento que não aceita submissões
        self.evento_recusa = Evento.objects.create(
            usuario_representante=self.organizador,
            nome='Seminario Interno De Integracao Academica',
            descricao='Seminário fechado apenas para apresentação interna.',
            data=timezone.now().date() + timedelta(days=30),
            hora_inicio=time(14, 0),
            hora_fim=time(17, 0),
            local='Sala 1',
            capacidade=100,
            categoria=CategoriaEvento.SEMINARIO,
            status=StatusEvento.PUBLICADO,
        )

        self.regra_recusa = RegraSubmissao.objects.create(
            evento=self.evento_recusa,
            aceita_submissao=False,
        )

        # Evento sem regra cadastrada
        self.evento_sem_regra = Evento.objects.create(
            usuario_representante=self.organizador,
            nome='Workshop De Metodologia Cientifica',
            descricao='Workshop prático de escrita de artigos.',
            data=timezone.now().date() + timedelta(days=15),
            hora_inicio=time(10, 0),
            hora_fim=time(12, 0),
            local='Laboratório 2',
            capacidade=50,
            categoria=CategoriaEvento.WORKSHOP,
            status=StatusEvento.PUBLICADO,
        )


class TestSubmissaoModels(SubmissaoBaseTestCase):
    """Testes unitários dos modelos do app de submissão."""

    def test_area_str(self):
        self.assertEqual(str(self.area_ti), 'Inteligência Artificial E Sistemas Inteligentes')

    def test_submissao_str_e_properties(self):
        submissao = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Avanços Em Aprendizado Profundo',
            abstract='This paper discusses deep learning advancements.',
            resumo='Resumo em português sobre IA.',
            palavras_chave='IA, Deep Learning, Redes Neurais',
            tipo=TipoSubmissao.ARTIGO,
            status=StatusSubmissao.RASCUNHO,
        )
        self.assertIn('Avanços Em Aprendizado Profundo', str(submissao))
        self.assertTrue(submissao.pode_editar)
        self.assertTrue(submissao.pode_submeter)

    def test_submissao_autor_str(self):
        submissao = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Visão Computacional Aplicada',
            abstract='Computer vision methods and techniques.',
            palavras_chave='Visao, IA',
            status=StatusSubmissao.RASCUNHO,
        )
        autor_sub = SubmissaoAutor.objects.create(
            submissao=submissao,
            usuario=self.autor,
            tipo_participacao=TipoParticipacaoAutor.PRINCIPAL,
            maiór_titulacao='Doutorado',
        )
        self.assertIn('Principal', str(autor_sub))
        self.assertEqual(autor_sub.maiór_titulacao, 'Doutorado')

    def test_submissao_versao_str(self):
        submissao = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Processamento De Linguagem Natural',
            abstract='Natural language processing advances.',
            palavras_chave='NLP, LLM',
            status=StatusSubmissao.RASCUNHO,
        )
        arquivo_pdf = gerar_arquivo_pdf_teste()
        versao = SubmissaoVersao.objects.create(
            submissao=submissao,
            numero_versao=1,
            caminho_arquivo=arquivo_pdf,
        )
        self.assertIn('(v1)', str(versao))

    def test_local_str(self):
        local = Local.objects.create(
            evento=self.evento_aceita,
            nome='Auditório A',
            capacidade=200,
        )
        self.assertEqual(str(local), 'Auditório A')


class TestSubmissaoService(SubmissaoBaseTestCase):
    """Testes unitários da camada de serviço de submissão."""

    def test_criar_submissao_rascunho_com_sucesso(self):
        """Criação de submissão em rascunho sem arquivo anexado."""
        dados = {
            'titulo': 'Novas Abordagens Em Redes Neurais Convolucionais',
            'abstract': 'A study on convolutional architectures.',
            'resumo': 'Estudo aprofundado sobre CNNs.',
            'palavras_chave': 'CNN, Redes Neurais, IA',
            'tipo': TipoSubmissao.ARTIGO,
        }
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao=dados,
        )

        self.assertIsNotNone(submissao.id)
        self.assertEqual(submissao.status, StatusSubmissao.RASCUNHO)
        self.assertEqual(submissao.autor_principal, self.autor)
        self.assertEqual(submissao.autores.count(), 1)

        autor_principal_rel = submissao.autores.first()
        self.assertEqual(autor_principal_rel.usuario, self.autor)
        self.assertEqual(autor_principal_rel.tipo_participacao, TipoParticipacaoAutor.PRINCIPAL)

    def test_criar_submissao_bloqueada_em_evento_que_recusa(self):
        """Evento com aceita_submissao=False deve lançar ValidationError."""
        dados = {
            'titulo': 'Tentativa De Submissao Em Evento Fechado',
            'abstract': 'Attempting to submit to closed event.',
            'palavras_chave': 'Teste, Bloqueio',
        }
        with self.assertRaises(ValidationError) as ctx:
            SubmissaoService.criar_submissao(
                usuario=self.autor,
                evento_id=self.evento_recusa.id,
                area_id=self.area_ti.id,
                dados_submissao=dados,
            )
        self.assertIn('Este evento não aceita submissão de trabalhos acadêmicos.', str(ctx.exception))

    def test_criar_submissao_bloqueada_em_evento_sem_regra(self):
        """Evento sem regra cadastrada deve lançar ValidationError."""
        dados = {
            'titulo': 'Tentativa Sem Regra',
            'abstract': 'Abstract test.',
            'palavras_chave': 'Palavra1, Palavra2',
        }
        with self.assertRaises(ValidationError) as ctx:
            SubmissaoService.criar_submissao(
                usuario=self.autor,
                evento_id=self.evento_sem_regra.id,
                area_id=self.area_ti.id,
                dados_submissao=dados,
            )
        self.assertIn('Este evento não aceita submissão de trabalhos acadêmicos.', str(ctx.exception))

    def test_criar_submissao_com_dados_autor_principal(self):
        """Salvar dados complementares de autoria (lattes, linkedin, afiliacao, titulacao)."""
        dados = {
            'titulo': 'Sistemas Embarcados De Baixo Consumo',
            'abstract': 'Embedded low power systems.',
            'palavras_chave': 'IoT, Embarcados',
            'lattes_url': 'https://lattes.cnpq.br/1234567890123456',
            'linkedin_url': 'https://linkedin.com/in/lucaspesquisador',
            'afiliacao_institucional': 'Universidade Federal Da Bahia',
            'maior_titulacao': 'Doutorado em Ciência da Computação',
        }
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao=dados,
        )

        autor_rel = submissao.autores.get(usuario=self.autor)
        self.assertEqual(autor_rel.lattes_url, 'https://lattes.cnpq.br/1234567890123456')
        self.assertEqual(autor_rel.linkedin_url, 'https://linkedin.com/in/lucaspesquisador')
        self.assertEqual(autor_rel.afiliacao_institucional, 'Universidade Federal Da Bahia')
        self.assertEqual(autor_rel.maiór_titulacao, 'Doutorado em Ciência da Computação')

    def test_criar_submissao_com_coautores(self):
        """Criação de submissão incluindo coautores."""
        dados = {
            'titulo': 'Colaboração Científica Entre Laboratórios',
            'abstract': 'Scientific collaboration research.',
            'palavras_chave': 'Pesquisa, Colaboracao',
            'coautores': [
                {
                    'usuario': self.coautor,
                    'tipo_participacao': TipoParticipacaoAutor.COAUTOR,
                    'ordem_autoria': 2,
                    'afiliacao_institucional': 'Universidade de São Paulo',
                    'maior_titulacao': 'Mestrado',
                }
            ],
        }
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao=dados,
        )

        self.assertEqual(submissao.autores.count(), 2)
        coautor_rel = submissao.autores.get(usuario=self.coautor)
        self.assertEqual(coautor_rel.tipo_participacao, TipoParticipacaoAutor.COAUTOR)
        self.assertEqual(coautor_rel.ordem_autoria, 2)
        self.assertEqual(coautor_rel.afiliacao_institucional, 'Universidade de São Paulo')
        self.assertEqual(coautor_rel.maiór_titulacao, 'Mestrado')

    def test_criar_submissao_direta_com_upload_arquivo(self):
        """Submissão direta com envio de PDF altera status para Submetida e cria versão 1."""
        arquivo_pdf = gerar_arquivo_pdf_teste()
        dados = {
            'titulo': 'Modelos Generativos Em Visão Computacional',
            'abstract': 'Generative models applied to computer vision.',
            'palavras_chave': 'GANs, Difusao, Visao',
            'arquivo': arquivo_pdf,
        }
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao=dados,
        )

        self.assertEqual(submissao.status, StatusSubmissao.SUBMETIDA)
        self.assertEqual(submissao.versoes.count(), 1)
        versao_1 = submissao.versoes.first()
        self.assertEqual(versao_1.numero_versao, 1)
        self.assertIsNotNone(versao_1.caminho_arquivo)

    def test_submeter_trabalho_em_duas_etapas(self):
        """Criação em duas etapas: primeiro rascunho, depois envio de arquivo via submeter_trabalho."""
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao={
                'titulo': 'Rascunho Que Sera Submetido Depois',
                'abstract': 'Draft abstract.',
                'palavras_chave': 'Rascunho, Teste',
            },
        )
        self.assertEqual(submissao.status, StatusSubmissao.RASCUNHO)
        self.assertEqual(submissao.versoes.count(), 0)

        # Segunda etapa: submeter
        arquivo_pdf = gerar_arquivo_pdf_teste()
        versao = SubmissaoService.submeter_trabalho(
            submissao=submissao,
            arquivo=arquivo_pdf,
            usuario=self.autor,
        )

        submissao.refresh_from_db()
        self.assertEqual(submissao.status, StatusSubmissao.SUBMETIDA)
        self.assertEqual(versao.numero_versao, 1)
        self.assertEqual(submissao.versoes.count(), 1)

    def test_submeter_trabalho_arquivo_invalido_rejeitado(self):
        """Arquivo com formato não permitido (.sh, .exe) deve ser recusado."""
        submissao = SubmissaoService.criar_submissao(
            usuario=self.autor,
            evento_id=self.evento_aceita.id,
            area_id=self.area_ti.id,
            dados_submissao={
                'titulo': 'Trabalho Com Arquivo Invalido',
                'abstract': 'Abstract text.',
                'palavras_chave': 'Invalido, Teste',
            },
        )
        arquivo_invalido = gerar_arquivo_invalido_teste()
        with self.assertRaises(ValidationError):
            SubmissaoService.submeter_trabalho(
                submissao=submissao,
                arquivo=arquivo_invalido,
                usuario=self.autor,
            )

    def test_submeter_trabalho_fora_do_prazo_rejeitado(self):
        """Tentativa de submeter quando prazo encerrou deve ser recusada."""
        # Evento com prazo de submissão encerrado
        self.regra_aceita.data_hora_fim = timezone.now() - timedelta(minutes=1)
        self.regra_aceita.save()

        submissao = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Tentativa Fora Do Prazo',
            abstract='Abstract late.',
            palavras_chave='Atrasado, Teste',
            status=StatusSubmissao.RASCUNHO,
        )

        arquivo_pdf = gerar_arquivo_pdf_teste()
        with self.assertRaises(ValidationError):
            SubmissaoService.submeter_trabalho(
                submissao=submissao,
                arquivo=arquivo_pdf,
                usuario=self.autor,
            )


class TestSubmissaoAPI(SubmissaoBaseTestCase):
    """Testes de integração dos endpoints da API REST de submissão."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_api_criar_submissao_rascunho(self):
        """POST /api/sgie/v1/submissoes/ cria rascunho com sucesso."""
        self.client.force_authenticate(user=self.autor)
        payload = {
            'evento': self.evento_aceita.id,
            'area': self.area_ti.id,
            'titulo': 'Desenvolvimento De Modelos De Linguagem Para Portugues',
            'abstract': 'Exploration of large language models for Portuguese processing.',
            'resumo': 'Resumo abrangente sobre modelos LLM.',
            'palavras_chave': 'LLM, PLN, Inteligencia Artificial',
            'tipo': TipoSubmissao.ARTIGO,
            'lattes_url': 'https://lattes.cnpq.br/0000111122223333',
            'afiliacao_institucional': 'UFBA',
            'maior_titulacao': 'Doutorando',
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['status'], StatusSubmissao.RASCUNHO)

        submissao = Submissao.objects.get(id=response.data['id'])
        self.assertEqual(submissao.status, StatusSubmissao.RASCUNHO)
        self.assertEqual(submissao.autor_principal, self.autor)

        # Verificar autor principal
        autor_rel = submissao.autores.get(usuario=self.autor)
        self.assertEqual(autor_rel.lattes_url, 'https://lattes.cnpq.br/0000111122223333')
        self.assertEqual(autor_rel.afiliacao_institucional, 'UFBA')
        self.assertEqual(autor_rel.maiór_titulacao, 'Doutorando')

    def test_api_criar_submissao_direta_com_upload_pdf(self):
        """POST /api/sgie/v1/submissoes/ com arquivo PDF submete imediatamente na v1."""
        self.client.force_authenticate(user=self.autor)
        arquivo_pdf = gerar_arquivo_pdf_teste('artigo_completo.pdf')

        payload = {
            'evento': self.evento_aceita.id,
            'area': self.area_ti.id,
            'titulo': 'Segmentacao Semantica De Imagens Medicas',
            'abstract': 'Semantic segmentation for CT scans.',
            'resumo': 'Segmentação aplicada à medicina.',
            'palavras_chave': 'Medicina, IA, Segmentacao',
            'tipo': TipoSubmissao.ARTIGO,
            'arquivo': arquivo_pdf,
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['status'], StatusSubmissao.SUBMETIDA)

        submissao = Submissao.objects.get(id=response.data['id'])
        self.assertEqual(submissao.status, StatusSubmissao.SUBMETIDA)
        self.assertEqual(submissao.versoes.count(), 1)
        self.assertEqual(submissao.versoes.first().numero_versao, 1)

    def test_api_submissao_em_duas_etapas(self):
        """Fluxo em 2 etapas: POST /submissoes/ (rascunho) -> POST /submissoes/{id}/submeter/."""
        self.client.force_authenticate(user=self.autor)

        # Etapa 1: criar rascunho
        payload_rascunho = {
            'evento': self.evento_aceita.id,
            'area': self.area_saude.id,
            'titulo': 'Analise Genomica Com Redes Neurais Graficas',
            'abstract': 'Genomic data analysis with graph neural networks.',
            'palavras_chave': 'Genomica, Grafos, IA',
            'tipo': TipoSubmissao.ARTIGO,
        }
        resp1 = self.client.post('/api/sgie/v1/submissoes/', payload_rascunho, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        submissao_id = resp1.data['id']
        self.assertEqual(resp1.data['status'], StatusSubmissao.RASCUNHO)

        # Etapa 2: submeter trabalho
        arquivo_pdf = gerar_arquivo_pdf_teste('versao_final.pdf')
        resp2 = self.client.post(
            f'/api/sgie/v1/submissoes/{submissao_id}/submeter/',
            {'arquivo': arquivo_pdf},
            format='multipart',
        )
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED, resp2.data)
        self.assertEqual(resp2.data['numero_versao'], 1)

        submissao = Submissao.objects.get(id=submissao_id)
        self.assertEqual(submissao.status, StatusSubmissao.SUBMETIDA)

    def test_api_rejeitar_evento_que_nao_aceita_submissoes(self):
        """Submissão para evento com aceita_submissao=False retorna 400 Bad Request."""
        self.client.force_authenticate(user=self.autor)
        payload = {
            'evento': self.evento_recusa.id,
            'area': self.area_ti.id,
            'titulo': 'Tentativa Invalida Em Evento Fechado',
            'abstract': 'This should fail.',
            'palavras_chave': 'Falha, Teste',
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Este evento não aceita submissão de trabalhos acadêmicos.', str(response.data))

    def test_api_rejeitar_evento_sem_regra(self):
        """Submissão para evento sem regra cadastrada retorna 400 Bad Request."""
        self.client.force_authenticate(user=self.autor)
        payload = {
            'evento': self.evento_sem_regra.id,
            'area': self.area_ti.id,
            'titulo': 'Tentativa Invalida Em Evento Sem Regra',
            'abstract': 'This should fail too.',
            'palavras_chave': 'Falha, Teste',
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Este evento não aceita submissão de trabalhos acadêmicos.', str(response.data))

    def test_api_validacao_arquivo_invalido_rejeita_com_400(self):
        """Envio de arquivo não PDF/DOCX rejeita com 400 Bad Request."""
        self.client.force_authenticate(user=self.autor)
        arquivo_sh = gerar_arquivo_invalido_teste('executavel.sh')

        payload = {
            'evento': self.evento_aceita.id,
            'area': self.area_ti.id,
            'titulo': 'Tentativa Com Arquivo Shell Script',
            'abstract': 'Testing file validation.',
            'palavras_chave': 'Teste, Arquivo',
            'arquivo': arquivo_sh,
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('arquivo', response.data)

    def test_api_listar_areas(self):
        """GET /api/sgie/v1/areas/ retorna lista de áreas temáticas com status 200."""
        self.client.force_authenticate(user=self.autor)
        response = self.client.get('/api/sgie/v1/areas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nomes = [item['nome'] for item in response.data]
        self.assertIn(self.area_ti.nome, nomes)
        self.assertIn(self.area_saude.nome, nomes)

    def test_api_listar_submissoes_proprias(self):
        """GET /api/sgie/v1/submissoes/ lista apenas submissões que o usuário tem acesso."""
        # Submissão do autor
        submissao_autor = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Artigo Do Autor Teste',
            abstract='Author paper abstract.',
            palavras_chave='Teste, Autor',
            status=StatusSubmissao.RASCUNHO,
        )
        # Submissão de outro usuário
        Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_saude,
            autor_principal=self.outro_usuario,
            titulo='Artigo De Outro Pesquisador',
            abstract='Other paper abstract.',
            palavras_chave='Teste, Outro',
            status=StatusSubmissao.RASCUNHO,
        )

        self.client.force_authenticate(user=self.autor)
        response = self.client.get('/api/sgie/v1/submissoes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titulos = [item['titulo'] for item in response.data]
        self.assertIn(submissao_autor.titulo, titulos)
        self.assertNotIn('Artigo De Outro Pesquisador', titulos)

    def test_api_filtrar_submissoes_por_evento(self):
        """GET /api/sgie/v1/submissoes/?evento={id} filtra por evento corretamente."""
        # Criar segundo evento que aceita
        evento_2 = Evento.objects.create(
            usuario_representante=self.organizador,
            nome='Simposio De Engenharia E Computacao 2026',
            descricao='Simpósio anual de computação.',
            data=timezone.now().date() + timedelta(days=90),
            hora_inicio=time(8, 0),
            hora_fim=time(17, 0),
            local='Auditório B',
            capacidade=300,
            categoria=CategoriaEvento.SIMPOSIO,
            status=StatusEvento.PUBLICADO,
        )
        RegraSubmissao.objects.create(
            evento=evento_2,
            aceita_submissao=True,
            data_hora_inicio=timezone.now() - timedelta(days=1),
            data_hora_fim=timezone.now() + timedelta(days=10),
        )

        sub1 = Submissao.objects.create(
            evento=self.evento_aceita,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Trabalho Do Evento Um',
            abstract='Paper event one.',
            palavras_chave='Evento1, Teste',
            status=StatusSubmissao.RASCUNHO,
        )
        sub2 = Submissao.objects.create(
            evento=evento_2,
            area=self.area_ti,
            autor_principal=self.autor,
            titulo='Trabalho Do Evento Dois',
            abstract='Paper event two.',
            palavras_chave='Evento2, Teste',
            status=StatusSubmissao.RASCUNHO,
        )

        self.client.force_authenticate(user=self.autor)

        # Filtrar por evento 1
        resp_evento1 = self.client.get(f'/api/sgie/v1/submissoes/?evento={self.evento_aceita.id}')
        self.assertEqual(resp_evento1.status_code, status.HTTP_200_OK)
        titulos_ev1 = [s['titulo'] for s in resp_evento1.data]
        self.assertIn(sub1.titulo, titulos_ev1)
        self.assertNotIn(sub2.titulo, titulos_ev1)

        # Filtrar por evento 2
        resp_evento2 = self.client.get(f'/api/sgie/v1/submissoes/?evento={evento_2.id}')
        self.assertEqual(resp_evento2.status_code, status.HTTP_200_OK)
        titulos_ev2 = [s['titulo'] for s in resp_evento2.data]
        self.assertIn(sub2.titulo, titulos_ev2)
        self.assertNotIn(sub1.titulo, titulos_ev2)

    def test_api_submissao_com_coautores_via_post(self):
        """POST /api/sgie/v1/submissoes/ criando autor principal e coautor com dados acadêmicos."""
        self.client.force_authenticate(user=self.autor)
        payload = {
            'evento': self.evento_aceita.id,
            'area': self.area_ti.id,
            'titulo': 'Trabalho Em Parceria Cientifica Com Coautor',
            'abstract': 'Joint research work abstract.',
            'palavras_chave': 'Parceria, Coautoria, IA',
            'tipo': TipoSubmissao.ARTIGO,
            'lattes_url': 'https://lattes.cnpq.br/1234567890123456',
            'afiliacao_institucional': 'UFBA',
            'maior_titulacao': 'Doutorando',
            'autores': [
                {
                    'usuario': self.coautor.id,
                    'tipo_participacao': TipoParticipacaoAutor.COAUTOR,
                    'ordem_autoria': 2,
                    'afiliacao_institucional': 'USP',
                    'maior_titulacao': 'Mestre',
                }
            ],
        }
        response = self.client.post('/api/sgie/v1/submissoes/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        submissao = Submissao.objects.get(id=response.data['id'])
        self.assertEqual(submissao.autores.count(), 2)

        autor_princ = submissao.autores.get(usuario=self.autor)
        self.assertEqual(autor_princ.tipo_participacao, TipoParticipacaoAutor.PRINCIPAL)
        self.assertEqual(autor_princ.maiór_titulacao, 'Doutorando')

        coautor_rec = submissao.autores.get(usuario=self.coautor)
        self.assertEqual(coautor_rec.tipo_participacao, TipoParticipacaoAutor.COAUTOR)
        self.assertEqual(coautor_rec.afiliacao_institucional, 'USP')
        self.assertEqual(coautor_rec.maiór_titulacao, 'Mestre')
