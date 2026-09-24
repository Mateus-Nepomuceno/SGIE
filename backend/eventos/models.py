from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import (
    validar_capacidade,
    validar_titulo_evento,
)


class Modalidade(models.TextChoices):

    PRESENCIAL = 'Presencial', _('Presencial')
    ONLINE = 'On-line', _('On-line')
    HIBRIDO = 'Híbrido', _('Híbrido')


class LocalTipo(models.TextChoices):

    AUDITORIO = 'Auditório', _('Auditório')
    SALA_1 = 'Sala 1', _('Sala 1')
    LABORATORIO_2 = 'Laboratório 2', _('Laboratório 2')
    OUTRO = 'Outro', _('Outro')


class CategoriaEvento(models.TextChoices):

    CONGRESSO = 'Congresso', _('Congresso')
    SIMPOSIO = 'Simpósio', _('Simpósio')
    SEMINARIO = 'Seminário', _('Seminário')
    FEIRA = 'Feira', _('Feira')
    CONFERENCIA = 'Conferência', _('Conferência')
    FESTIVAL = 'Festival', _('Festival')
    COMPETICAO = 'Competição', _('Competição')
    WORKSHOP = 'Workshop', _('Workshop')
    OFICINA = 'Oficina', _('Oficina')
    CURSO = 'Curso', _('Curso')
    MINI_CURSO = 'Mini-curso', _('Mini-curso')
    PALESTRA = 'Palestra', _('Palestra')
    RODA_DE_CONVERSA = 'Roda de Conversa', _('Roda de Conversa')
    TREINAMENTO = 'Treinamento', _('Treinamento')
    LANCAMENTO_DE_PRODUTO = 'Lançamento de Produto', _('Lançamento de Produto')
    OUTRO = 'Outro', _('Outro')


CATEGORIAS_CURTA_DURACAO = {
    CategoriaEvento.OFICINA.value,
    CategoriaEvento.MINI_CURSO.value,
    CategoriaEvento.PALESTRA.value,
    CategoriaEvento.RODA_DE_CONVERSA.value,
    CategoriaEvento.TREINAMENTO.value,
    CategoriaEvento.LANCAMENTO_DE_PRODUTO.value,
}


class StatusEvento(models.TextChoices):

    RASCUNHO = 'Rascunho', _('Rascunho')
    CONFIGURACAO = 'Configuração', _('Configuração')
    PUBLICADO = 'Publicado', _('Publicado')
    INSCRICOES_ABERTAS = 'Inscrições abertas', _('Inscrições abertas')
    EM_REALIZACAO = 'Em realização', _('Em realização')
    FINALIZADO = 'Finalizado', _('Finalizado')
    ARQUIVADO = 'Arquivado', _('Arquivado')
    CANCELADO = 'Cancelado', _('Cancelado')


class VisibilidadeEvento(models.TextChoices):

    PUBLICO = 'Público', _('Público')
    PRIVADO = 'Privado', _('Privado')


class Evento(models.Model):

    id = models.BigAutoField(primary_key=True)

    usuario_representante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='eventos_representados',
        verbose_name=_('Usuário Representante'),
        help_text=_('Usuário organizador responsável pela criação e gestão do evento.'),
    )

    nome = models.CharField(
        _('Nome do Evento'),
        max_length=100,
        validators=[validar_titulo_evento],
        help_text=_('Título com até 100 caracteres e todas as palavras iniciadas em maiúscula.'),
    )

    descricao = models.TextField(
        _('Descrição'),
        help_text=_('Descrição detalhada do evento sem limite de caracteres.'),
    )

    data = models.DateField(
        _('Data de Realização'),
        help_text=_('Data de realização do evento.'),
    )

    data_original = models.DateField(
        _('Data Original'),
        null=True,
        blank=True,
        help_text=_('Registro histórico da primeira data estipulada para cálculo de prazos de alteração.'),
    )

    hora_inicio = models.TimeField(
        _('Horário de Início'),
        help_text=_('Horário militar previsto para o início (ex: 14:00).'),
    )

    hora_inicio_original = models.TimeField(
        _('Horário de Início Original'),
        null=True,
        blank=True,
        help_text=_('Horário de início estipulado originalmente.'),
    )

    hora_fim = models.TimeField(
        _('Horário de Fim'),
        help_text=_('Horário militar previsto para o término (ex: 18:00).'),
    )

    local_tipo = models.CharField(
        _('Tipo de Local'),
        max_length=50,
        choices=LocalTipo.choices,
        default=LocalTipo.AUDITORIO,
    )

    local = models.CharField(
        _('Local'),
        max_length=255,
        help_text=_('Descrição do local de realização (ou texto livre para opção Outro).'),
    )

    modalidade = models.CharField(
        _('Modalidade'),
        max_length=20,
        choices=Modalidade.choices,
        default=Modalidade.PRESENCIAL,
    )

    capacidade = models.PositiveIntegerField(
        _('Capacidade Máxima'),
        validators=[validar_capacidade],
        help_text=_('Quantidade máxima de participantes (até 10.000).'),
    )

    status = models.CharField(
        _('Status'),
        max_length=30,
        choices=StatusEvento.choices,
        default=StatusEvento.RASCUNHO,
        db_index=True,
    )

    categoria = models.CharField(
        _('Categoria'),
        max_length=50,
        choices=CategoriaEvento.choices,
        default=CategoriaEvento.CONGRESSO,
    )

    categoria_personalizada = models.CharField(
        _('Categoria Personalizada'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Preenchido quando a categoria selecionada for "Outro".'),
    )

    e_gratuito = models.BooleanField(
        _('Gratuito'),
        default=True,
        help_text=_('Define se o evento é gratuito ou possui cobrança de inscrição.'),
    )

    necessita_comprovante = models.BooleanField(
        _('Comprovante'),
        default=False,
        help_text=_('Define se o evento necessita ou não de comprovante'),
    )

    preco = models.DecimalField(
        _('Preço da Inscrição (R$)'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )

    visibilidade = models.CharField(
        _('Visibilidade'),
        max_length=20,
        choices=VisibilidadeEvento.choices,
        default=VisibilidadeEvento.PUBLICO,
    )

    programacao_geral = models.TextField(
        _('Programação Geral'),
        blank=True,
        default='',
        help_text=_('Descrição textual resumida da programação do evento.'),
    )

    motivo_cancelamento = models.TextField(
        _('Motivo do Cancelamento'),
        blank=True,
        default='',
    )

    cancelado_em = models.DateTimeField(
        _('Data/Hora de Cancelamento'),
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Evento')
        verbose_name_plural = _('Eventos')
        ordering = ['-data', '-hora_inicio']

    def __str__(self) -> str:
        return f'{self.nome} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.data_original and self.data:
            self.data_original = self.data
        if not self.hora_inicio_original and self.hora_inicio:
            self.hora_inicio_original = self.hora_inicio
        if self.local_tipo != LocalTipo.OUTRO and not self.local.strip():
            self.local = self.get_local_tipo_display()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.nome:
            validar_titulo_evento(self.nome)

        if self.capacidade is not None:
            validar_capacidade(self.capacidade)

        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError(
                {'hora_fim': _('O horário de fim deve ser estritamente posterior ao horário de início.')}
            )

        if not self.e_gratuito and self.preco <= 0:
            raise ValidationError(
                {'preco': _('Eventos pagos devem possuir valor de inscrição superior a R$ 0,00.')}
            )

        if self.e_gratuito and self.preco != 0:
            self.preco = 0.00

        if self.categoria == CategoriaEvento.OUTRO and not self.categoria_personalizada.strip():
            raise ValidationError(
                {'categoria_personalizada': _('Informe a categoria personalizada quando selecionar a opção "Outro".')}
            )

        if self.local_tipo == LocalTipo.OUTRO and not self.local.strip():
            raise ValidationError(
                {'local': _('Informe a descrição do local quando selecionar a opção "Outro".')}
            )

    @property
    def data_inicio_completa(self) -> datetime:
        dt = datetime.combine(self.data, self.hora_inicio)
        tz = timezone.get_current_timezone()
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, tz)
        return dt

    @property
    def data_fim_completa(self) -> datetime:
        dt = datetime.combine(self.data, self.hora_fim)
        tz = timezone.get_current_timezone()
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, tz)
        return dt

    @property
    def data_original_inicio_completa(self) -> datetime:
        data_base = self.data_original or self.data
        hora_base = self.hora_inicio_original or self.hora_inicio
        dt = datetime.combine(data_base, hora_base)
        tz = timezone.get_current_timezone()
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, tz)
        return dt

    @property
    def is_curta_duracao(self) -> bool:
        return self.categoria in CATEGORIAS_CURTA_DURACAO

    @property
    def limite_encerramento_inscricoes(self) -> datetime:
        return self.data_inicio_completa - timedelta(minutes=15)

    @property
    def inscricoes_abertas_status(self) -> bool:
        if self.status not in {StatusEvento.PUBLICADO, StatusEvento.INSCRICOES_ABERTAS}:
            return False
        agora = timezone.now()
        return agora < self.limite_encerramento_inscricoes

    @property
    def limite_alteracao_data(self) -> datetime:
        return self.data_original_inicio_completa - timedelta(days=7)

    @property
    def limite_alteracao_detalhes(self) -> datetime:
        return self.data_inicio_completa - timedelta(hours=1)

    @property
    def limite_cancelamento(self) -> datetime:
        if self.is_curta_duracao:
            return self.data_inicio_completa - timedelta(hours=1)
        return self.data_original_inicio_completa - timedelta(days=7)

    def pode_alterar_data(self) -> bool:
        if self.status in {StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO}:
            return True
        if self.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            return False
        return timezone.now() <= self.limite_alteracao_data

    def pode_alterar_detalhes(self) -> bool:
        if self.status in {StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO}:
            return True
        if self.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            return False
        return timezone.now() <= self.limite_alteracao_detalhes

    def pode_cancelar(self) -> bool:
        if self.status in {StatusEvento.FINALIZADO, StatusEvento.ARQUIVADO, StatusEvento.CANCELADO}:
            return False
        if self.status in {StatusEvento.RASCUNHO, StatusEvento.CONFIGURACAO}:
            return True
        return timezone.now() <= self.limite_cancelamento


class EquipeOrganizadora(models.Model):

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='organizadores',
        verbose_name=_('Evento'),
    )
    nome = models.CharField(_('Nome do Organizador'), max_length=150)
    email_publico = models.EmailField(_('E-mail Público'))
    papel_funcao = models.CharField(
        _('Função na Organização'),
        max_length=100,
        blank=True,
        default='Organizador',
    )

    class Meta:
        verbose_name = _('Integrante da Equipe Organizadora')
        verbose_name_plural = _('Integrantes da Equipe Organizadora')
        ordering = ['nome']

    def __str__(self) -> str:
        return f'{self.nome} ({self.email_publico}) - Evento {self.evento_id}'


class RegraSubmissao(models.Model):

    evento = models.OneToOneField(
        Evento,
        on_delete=models.CASCADE,
        related_name='regra_submissao',
        verbose_name=_('Evento'),
    )
    aceita_submissao = models.BooleanField(
        _('Aceita Submissão de Trabalhos'),
        default=False,
    )
    data_hora_inicio = models.DateTimeField(
        _('Início do Período de Submissão'),
        null=True,
        blank=True,
    )
    data_hora_fim = models.DateTimeField(
        _('Fim do Período de Submissão'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Regra de Submissão')
        verbose_name_plural = _('Regras de Submissão')

    def __str__(self) -> str:
        status_txt = 'Aceita' if self.aceita_submissao else 'Não aceita'
        return f'Submissão ({status_txt}) - Evento {self.evento_id}'

    def clean(self):
        super().clean()
        if self.aceita_submissao:
            if not self.data_hora_inicio or not self.data_hora_fim:
                raise ValidationError(
                    _('Eventos que aceitam submissão de trabalhos devem obrigatoriamente possuir data/hora de início e término.')
                )
            if self.data_hora_fim <= self.data_hora_inicio:
                raise ValidationError(
                    {'data_hora_fim': _('A data e horário de fim das submissões deve ser posterior ao início.')}
                )

    @property
    def periodo_aberto(self) -> bool:
        if not self.aceita_submissao or not self.data_hora_inicio or not self.data_hora_fim:
            return False
        agora = timezone.now()
        return self.data_hora_inicio <= agora <= self.data_hora_fim
