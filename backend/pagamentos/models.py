import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import ModeloUUID


class StatusCobranca(models.TextChoices):
    PENDENTE = 'PENDENTE', _('Pendente')
    PAGA = 'PAGA', _('Paga')
    CANCELADA = 'CANCELADA', _('Cancelada')
    EXPIRADA = 'EXPIRADA', _('Expirada')


class StatusPagamento(models.TextChoices):
    """
    Ciclo de vida do pagamento conforme diagrama_de_estados_de_pagamento.md:
    Pendente -> Processando -> Aprovado / Recusado -> Cancelado / Reembolsado.
    """

    PENDENTE = 'PENDENTE', _('Pendente')
    PROCESSANDO = 'PROCESSANDO', _('Processando')
    APROVADO = 'APROVADO', _('Aprovado')
    RECUSADO = 'RECUSADO', _('Recusado')
    CANCELADO = 'CANCELADO', _('Cancelado')
    REEMBOLSADO = 'REEMBOLSADO', _('Reembolsado')


class StatusReembolso(models.TextChoices):
    SOLICITADO = 'SOLICITADO', _('Solicitado')
    PROCESSANDO = 'PROCESSANDO', _('Processando')
    CONCLUIDO = 'CONCLUIDO', _('Concluído')
    RECUSADO = 'RECUSADO', _('Recusado')


class TipoIsencao(models.TextChoices):
    TOTAL = 'TOTAL', _('Total')
    PARCIAL = 'PARCIAL', _('Parcial')


class MetodoPagamento(models.TextChoices):
    PIX = 'PIX', _('Pix')
    CARTAO_CREDITO = 'CARTAO_CREDITO', _('Cartão de Crédito')
    CARTAO_DEBITO = 'CARTAO_DEBITO', _('Cartão de Débito')
    BOLETO = 'BOLETO', _('Boleto Bancário')


class Canal(models.TextChoices):
    EMAIL = 'EMAIL', _('E-mail')
    SMS = 'SMS', _('SMS')
    WHATSAPP = 'WHATSAPP', _('WhatsApp')


class CategoriaPreco(ModeloUUID):
    """
    Agrupa as regras de precificação baseadas no evento.
    Relacionamento: Sistema_de_Eventos -> CategoriaPreco
    """

    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='categorias_preco',
        verbose_name=_('Evento'),
    )
    nome = models.CharField(
        _('Nome da Categoria'),
        max_length=100,
        help_text=_('Ex: Estudante, Profissional, Geral, VIP'),
    )
    descricao = models.TextField(
        _('Descrição'),
        blank=True,
        default='',
    )
    ativo = models.BooleanField(
        _('Ativo'),
        default=True,
    )
    criado_em = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Categoria de Preço')
        verbose_name_plural = _('Categorias de Preço')
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.evento.nome})'


class Lote(ModeloUUID):
    """
    Representa a disponibilidade e controle de vagas para uma determinada categoria de preço.
    Relacionamento: CategoriaPreco -> Lote
    """

    categoria_preco = models.ForeignKey(
        CategoriaPreco,
        on_delete=models.CASCADE,
        related_name='lotes',
        verbose_name=_('Categoria de Preço'),
    )
    nome = models.CharField(
        _('Nome do Lote'),
        max_length=100,
        help_text=_('Ex: 1º Lote, Lote Promocional'),
    )
    numero = models.PositiveIntegerField(
        _('Número do Lote'),
        default=1,
    )
    preco = models.DecimalField(
        _('Preço'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    quantidade_total = models.PositiveIntegerField(
        _('Quantidade Total'),
        validators=[MinValueValidator(1)],
    )
    quantidade_disponivel = models.PositiveIntegerField(
        _('Quantidade Disponível'),
        help_text=_('Quantidade de inscrições disponíveis restantes neste lote'),
    )
    data_inicio = models.DateTimeField(
        _('Data de Início da Vigência'),
    )
    data_fim = models.DateTimeField(
        _('Data de Término da Vigência'),
    )
    ativo = models.BooleanField(
        _('Ativo'),
        default=True,
    )
    criado_em = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Lote')
        verbose_name_plural = _('Lotes')
        ordering = ['numero', 'data_inicio']

    def __str__(self):
        return f'{self.nome} - {self.categoria_preco.nome} (R$ {self.preco})'

    def save(self, *args, **kwargs):
        if self.quantidade_disponivel is None and self.quantidade_total is not None:
            self.quantidade_disponivel = self.quantidade_total
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.data_inicio and self.data_fim and self.data_inicio >= self.data_fim:
            raise ValidationError({'data_fim': _('A data de término deve ser posterior à data de início.')})

        if self.quantidade_disponivel is not None and self.quantidade_total is not None and self.quantidade_disponivel > self.quantidade_total:
            raise ValidationError({'quantidade_disponivel': _('A quantidade disponível não pode ser maior do que a quantidade total.')})

    @property
    def esta_vigente(self):
        agora = timezone.now()
        return self.ativo and self.data_inicio <= agora <= self.data_fim

    @property
    def tem_vagas(self):
        return self.quantidade_disponivel > 0


class Cobranca(ModeloUUID):
    """
    Classe central de faturamento.
    Relacionamento: Sistema_de_Inscricoes -> Cobranca
    Gera Pagamento e possui IsencaoPagamento.
    """

    inscricao = models.ForeignKey(
        'inscricao.Inscricao',
        on_delete=models.CASCADE,
        related_name='cobrancas',
        verbose_name=_('Inscrição'),
    )
    lote = models.ForeignKey(
        Lote,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cobrancas',
        verbose_name=_('Lote Aplicado'),
    )
    valor_original = models.DecimalField(
        _('Valor Original'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    valor_final = models.DecimalField(
        _('Valor Final'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    status = models.CharField(
        _('Status da Cobrança'),
        max_length=20,
        choices=StatusCobranca.choices,
        default=StatusCobranca.PENDENTE,
    )
    data_vencimento = models.DateTimeField(
        _('Data de Vencimento'),
    )
    criado_em = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Cobrança')
        verbose_name_plural = _('Cobranças')
        ordering = ['-criado_em']

    def __str__(self):
        return f'Cobrança #{self.id} - Inscrição #{self.inscricao_id} ({self.status})'

    @property
    def esta_vencida(self):
        return self.status == StatusCobranca.PENDENTE and timezone.now() > self.data_vencimento


class IsencaoPagamento(ModeloUUID):
    """
    Define regras ou registros de isenção aplicados a uma cobrança.
    TOTAL: cobrança integralmente dispensada.
    PARCIAL: permanece saldo a pagar.
    """

    cobranca = models.OneToOneField(
        Cobranca,
        on_delete=models.CASCADE,
        related_name='isencao',
        verbose_name=_('Cobrança'),
    )
    tipo = models.CharField(
        _('Tipo de Isenção'),
        max_length=20,
        choices=TipoIsencao.choices,
        default=TipoIsencao.TOTAL,
    )
    desconto_percentual = models.DecimalField(
        _('Desconto Percentual (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        blank=True,
    )
    desconto_valor = models.DecimalField(
        _('Valor do Desconto (R$)'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
    )
    motivo = models.TextField(
        _('Motivo / Justificativa'),
        help_text=_('Justificativa para a concessão da isenção ou abatimento.'),
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='isencoes_concedidas',
        verbose_name=_('Aprovado por'),
    )
    criado_em = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Isenção de Pagamento')
        verbose_name_plural = _('Isenções de Pagamento')
        ordering = ['-criado_em']

    def __str__(self):
        return f'Isenção {self.tipo} - Cobrança #{self.cobranca_id}'

    def clean(self):
        super().clean()
        if self.tipo == TipoIsencao.PARCIAL:
            if (not self.desconto_percentual or self.desconto_percentual <= Decimal('0.00')) and (not self.desconto_valor or self.desconto_valor <= Decimal('0.00')):
                raise ValidationError(_('Para isenção parcial, informe um percentual ou valor de desconto válido.'))

    def aplicar_a_cobranca(self):
        """
        Calcula e ajusta o valor final da cobrança vinculada.
        """
        cobranca = self.cobranca
        if self.tipo == TipoIsencao.TOTAL:
            cobranca.valor_final = Decimal('0.00')
            cobranca.status = StatusCobranca.PAGA
        elif self.tipo == TipoIsencao.PARCIAL:
            if self.desconto_valor and self.desconto_valor > Decimal('0.00'):
                cobranca.valor_final = max(Decimal('0.00'), cobranca.valor_original - self.desconto_valor)
            elif self.desconto_percentual and self.desconto_percentual > Decimal('0.00'):
                abatimento = (cobranca.valor_original * self.desconto_percentual) / Decimal('100.00')
                cobranca.valor_final = max(Decimal('0.00'), cobranca.valor_original - abatimento)

            if cobranca.valor_final == Decimal('0.00'):
                cobranca.status = StatusCobranca.PAGA
        cobranca.save()


class Pagamento(ModeloUUID):
    """
    Representa a transação financeira propriamente dita.
    Gerenciado pelo ServicoPagamento com intermédio de GatewayPagamento.
    Pode gerar 0..1 Reembolso.
    """

    TRANSICOES_VALIDAS = {
        StatusPagamento.PENDENTE: {StatusPagamento.PROCESSANDO, StatusPagamento.CANCELADO},
        StatusPagamento.PROCESSANDO: {StatusPagamento.APROVADO, StatusPagamento.RECUSADO},
        StatusPagamento.APROVADO: {StatusPagamento.CANCELADO, StatusPagamento.REEMBOLSADO},
        StatusPagamento.RECUSADO: set(),
        StatusPagamento.CANCELADO: set(),
        StatusPagamento.REEMBOLSADO: set(),
    }

    cobranca = models.ForeignKey(
        Cobranca,
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name=_('Cobrança'),
    )
    valor = models.DecimalField(
        _('Valor'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    metodo = models.CharField(
        _('Método de Pagamento'),
        max_length=20,
        choices=MetodoPagamento.choices,
    )
    status = models.CharField(
        _('Status do Pagamento'),
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
    )
    transacao_id = models.CharField(
        _('ID da Transação'),
        max_length=255,
        blank=True,
        default='',
        db_index=True,
        help_text=_('Código retornado pelo Gateway/PSP'),
    )
    gateway_nome = models.CharField(
        _('Gateway / PSP'),
        max_length=50,
        blank=True,
        default='',
    )
    detalhes_processamento = models.JSONField(
        _('Detalhes do Processamento'),
        default=dict,
        blank=True,
        help_text=_('Retorno e metadados da transação fornecidos pelo gateway'),
    )
    qr_code_pix = models.TextField(
        _('Payload Copia e Cola / QR Code Pix'),
        blank=True,
        default='',
    )
    url_pagamento = models.URLField(
        _('URL de Redirecionamento / Boleto'),
        max_length=500,
        blank=True,
        default='',
    )
    data_criacao = models.DateTimeField(
        _('Data de Criação'),
        auto_now_add=True,
    )
    data_pagamento = models.DateTimeField(
        _('Data de Confirmação do Pagamento'),
        null=True,
        blank=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamentos')
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Pagamento #{self.id} - R$ {self.valor} ({self.status})'

    def pode_transicionar_para(self, novo_status):
        """
        Valida se a mudança de estado respeita o diagrama de estados de pagamento.
        """
        destinos_permitidos = self.TRANSICOES_VALIDAS.get(self.status, set())
        return novo_status in destinos_permitidos

    def atualizar_status(self, novo_status, transacao_id=None, detalhes=None):
        """
        Aplica transição de estado validada.
        """
        if novo_status != self.status and not self.pode_transicionar_para(novo_status):
            raise ValidationError(
                _('Transição de status inválida: de %(atual)s para %(novo)s.'),
                params={'atual': self.status, 'novo': novo_status},
            )

        self.status = novo_status
        if transacao_id:
            self.transacao_id = transacao_id
        if detalhes:
            self.detalhes_processamento = detalhes
        if novo_status == StatusPagamento.APROVADO and not self.data_pagamento:
            self.data_pagamento = timezone.now()
        self.save()


class Reembolso(ModeloUUID):
    """
    Representa a devolução de um pagamento.
    Relacionamento: Pagamento 1 -> 0..1 Reembolso
    """

    pagamento = models.OneToOneField(
        Pagamento,
        on_delete=models.CASCADE,
        related_name='reembolso',
        verbose_name=_('Pagamento'),
    )
    valor = models.DecimalField(
        _('Valor do Reembolso'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    motivo = models.TextField(
        _('Motivo do Reembolso'),
    )
    status = models.CharField(
        _('Status do Reembolso'),
        max_length=20,
        choices=StatusReembolso.choices,
        default=StatusReembolso.SOLICITADO,
    )
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reembolsos_solicitados',
        verbose_name=_('Solicitado por'),
    )
    analisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reembolsos_avaliados',
        verbose_name=_('Analisado por'),
    )
    transacao_reembolso_id = models.CharField(
        _('ID do Reembolso no Gateway'),
        max_length=255,
        blank=True,
        default='',
    )
    data_solicitacao = models.DateTimeField(
        _('Data da Solicitação'),
        auto_now_add=True,
    )
    data_conclusao = models.DateTimeField(
        _('Data de Conclusão'),
        null=True,
        blank=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Reembolso')
        verbose_name_plural = _('Reembolsos')
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'Reembolso #{self.id} - Pagamento #{self.pagamento_id} ({self.status})'

    def clean(self):
        super().clean()
        if self.pagamento_id and self.valor and self.valor > self.pagamento.valor:
            raise ValidationError({'valor': _('O valor do reembolso não pode ser superior ao valor do pagamento original.')})


class Certificado(ModeloUUID):
    """
    Representa o documento de participação.
    O certificado só é disponibilizado quando a inscrição atende às condições de participação.
    A presença é controlada pelo módulo de Inscrições/Participantes.
    """

    inscricao = models.OneToOneField(
        'inscricao.Inscricao',
        on_delete=models.CASCADE,
        related_name='certificado',
        verbose_name=_('Inscrição'),
    )
    codigo_autenticacao = models.CharField(
        _('Código de Autenticação'),
        max_length=100,
        unique=True,
        db_index=True,
        default=uuid.uuid4,
    )
    arquivo = models.FileField(
        _('Arquivo do Certificado (PDF)'),
        upload_to='certificados/',
        null=True,
        blank=True,
    )
    disponivel = models.BooleanField(
        _('Disponível para Emissão'),
        default=False,
        help_text=_('Habilitado quando cumpridas as condições de participação e confirmação de presença.'),
    )
    carga_horaria = models.PositiveIntegerField(
        _('Carga Horária (horas)'),
        default=0,
    )
    emitido_em = models.DateTimeField(
        _('Emitido em'),
        auto_now_add=True,
    )
    atualizado_em = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('Certificado')
        verbose_name_plural = _('Certificados')
        ordering = ['-emitido_em']

    def __str__(self):
        return f'Certificado {self.codigo_autenticacao} - Inscrição #{self.inscricao_id}'


class Comunicacao(ModeloUUID):
    """
    Gerencia envios ou notificações pós-evento para os participantes.
    Certificado fornece destinatários para Comunicação.
    """

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comunicacoes_recebidas',
        verbose_name=_('Destinatário'),
    )
    certificado = models.ForeignKey(
        Certificado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comunicacoes',
        verbose_name=_('Certificado Relacionado'),
    )
    canal = models.CharField(
        _('Canal'),
        max_length=20,
        choices=Canal.choices,
        default=Canal.EMAIL,
    )
    assunto = models.CharField(
        _('Assunto'),
        max_length=255,
    )
    mensagem = models.TextField(
        _('Mensagem'),
    )
    enviado = models.BooleanField(
        _('Enviado'),
        default=False,
    )
    data_envio = models.DateTimeField(
        _('Data de Envio'),
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _('Comunicação')
        verbose_name_plural = _('Comunicações')
        ordering = ['-criado_em']

    def __str__(self):
        return f'Comunicação ({self.canal}) para {self.destinatario} - {self.assunto}'
