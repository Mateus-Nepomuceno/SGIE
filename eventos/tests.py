from datetime import date, time, timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import PerfilOrganizador, Usuario
from eventos.models import Evento, StatusEvento
from eventos.services import EventoService


class PermissoesEventoTestCase(APITestCase):
    def setUp(self):
        # 1. Usuário Dono / Representante (Organizador Homologado)
        self.dono = Usuario.objects.create_user(
            email='organizador@teste.com',
            cpf='11122233344',
            nome_completo='Organizador Dono',
            data_nascimento=date(1990, 5, 10),
            telefone='61988887777',
            password='SenhaSegura123!',
        )
        PerfilOrganizador.objects.create(usuario=self.dono, homologado=True)

        # 2. Usuário Não-Dono (Outro Usuário)
        self.nao_dono = Usuario.objects.create_user(
            email='outro@teste.com',
            cpf='55566677788',
            nome_completo='Outro Usuário',
            data_nascimento=date(1995, 8, 20),
            telefone='61977776666',
            password='SenhaSegura123!',
        )

        # 3. Evento criado pelo dono
        self.evento = Evento.objects.create(
            usuario_representante=self.dono,
            nome='Congresso De Teste De Permissoes',
            descricao='Descrição de teste para validação de permissões de gestão.',
            data=date.today() + timedelta(days=30),
            hora_inicio=time(9, 0),
            hora_fim=time(18, 0),
            local='Campus Universitário',
            capacidade=100,
            status=StatusEvento.PUBLICADO,
        )

    def test_usuario_pode_gerenciar_evento_service(self):
        """Apenas o representante ou organizador contextual pode gerenciar o evento."""
        self.assertTrue(EventoService.usuario_pode_gerenciar_evento(self.dono, self.evento))
        self.assertFalse(EventoService.usuario_pode_gerenciar_evento(self.nao_dono, self.evento))

    def test_nao_dono_nao_pode_alterar_informacoes_evento(self):
        """Usuário autenticado que não é dono recebe 403 Forbidden ao tentar atualizar informações."""
        self.client.force_authenticate(user=self.nao_dono)
        url = f'/api/sgie/v1/eventos/{self.evento.id}/'
        resp = self.client.patch(url, {'nome': 'Nome Alterado Ilicitamente'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_dono_nao_pode_mudar_status_evento(self):
        """Usuário autenticado que não é dono recebe 403 Forbidden ao tentar mudar status do evento."""
        self.client.force_authenticate(user=self.nao_dono)

        # Tentar abrir inscrições
        url_abrir = f'/api/sgie/v1/eventos/{self.evento.id}/abrir-inscricoes/'
        resp_abrir = self.client.post(url_abrir)
        self.assertEqual(resp_abrir.status_code, status.HTTP_403_FORBIDDEN)

        # Tentar cancelar
        url_cancelar = f'/api/sgie/v1/eventos/{self.evento.id}/cancelar/'
        resp_cancelar = self.client.post(url_cancelar, {'motivo': 'Motivo indevido'}, format='json')
        self.assertEqual(resp_cancelar.status_code, status.HTTP_403_FORBIDDEN)

        # Tentar finalizar
        url_finalizar = f'/api/sgie/v1/eventos/{self.evento.id}/finalizar/'
        resp_finalizar = self.client.post(url_finalizar)
        self.assertEqual(resp_finalizar.status_code, status.HTTP_403_FORBIDDEN)

    def test_dono_pode_mudar_status_evento(self):
        """Dono do evento consegue realizar as transições regimentais com sucesso."""
        self.client.force_authenticate(user=self.dono)

        # Abrir inscrições
        url_abrir = f'/api/sgie/v1/eventos/{self.evento.id}/abrir-inscricoes/'
        resp_abrir = self.client.post(url_abrir)
        self.assertEqual(resp_abrir.status_code, status.HTTP_200_OK)

        self.evento.refresh_from_db()
        self.assertEqual(self.evento.status, StatusEvento.INSCRICOES_ABERTAS)
