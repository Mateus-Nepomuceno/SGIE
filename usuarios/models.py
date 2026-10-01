from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import ModeloUUID

from .validators import formatar_cpf, limpar_cpf, validar_cpf, validar_extensao_imagem

MAX_TENTATIVAS_CODIGO = 3


class UsuarioManager(BaseUserManager):
    """
    Gerenciador customizado para a entidade Usuario.
    Obriga a definição de e-mail e CPF como identificadores fundamentais (RN01).
    """

    def create_user(self, email, cpf, nome_completo, data_nascimento, telefone, password=None, **extra_fields):  # noqa: PLR0913, PLR0917
        if not email:
            raise ValueError(_('O endereço de e-mail é obrigatório.'))
        if not cpf:
            raise ValueError(_('O CPF é obrigatório.'))
        if not nome_completo:
            raise ValueError(_('O nome completo é obrigatório.'))
        if not data_nascimento:
            raise ValueError(_('A data de nascimento é obrigatória.'))
        if not telefone:
            raise ValueError(_('O número de telefone é obrigatório.'))

        email = self.normalize_email(email).lower().strip()
        cpf = limpar_cpf(cpf)

        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        user = self.model(
            email=email,
            cpf=cpf,
            nome_completo=nome_completo.strip(),
            data_nascimento=data_nascimento,
            telefone=telefone.strip(),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, cpf, nome_completo, data_nascimento, telefone, password=None, **extra_fields):  # noqa: PLR0913, PLR0917
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superusuário deve possuir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superusuário deve possuir is_superuser=True.'))

        return self.create_user(
            email=email,
            cpf=cpf,
            nome_completo=nome_completo,
            data_nascimento=data_nascimento,
            telefone=telefone,
            password=password,
            **extra_fields,
        )


class Usuario(AbstractBaseUser, PermissionsMixin, ModeloUUID):
    """
    Modelo Customizado de Usuário do SGIE (substitui django.contrib.auth.models.User).
    Atende aos requisitos RF01, RF02, RN01 e RN06. Herda chave primária UUID de ModeloUUID.
    """

    nome_completo = models.CharField(_('Nome Completo'), max_length=150)
    email = models.EmailField(_('E-mail'), max_length=254, unique=True, db_index=True)
    cpf = models.CharField(_('CPF'), max_length=14, unique=True, db_index=True, validators=[validar_cpf])
    data_nascimento = models.DateField(_('Data de Nascimento'))
    telefone = models.CharField(_('Telefone'), max_length=20)
    is_active = models.BooleanField(_('Ativo'), default=True)
    is_staff = models.BooleanField(_('Acesso Admin'), default=False)
    is_superuser = models.BooleanField(_('Superusuário'), default=False)
    date_joined = models.DateTimeField(_('Data de Cadastro'), default=timezone.now)
    last_login = models.DateTimeField(_('Último Acesso'), null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo', 'cpf', 'data_nascimento', 'telefone']

    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['id']

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()
        if self.cpf:
            validar_cpf(self.cpf)
            self.cpf = limpar_cpf(self.cpf)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        if self.cpf:
            self.cpf = limpar_cpf(self.cpf)
        super().save(*args, **kwargs)

    @property
    def cpf_formatado(self) -> str:
        """Retorna o CPF formatado para visualização amigável."""
        return formatar_cpf(self.cpf)

    def has_role(self, evento_id: int, papel: str) -> bool:
        """Verifica se o usuário possui determinado papel ativo em um evento específico (RN03, RN05)."""
        if not self.is_active:
            return False
        try:
            ev_id = int(evento_id)
        except (ValueError, TypeError):
            return False
        return self.papeis_contextuais.filter(
            evento_id=ev_id,
            papel=papel,
            ativo=True,
        ).exists()

    def is_organizador(self) -> bool:
        """
        Verifica se o usuário está qualificado para atuar como Organizador/Criador de eventos (RN04).
        Superusuários ativos possuem permissão implícita.
        """
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        perfil = getattr(self, 'perfil_organizador', None)
        return bool(perfil and perfil.homologado)

    def __str__(self) -> str:
        return f'{self.nome_completo} ({self.email})'


class PerfilOrganizador(ModeloUUID):
    """
    Armazena dados adicionais para promoção de usuários a Organizadores (RF04, RN04).
    Herda chave primária UUID de ModeloUUID.
    """

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_organizador',
        verbose_name=_('Usuário'),
    )
    foto_de_perfil = models.ImageField(
        _('Foto de Perfil'),
        upload_to='organizadores/fotos/',
        null=True,
        blank=True,
        validators=[validar_extensao_imagem],
    )
    banner = models.ImageField(
        _('Banner Visual'),
        upload_to='organizadores/banners/',
        null=True,
        blank=True,
        validators=[validar_extensao_imagem],
    )
    bio_do_organizador = models.TextField(
        _('Mini-biografia do Organizador'),
        max_length=1000,
        blank=True,
        default='',
    )
    homologado = models.BooleanField(_('Homologado para Criar Eventos'), default=False)
    atualizado_em = models.DateTimeField(_('Última Atualização'), auto_now=True)

    class Meta:
        verbose_name = _('Perfil de Organizador')
        verbose_name_plural = _('Perfis de Organizadores')

    def __str__(self) -> str:
        return f'Perfil Organizador - {self.usuario.nome_completo}'


class CodigoRecuperacao(ModeloUUID):
    """
    Código temporário de 6 dígitos gerado para recuperação de acesso (RF03).
    Expira em 15 minutos e possui uso único. Herda chave primária UUID de ModeloUUID.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='codigos_recuperacao',
        verbose_name=_('Usuário'),
    )
    codigo = models.CharField(_('Código de Verificação'), max_length=6)
    canal = models.CharField(_('Canal de Envio'), max_length=20, default='EMAIL')
    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    expira_em = models.DateTimeField(_('Expira em'))
    utilizado = models.BooleanField(_('Utilizado'), default=False)
    tentativas = models.PositiveSmallIntegerField(_('Tentativas Incorretas'), default=0)

    class Meta:
        verbose_name = _('Código de Recuperação')
        verbose_name_plural = _('Códigos de Recuperação')
        indexes = [
            models.Index(fields=['usuario', 'codigo', 'utilizado']),
        ]

    def __str__(self) -> str:
        return f'Código {self.codigo} ({self.usuario.email})'

    def save(self, *args, **kwargs):
        if not self.expira_em:
            self.expira_em = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valido(self) -> bool:
        """Verifica se o código não foi consumido, não excedeu tentativas e ainda está no período de validade."""
        if self.utilizado or self.tentativas >= MAX_TENTATIVAS_CODIGO:
            return False
        return timezone.now() <= self.expira_em

    def marcar_como_usado(self) -> None:
        """Invalida o código marcando-o como utilizado."""
        self.utilizado = True
        self.save(update_fields=['utilizado'])


class Papel(models.TextChoices):
    """Enumeração de papéis contextuais aceitos pelo SGIE (RF06, RN03, RN05)."""

    PARTICIPANTE = 'PARTICIPANTE', _('Participante')
    AUTOR = 'AUTOR', _('Autor')
    AVALIADOR = 'AVALIADOR', _('Avaliador')
    ORGANIZADOR = 'ORGANIZADOR', _('Organizador')
    PALESTRANTE = 'PALESTRANTE', _('Palestrante')
    VOLUNTARIO = 'VOLUNTARIO', _('Voluntário')
    SUPORTE = 'SUPORTE', _('Suporte')


class PapelContextual(ModeloUUID):
    """
    Tabela associativa para suportar a multiplicidade de papéis de um usuário por evento (RN03, RN05).
    Herda chave primária UUID de ModeloUUID.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='papeis_contextuais',
        verbose_name=_('Usuário'),
    )
    evento_id = models.PositiveBigIntegerField(_('ID do Evento'), db_index=True)
    papel = models.CharField(
        _('Papel'),
        max_length=20,
        choices=Papel.choices,
        default=Papel.PARTICIPANTE,
    )
    ativo = models.BooleanField(_('Ativo'), default=True)
    atribuido_em = models.DateTimeField(_('Atribuído em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Papel Contextual')
        verbose_name_plural = _('Papéis Contextuais')
        unique_together = ('usuario', 'evento_id', 'papel')

    def __str__(self) -> str:
        return f'{self.usuario.nome_completo} - {self.get_papel_display()} (Evento {self.evento_id})'
