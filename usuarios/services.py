import logging
import secrets
from datetime import timedelta
from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import CodigoRecuperacao, PapelContextual, PerfilOrganizador, Usuario

logger = logging.getLogger(__name__)


class UsuarioService:
    """
    Camada de Serviços do Módulo de Usuários.
    Isola a lógica de negócio, integrações externas e RBAC contextual para consumo interno e por outras Squads.
    """

    @staticmethod
    def cadastrar_usuario(  # noqa: PLR0913, PLR0917
        nome_completo: str,
        email: str,
        cpf: str,
        data_nascimento,
        telefone: str,
        password: str,
        **extra_fields,
    ) -> Usuario:
        """Cria e persiste um novo usuário no banco de dados com senha criptografada (RF01, RN01)."""
        return Usuario.objects.create_user(
            email=email,
            cpf=cpf,
            nome_completo=nome_completo,
            data_nascimento=data_nascimento,
            telefone=telefone,
            password=password,
            **extra_fields,
        )

    @staticmethod
    def autenticar_usuario(request, identificador: str, senha: str) -> Optional[Usuario]:
        """Autentica usuário utilizando o backend híbrido por e-mail ou CPF (RF02)."""
        return authenticate(request, identificador=identificador, password=senha)

    @staticmethod
    def gerar_codigo_recuperacao(email: str) -> bool:
        """
        Gera um código aleatório seguro de 6 dígitos com expiração de 15 minutos (RF03).
        Retorna True mesmo se o e-mail não existir para evitar enumeração de contas.
        """
        email_limpo = str(email).lower().strip()
        usuario = Usuario.objects.filter(email__iexact=email_limpo, is_active=True).first()

        if not usuario:
            return True

        codigo_gerado = f'{secrets.randbelow(900000) + 100000}'
        expira_em = timezone.now() + timedelta(minutes=15)

        with transaction.atomic():
            # Invalida códigos anteriores não utilizados deste usuário
            CodigoRecuperacao.objects.filter(usuario=usuario, utilizado=False).update(utilizado=True)
            CodigoRecuperacao.objects.create(
                usuario=usuario,
                codigo=codigo_gerado,
                canal='EMAIL',
                expira_em=expira_em,
            )

        assunto = 'SGIE - Código para Recuperação de Senha'
        mensagem = f'Olá, {usuario.nome_completo}.\n\nSeu código de verificação para redefinição de senha no SGIE é: {codigo_gerado}\n\nEste código possui validade de 15 minutos e consumo único.\nCaso você não tenha solicitado esta alteração, ignore esta mensagem.'
        remetente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sgie@universidade.edu.br')

        try:
            send_mail(
                subject=assunto,
                message=mensagem,
                from_email=remetente,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
        except Exception as exc:
            logger.warning('Falha no envio de e-mail de recuperação para %s: %s', usuario.email, exc)

        return True

    @staticmethod
    def redefinir_senha_com_codigo(email: str, codigo: str, nova_senha: str) -> bool:
        """Valida o código de 6 dígitos e aplica a nova senha criptografada (RF03)."""
        email_limpo = str(email).lower().strip()
        usuario = Usuario.objects.filter(email__iexact=email_limpo, is_active=True).first()

        if not usuario:
            raise ValidationError(_('Código de verificação inválido ou expirado.'), code='codigo_invalido')

        codigo_registro = (
            CodigoRecuperacao.objects
            .filter(
                usuario=usuario,
                codigo=str(codigo).strip(),
                utilizado=False,
            )
            .order_by('-criado_em')
            .first()
        )

        if not codigo_registro or not codigo_registro.is_valido():
            raise ValidationError(_('Código de verificação inválido ou expirado.'), code='codigo_invalido')

        with transaction.atomic():
            usuario.set_password(nova_senha)
            usuario.save(update_fields=['password'])
            codigo_registro.marcar_como_usado()

        return True

    @staticmethod
    def atualizar_perfil_organizador(
        usuario: Usuario,
        foto_de_perfil=None,
        banner=None,
        bio_do_organizador: Optional[str] = None,
        homologado: Optional[bool] = None,
    ) -> PerfilOrganizador:
        """Atualiza ou cria o perfil estendido para qualificá-lo a Organizador (RF04, RN04)."""
        perfil, criado = PerfilOrganizador.objects.get_or_create(usuario=usuario)

        campos_atualizados = []
        if foto_de_perfil is not None:
            perfil.foto_de_perfil = foto_de_perfil
            campos_atualizados.append('foto_de_perfil')
        if banner is not None:
            perfil.banner = banner
            campos_atualizados.append('banner')
        if bio_do_organizador is not None:
            perfil.bio_do_organizador = bio_do_organizador.strip()
            campos_atualizados.append('bio_do_organizador')
        if homologado is not None:
            perfil.homologado = homologado
            campos_atualizados.append('homologado')

        if campos_atualizados and not criado:
            perfil.save(update_fields=campos_atualizados + ['atualizado_em'])
        else:
            perfil.save()
        return perfil

    @staticmethod
    def obter_dados_cadastrais(usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Contrato público de fornecimento de dados para outros módulos (RN06).
        Consumido por Gestão de Eventos, Inscrições, Certificados e Financeiro.
        """
        usuario = Usuario.objects.filter(pk=usuario_id, is_active=True).first()
        if not usuario:
            return None

        return {
            'id': usuario.id,
            'nome_completo': usuario.nome_completo,
            'email': usuario.email,
            'cpf': usuario.cpf_formatado,
            'cpf_limpo': usuario.cpf,
            'data_nascimento': usuario.data_nascimento.isoformat() if usuario.data_nascimento else None,
            'telefone': usuario.telefone,
            'is_organizador': usuario.is_organizador(),
        }

    @staticmethod
    def verificar_papel_evento(
        usuario_ou_id: Union[Usuario, int],
        evento_id: int,
        papel_esperado: Optional[str] = None,
        papel: Optional[str] = None,
    ) -> bool:
        """
        Verifica se o usuário possui determinado papel em um evento específico (RN03, RN05).
        Utilizado pelos módulos de Submissão (Autor) e Avaliação (Avaliador).
        """
        papel_alvo = papel_esperado or papel
        if not papel_alvo:
            return False

        usuario_id = usuario_ou_id.id if isinstance(usuario_ou_id, Usuario) else usuario_ou_id
        return PapelContextual.objects.filter(
            usuario_id=usuario_id,
            evento_id=evento_id,
            papel=papel_alvo,
            ativo=True,
        ).exists()

    @staticmethod
    def atribuir_papel_evento(
        usuario_ou_id: Union[Usuario, int],
        evento_id: int,
        papel: str,
        ativo: bool = True,
    ) -> PapelContextual:
        """Concede ou atualiza papel contextual de um usuário em determinado evento (RN02, RN03)."""
        usuario = usuario_ou_id if isinstance(usuario_ou_id, Usuario) else Usuario.objects.get(pk=usuario_ou_id)

        papel_obj, _ = PapelContextual.objects.update_or_create(
            usuario=usuario,
            evento_id=evento_id,
            papel=papel,
            defaults={'ativo': ativo},
        )
        return papel_obj

    @staticmethod
    def is_organizador_homologado(usuario_ou_id: Union[Usuario, int]) -> bool:
        """Verifica se o usuário tem permissão para criar e gerir novos eventos (RF05, RN04)."""
        usuario = usuario_ou_id if isinstance(usuario_ou_id, Usuario) else Usuario.objects.filter(pk=usuario_ou_id).first()
        if not usuario:
            return False
        return usuario.is_organizador()
