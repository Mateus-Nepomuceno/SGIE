from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from eventos.models import CategoriaEvento, Evento, Modalidade, StatusEvento
from inscricao.models import Inscricao
from pagamentos.models import (
    Canal,
    CategoriaPreco,
    Certificado,
    Cobranca,
    Comunicacao,
    IsencaoPagamento,
    Lote,
    MetodoPagamento,
    Pagamento,
    Reembolso,
    StatusCobranca,
    StatusPagamento,
    StatusReembolso,
    TipoIsencao,
)
from pagamentos.services import (
    ServicoCobranca,
    ServicoPagamento,
)

Usuario = get_user_model()


class PagamentosModelTests(TestCase):
    def setUp(self):
        self.organizador = Usuario.objects.create_user(
            email='organizador@evento.com',
            cpf='11122233344',
            nome_completo='Organizador Geral',
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 99999-0000',
            password='SenhaSegura@123',
        )
        self.participante = Usuario.objects.create_user(
            email='participante@evento.com',
            cpf='99988877766',
            nome_completo='Participante Teste',
            data_nascimento=date(1998, 5, 20),
            telefone='(71) 98888-2222',
            password='SenhaSegura@123',
        )
        data_evento = (timezone.now() + timedelta(days=10)).date()
        self.evento = Evento.objects.create(
            nome='Congresso De Tecnologia',
            descricao='Congresso anual de tecnologia e inovação.',
            usuario_representante=self.organizador,
            data=data_evento,
            hora_inicio=time(14, 0),
            hora_fim=time(18, 0),
            local='Auditório Principal',
            capacidade=100,
            modalidade=Modalidade.PRESENCIAL,
            categoria=CategoriaEvento.CONGRESSO,
            status=StatusEvento.INSCRICOES_ABERTAS,
            e_gratuito=False,
            preco=Decimal('100.00'),
        )
        self.inscricao = Inscricao.objects.create(
            usuario=self.participante,
            evento=self.evento,
            status='pendente_pagamento',
        )

    def test_categoria_preco_e_lote_criacao(self):
        agora = timezone.now()
        categoria = CategoriaPreco.objects.create(
            evento=self.evento,
            nome='Estudante',
            descricao='Válido mediante comprovante estudantil',
        )
        self.assertEqual(str(categoria), f'Estudante ({self.evento.nome})')

        lote = Lote.objects.create(
            categoria_preco=categoria,
            nome='1º Lote',
            numero=1,
            preco=Decimal('50.00'),
            quantidade_total=50,
            data_inicio=agora - timedelta(days=1),
            data_fim=agora + timedelta(days=5),
        )
        self.assertEqual(lote.quantidade_disponivel, 50)
        self.assertTrue(lote.esta_vigente)
        self.assertTrue(lote.tem_vagas)

    def test_lote_validacao_datas_e_vagas(self):
        agora = timezone.now()
        categoria = CategoriaPreco.objects.create(evento=self.evento, nome='Geral')

        with self.assertRaises(ValidationError):
            Lote.objects.create(
                categoria_preco=categoria,
                nome='Lote Inválido',
                preco=Decimal('100.00'),
                quantidade_total=20,
                data_inicio=agora + timedelta(days=5),
                data_fim=agora + timedelta(days=2),
            )

        with self.assertRaises(ValidationError):
            lote = Lote(
                categoria_preco=categoria,
                nome='Lote Excedido',
                preco=Decimal('100.00'),
                quantidade_total=10,
                quantidade_disponivel=15,
                data_inicio=agora,
                data_fim=agora + timedelta(days=2),
            )
            lote.clean()

    def test_cobranca_criacao_e_vencimento(self):
        agora = timezone.now()
        categoria = CategoriaPreco.objects.create(evento=self.evento, nome='Geral')
        lote = Lote.objects.create(
            categoria_preco=categoria,
            nome='1º Lote',
            preco=Decimal('100.00'),
            quantidade_total=10,
            data_inicio=agora - timedelta(days=1),
            data_fim=agora + timedelta(days=2),
        )
        cobranca = Cobranca.objects.create(
            inscricao=self.inscricao,
            lote=lote,
            valor_original=lote.preco,
            valor_final=lote.preco,
            status=StatusCobranca.PENDENTE,
            data_vencimento=agora + timedelta(days=3),
        )
        self.assertFalse(cobranca.esta_vencida)
        cobranca.data_vencimento = agora - timedelta(days=1)
        self.assertTrue(cobranca.esta_vencida)

    def test_isencao_total(self):
        agora = timezone.now()
        cobranca = Cobranca.objects.create(
            inscricao=self.inscricao,
            valor_original=Decimal('100.00'),
            valor_final=Decimal('100.00'),
            status=StatusCobranca.PENDENTE,
            data_vencimento=agora + timedelta(days=3),
        )
        isencao = IsencaoPagamento.objects.create(
            cobranca=cobranca,
            tipo=TipoIsencao.TOTAL,
            motivo='Bolsista de Iniciação Científica',
            aprovado_por=self.organizador,
        )
        isencao.aplicar_a_cobranca()
        cobranca.refresh_from_db()
        self.assertEqual(cobranca.valor_final, Decimal('0.00'))
        self.assertEqual(cobranca.status, StatusCobranca.PAGA)

    def test_isencao_parcial_percentual(self):
        agora = timezone.now()
        cobranca = Cobranca.objects.create(
            inscricao=self.inscricao,
            valor_original=Decimal('200.00'),
            valor_final=Decimal('200.00'),
            status=StatusCobranca.PENDENTE,
            data_vencimento=agora + timedelta(days=3),
        )
        isencao = IsencaoPagamento.objects.create(
            cobranca=cobranca,
            tipo=TipoIsencao.PARCIAL,
            desconto_percentual=Decimal('50.00'),
            motivo='Desconto para afiliados',
            aprovado_por=self.organizador,
        )
        isencao.aplicar_a_cobranca()
        cobranca.refresh_from_db()
        self.assertEqual(cobranca.valor_final, Decimal('100.00'))
        self.assertEqual(cobranca.status, StatusCobranca.PENDENTE)

    def test_ciclo_de_vida_estados_pagamento(self):
        agora = timezone.now()
        cobranca = Cobranca.objects.create(
            inscricao=self.inscricao,
            valor_original=Decimal('80.00'),
            valor_final=Decimal('80.00'),
            status=StatusCobranca.PENDENTE,
            data_vencimento=agora + timedelta(days=3),
        )
        pagamento = Pagamento.objects.create(
            cobranca=cobranca,
            valor=cobranca.valor_final,
            metodo=MetodoPagamento.PIX,
            status=StatusPagamento.PENDENTE,
        )

        # Transição inválida: PENDENTE -> APROVADO sem passar por PROCESSANDO
        with self.assertRaises(ValidationError):
            pagamento.atualizar_status(StatusPagamento.APROVADO)

        # Transições válidas: PENDENTE -> PROCESSANDO -> APROVADO
        pagamento.atualizar_status(StatusPagamento.PROCESSANDO)
        self.assertEqual(pagamento.status, StatusPagamento.PROCESSANDO)

        pagamento.atualizar_status(StatusPagamento.APROVADO, transacao_id='TX-998877')
        self.assertEqual(pagamento.status, StatusPagamento.APROVADO)
        self.assertIsNotNone(pagamento.data_pagamento)
        self.assertEqual(pagamento.transacao_id, 'TX-998877')

        # Transição válida: APROVADO -> REEMBOLSADO
        pagamento.atualizar_status(StatusPagamento.REEMBOLSADO)
        self.assertEqual(pagamento.status, StatusPagamento.REEMBOLSADO)

    def test_reembolso_criacao_e_validacao(self):
        agora = timezone.now()
        cobranca = Cobranca.objects.create(
            inscricao=self.inscricao,
            valor_original=Decimal('100.00'),
            valor_final=Decimal('100.00'),
            status=StatusCobranca.PAGA,
            data_vencimento=agora + timedelta(days=3),
        )
        pagamento = Pagamento.objects.create(
            cobranca=cobranca,
            valor=Decimal('100.00'),
            metodo=MetodoPagamento.CARTAO_CREDITO,
            status=StatusPagamento.APROVADO,
            data_pagamento=agora,
        )

        # Reembolso com valor superior ao pagamento deve falhar
        with self.assertRaises(ValidationError):
            reembolso_invalido = Reembolso(
                pagamento=pagamento,
                valor=Decimal('150.00'),
                motivo='Desistência',
                solicitado_por=self.participante,
            )
            reembolso_invalido.clean()

        reembolso = Reembolso.objects.create(
            pagamento=pagamento,
            valor=Decimal('100.00'),
            motivo='Desistência antes do evento',
            status=StatusReembolso.SOLICITADO,
            solicitado_por=self.participante,
        )
        self.assertEqual(reembolso.pagamento, pagamento)
        self.assertEqual(reembolso.status, StatusReembolso.SOLICITADO)

    def test_certificado_e_comunicacao(self):
        certificado = Certificado.objects.create(
            inscricao=self.inscricao,
            carga_horaria=20,
            disponivel=True,
        )
        self.assertTrue(bool(certificado.codigo_autenticacao))
        self.assertTrue(certificado.disponivel)

        comunicacao = Comunicacao.objects.create(
            destinatario=self.participante,
            certificado=certificado,
            canal=Canal.EMAIL,
            assunto='Seu certificado está disponível',
            mensagem='Parabéns pela participação no evento!',
        )
        self.assertEqual(comunicacao.canal, Canal.EMAIL)
        self.assertEqual(comunicacao.destinatario, self.participante)


class PagamentosServiceTests(TestCase):
    def setUp(self):
        self.organizador = Usuario.objects.create_user(
            email='organizador@evento.com',
            cpf='11122233344',
            nome_completo='Organizador Geral',
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 99999-0000',
            password='SenhaSegura@123',
        )
        self.participante = Usuario.objects.create_user(
            email='participante@evento.com',
            cpf='99988877766',
            nome_completo='Participante Teste',
            data_nascimento=date(1998, 5, 20),
            telefone='(71) 98888-2222',
            password='SenhaSegura@123',
        )
        data_evento = (timezone.now() + timedelta(days=10)).date()
        self.evento = Evento.objects.create(
            nome='Congresso De Inteligencia Artificial',
            descricao='Congresso anual de IA.',
            usuario_representante=self.organizador,
            data=data_evento,
            hora_inicio=time(9, 0),
            hora_fim=time(18, 0),
            local='Auditório Principal',
            capacidade=50,
            modalidade=Modalidade.PRESENCIAL,
            categoria=CategoriaEvento.CONGRESSO,
            status=StatusEvento.INSCRICOES_ABERTAS,
            e_gratuito=False,
            preco=Decimal('120.00'),
        )
        self.inscricao = Inscricao.objects.create(
            usuario=self.participante,
            evento=self.evento,
            status='pendente_pagamento',
        )
        self.categoria = CategoriaPreco.objects.create(
            evento=self.evento,
            nome='Profissional',
        )
        agora = timezone.now()
        self.lote = Lote.objects.create(
            categoria_preco=self.categoria,
            nome='Lote Regular',
            preco=Decimal('150.00'),
            quantidade_total=10,
            data_inicio=agora - timedelta(days=1),
            data_fim=agora + timedelta(days=5),
        )
        self.servico_pagamento = ServicoPagamento()

    def test_gerar_cobranca_sucesso(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            categoria=self.categoria,
            lote=self.lote,
        )
        self.assertEqual(cobranca.valor_original, Decimal('150.00'))
        self.assertEqual(cobranca.valor_final, Decimal('150.00'))
        self.assertEqual(cobranca.status, StatusCobranca.PENDENTE)
        self.assertEqual(cobranca.lote, self.lote)

    def test_gerar_cobranca_evento_gratuito_falha(self):
        self.evento.e_gratuito = True
        self.evento.save(update_fields=['e_gratuito'])

        with self.assertRaises(ValidationError):
            ServicoCobranca.gerar_cobranca(inscricao=self.inscricao)

    def test_gerar_cobranca_lote_sem_vagas_falha(self):
        self.lote.quantidade_disponivel = 0
        self.lote.save(update_fields=['quantidade_disponivel'])

        with self.assertRaises(ValidationError):
            ServicoCobranca.gerar_cobranca(
                inscricao=self.inscricao,
                lote=self.lote,
            )

    def test_conceder_isencao_total_confirma_inscricao(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        vagas_iniciais = self.lote.quantidade_disponivel

        isencao = ServicoCobranca.conceder_isencao(
            cobranca=cobranca,
            tipo=TipoIsencao.TOTAL,
            motivo='Isenção concedida para palestrante convidado',
            aprovado_por=self.organizador,
        )
        cobranca.refresh_from_db()
        self.inscricao.refresh_from_db()
        self.lote.refresh_from_db()

        self.assertEqual(cobranca.status, StatusCobranca.PAGA)
        self.assertEqual(cobranca.valor_final, Decimal('0.00'))
        self.assertEqual(self.inscricao.status, 'confirmada')
        self.assertEqual(self.lote.quantidade_disponivel, vagas_iniciais - 1)
        self.assertEqual(isencao.tipo, TipoIsencao.TOTAL)

    def test_processar_pagamento_pix(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.PIX,
        )
        self.assertEqual(pagamento.status, StatusPagamento.PROCESSANDO)
        self.assertTrue(bool(pagamento.qr_code_pix))
        self.assertTrue(pagamento.transacao_id.startswith('SIM-'))

    def test_processar_pagamento_cartao_aprovado(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        vagas_iniciais = self.lote.quantidade_disponivel

        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.CARTAO_CREDITO,
            dados_cartao={'numero_cartao': '4111111111111234'},
        )
        cobranca.refresh_from_db()
        self.inscricao.refresh_from_db()
        self.lote.refresh_from_db()

        self.assertEqual(pagamento.status, StatusPagamento.APROVADO)
        self.assertEqual(cobranca.status, StatusCobranca.PAGA)
        self.assertEqual(self.inscricao.status, 'confirmada')
        self.assertEqual(self.lote.quantidade_disponivel, vagas_iniciais - 1)

        # Verifica comunicação enviada
        comunicacao = Comunicacao.objects.filter(destinatario=self.participante).first()
        self.assertIsNotNone(comunicacao)
        self.assertIn('Pagamento Aprovado', comunicacao.assunto)

    def test_processar_pagamento_cartao_recusado(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.CARTAO_CREDITO,
            dados_cartao={'numero_cartao': '4111111111110000'},
        )
        cobranca.refresh_from_db()
        self.inscricao.refresh_from_db()

        self.assertEqual(pagamento.status, StatusPagamento.RECUSADO)
        self.assertEqual(cobranca.status, StatusCobranca.PENDENTE)
        self.assertEqual(self.inscricao.status, 'pendente_pagamento')

        # Verifica comunicação de falha
        comunicacao = Comunicacao.objects.filter(destinatario=self.participante).first()
        self.assertIsNotNone(comunicacao)
        self.assertIn('Falha no Pagamento', comunicacao.assunto)

    def test_processar_notificacao_webhook_aprovacao(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.PIX,
        )
        self.assertEqual(pagamento.status, StatusPagamento.PROCESSANDO)

        pagamento_atualizado = ServicoPagamento.processar_notificacao_webhook(
            transacao_id=pagamento.transacao_id,
            novo_status=StatusPagamento.APROVADO,
            detalhes={'webhook_recebido': True},
        )
        cobranca.refresh_from_db()
        self.inscricao.refresh_from_db()

        self.assertEqual(pagamento_atualizado.status, StatusPagamento.APROVADO)
        self.assertEqual(cobranca.status, StatusCobranca.PAGA)
        self.assertEqual(self.inscricao.status, 'confirmada')

    def test_solicitar_reembolso_sucesso(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.CARTAO_CREDITO,
        )
        self.assertEqual(pagamento.status, StatusPagamento.APROVADO)
        vagas_apos_pagamento = self.lote.quantidade_disponivel

        reembolso = self.servico_pagamento.solicitar_reembolso(
            pagamento=pagamento,
            motivo='Imprevisto de agenda pessoal',
            solicitado_por=self.participante,
        )
        pagamento.refresh_from_db()
        cobranca.refresh_from_db()
        self.inscricao.refresh_from_db()
        self.lote.refresh_from_db()

        self.assertEqual(reembolso.status, StatusReembolso.CONCLUIDO)
        self.assertEqual(pagamento.status, StatusPagamento.REEMBOLSADO)
        self.assertEqual(cobranca.status, StatusCobranca.CANCELADA)
        self.assertEqual(self.inscricao.status, 'cancelada')
        # Vaga foi devolvida ao lote
        self.assertEqual(self.lote.quantidade_disponivel, vagas_apos_pagamento + 1)

    def test_solicitar_reembolso_pagamento_nao_aprovado_falha(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = self.servico_pagamento.processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.PIX,
        )
        # Status está PROCESSANDO, não APROVADO
        with self.assertRaises(ValidationError):
            self.servico_pagamento.solicitar_reembolso(
                pagamento=pagamento,
                motivo='Desistência',
                solicitado_por=self.participante,
            )


class PagamentosAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organizador = Usuario.objects.create_user(
            email='organizador@evento.com',
            cpf='11122233344',
            nome_completo='Organizador Geral',
            data_nascimento=date(1990, 1, 1),
            telefone='(71) 99999-0000',
            password='SenhaSegura@123',
        )
        self.participante = Usuario.objects.create_user(
            email='participante@evento.com',
            cpf='99988877766',
            nome_completo='Participante Teste',
            data_nascimento=date(1998, 5, 20),
            telefone='(71) 98888-2222',
            password='SenhaSegura@123',
        )
        data_evento = (timezone.now() + timedelta(days=10)).date()
        self.evento = Evento.objects.create(
            nome='Seminario De Cloud Computing',
            descricao='Seminário de computação em nuvem.',
            usuario_representante=self.organizador,
            data=data_evento,
            hora_inicio=time(8, 0),
            hora_fim=time(17, 0),
            local='Auditório Principal',
            capacidade=100,
            modalidade=Modalidade.PRESENCIAL,
            categoria=CategoriaEvento.SEMINARIO,
            status=StatusEvento.INSCRICOES_ABERTAS,
            e_gratuito=False,
            preco=Decimal('80.00'),
        )
        self.inscricao = Inscricao.objects.create(
            usuario=self.participante,
            evento=self.evento,
            status='pendente_pagamento',
        )
        self.categoria = CategoriaPreco.objects.create(
            evento=self.evento,
            nome='Geral',
        )
        agora = timezone.now()
        self.lote = Lote.objects.create(
            categoria_preco=self.categoria,
            nome='1º Lote',
            preco=Decimal('80.00'),
            quantidade_total=20,
            data_inicio=agora - timedelta(days=1),
            data_fim=agora + timedelta(days=5),
        )

    def test_gerenciar_categoria_preco_e_lote_endpoints(self):
        self.client.force_authenticate(user=self.organizador)

        # Criação de categoria
        resp_cat = self.client.post(
            '/api/sgie/v1/categorias-preco/',
            {
                'evento': self.evento.id,
                'nome': 'Estudante',
                'descricao': 'Válido com carteirinha',
            },
            format='json',
        )
        self.assertEqual(resp_cat.status_code, status.HTTP_201_CREATED)
        cat_id = resp_cat.data['id']

        # Criação de lote
        agora = timezone.now()
        resp_lote = self.client.post(
            '/api/sgie/v1/lotes/',
            {
                'categoria_preco': cat_id,
                'nome': 'Lote Meia Entrada',
                'numero': 1,
                'preco': '40.00',
                'quantidade_total': 15,
                'data_inicio': (agora - timedelta(days=1)).isoformat(),
                'data_fim': (agora + timedelta(days=4)).isoformat(),
            },
            format='json',
        )
        self.assertEqual(resp_lote.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_lote.data['preco'], '40.00')

    def test_fluxo_completo_cobranca_pagamento_e_reembolso_api(self):
        # 1. Participante emite cobrança para sua inscrição
        self.client.force_authenticate(user=self.participante)
        resp_cobranca = self.client.post(
            '/api/sgie/v1/cobrancas/',
            {
                'inscricao_id': self.inscricao.id,
                'lote_id': self.lote.id,
                'dias_vencimento': 2,
            },
            format='json',
        )
        self.assertEqual(resp_cobranca.status_code, status.HTTP_201_CREATED)
        cobranca_id = resp_cobranca.data['id']
        self.assertEqual(resp_cobranca.data['status'], 'PENDENTE')

        # 2. Participante realiza o pagamento com Cartão
        resp_pagar = self.client.post(
            f'/api/sgie/v1/cobrancas/{cobranca_id}/pagar/',
            {
                'metodo': MetodoPagamento.CARTAO_CREDITO,
                'dados_cartao': {'numero_cartao': '4111111111111111'},
            },
            format='json',
        )
        self.assertEqual(resp_pagar.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_pagar.data['status'], 'APROVADO')
        pagamento_id = resp_pagar.data['id']

        # Inscrição confirmada após pagamento
        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.status, 'confirmada')

        # 3. Participante solicita reembolso
        resp_reembolso = self.client.post(
            f'/api/sgie/v1/pagamentos/{pagamento_id}/solicitar-reembolso/',
            {
                'motivo': 'Conflito com prova da faculdade',
            },
            format='json',
        )
        self.assertEqual(resp_reembolso.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_reembolso.data['status'], 'CONCLUIDO')

        # Inscrição cancelada após reembolso
        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.status, 'cancelada')

    def test_conceder_isencao_via_endpoint(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )

        # Participante comum não pode conceder isenção
        self.client.force_authenticate(user=self.participante)
        resp_proibida = self.client.post(
            f'/api/sgie/v1/cobrancas/{cobranca.id}/conceder-isencao/',
            {
                'tipo': TipoIsencao.TOTAL,
                'motivo': 'Tentativa indevida',
            },
            format='json',
        )
        self.assertEqual(resp_proibida.status_code, status.HTTP_403_FORBIDDEN)

        # Organizador do evento pode conceder isenção
        self.client.force_authenticate(user=self.organizador)
        resp_ok = self.client.post(
            f'/api/sgie/v1/cobrancas/{cobranca.id}/conceder-isencao/',
            {
                'tipo': TipoIsencao.TOTAL,
                'motivo': 'Isenção docente',
            },
            format='json',
        )
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_ok.data['status'], 'PAGA')
        self.assertEqual(resp_ok.data['valor_final'], '0.00')

    def test_webhook_pagamento_endpoint(self):
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        pagamento = ServicoPagamento().processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.PIX,
        )
        self.assertEqual(pagamento.status, 'PROCESSANDO')

        # Disparo não autenticado simulando servidor PSP
        self.client.force_authenticate(user=None)
        resp_webhook = self.client.post(
            '/api/sgie/v1/pagamentos/webhook/',
            {
                'transacao_id': pagamento.transacao_id,
                'status': StatusPagamento.APROVADO,
                'detalhes': {'webhook': 'simulado'},
            },
            format='json',
        )
        self.assertEqual(resp_webhook.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_webhook.data['pagamento_status'], 'APROVADO')

        self.inscricao.refresh_from_db()
        self.assertEqual(self.inscricao.status, 'confirmada')

    def test_validar_certificado_publico_endpoint(self):
        certificado = Certificado.objects.create(
            inscricao=self.inscricao,
            carga_horaria=30,
            disponivel=True,
        )
        self.client.force_authenticate(user=None)
        resp = self.client.get(f'/api/sgie/v1/certificados/validar/{certificado.codigo_autenticacao}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['autentico'])
        self.assertEqual(resp.data['codigo'], str(certificado.codigo_autenticacao))
        self.assertEqual(resp.data['evento'], self.evento.nome)

    def test_relatorio_financeiro_evento_endpoint(self):
        # Gera cobrança e pagamento aprovado
        cobranca = ServicoCobranca.gerar_cobranca(
            inscricao=self.inscricao,
            lote=self.lote,
        )
        ServicoPagamento().processar_pagamento(
            cobranca=cobranca,
            metodo_pagamento=MetodoPagamento.PIX,
        )
        ServicoPagamento.processar_notificacao_webhook(
            transacao_id=cobranca.pagamentos.first().transacao_id,
            novo_status=StatusPagamento.APROVADO,
        )

        # Participante não pode ver relatório financeiro
        self.client.force_authenticate(user=self.participante)
        resp_part = self.client.get(f'/api/sgie/v1/eventos/{self.evento.id}/relatorio-financeiro/')
        self.assertEqual(resp_part.status_code, status.HTTP_403_FORBIDDEN)

        # Organizador pode consultar o relatório
        self.client.force_authenticate(user=self.organizador)
        resp_org = self.client.get(f'/api/sgie/v1/eventos/{self.evento.id}/relatorio-financeiro/')
        self.assertEqual(resp_org.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_org.data['evento_id'], self.evento.id)
        self.assertEqual(Decimal(str(resp_org.data['total_arrecadado_bruto'])), Decimal('80.00'))
        self.assertEqual(Decimal(str(resp_org.data['total_liquido'])), Decimal('80.00'))
