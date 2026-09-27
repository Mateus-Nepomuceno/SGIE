from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TipoSubmissao(models.TextChoices):

    ARTIGO = 'Artigo', _('Artigo')
    PALESTRA = 'Palestra', _('Palestra')
    MINICURSO = 'Minicurso', _('Minicurso')
    POSTER = 'Poster', _('Poster')
    OUTRO = 'Outro', _('Outro')


class StatusSubmissao(models.TextChoices):

    RASCUNHO = 'Rascunho', _('Rascunho')
    SUBMETIDA = 'Submetida', _('Submetida')
    EM_AVALIACAO = 'Em avaliação', _('Em avaliação')
    CORRECOES_SOLICITADAS = 'Correções solicitadas', _('Correções solicitadas')
    APROVADA = 'Aprovada', _('Aprovada')
    REJEITADA = 'Rejeitada', _('Rejeitada')


class TipoParticipacaoAutor(models.TextChoices):

    PRINCIPAL = 'Principal', _('Principal')
    COAUTOR = 'Coautor', _('Coautor')


class StatusParecer(models.TextChoices):

    APROVADO = 'Aprovado', _('Aprovado')
    REJEITADO = 'Rejeitado', _('Rejeitado')
    NECESSITA_CORRECAO = 'Necessita correção', _('Necessita correção')


class Area(models.Model):

    id = models.BigAutoField(primary_key=True)

    nome = models.CharField(
        _('Nome da Área'),
        max_length=150,
        unique=True,
    )

    descricao = models.TextField(
        _('Descrição'),
        blank=True,
        default='',
        help_text=_('Descrição detalhada da área temática.'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Área Temática')
        verbose_name_plural = _('Áreas Temáticas')
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome


class Submissao(models.Model):

    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='submissoes',
        verbose_name=_('Evento'),
        help_text=_('Evento para o qual o trabalho é submetido.'),
    )

    autor_principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissoes_como_autor',
        verbose_name=_('Autor Principal'),
        help_text=_('Usuário responsável pela submissão do trabalho.'),
    )

    area = models.ForeignKey(
        Area,
        on_delete=models.PROTECT,
        related_name='submissoes',
        verbose_name=_('Área Temática'),
        help_text=_('Área temática de classificação do trabalho.'),
    )

    titulo = models.CharField(
        _('Título'),
        max_length=300,
        help_text=_('Título do trabalho acadêmico.'),
    )

    descricao = models.TextField(
        _('Descrição'),
        blank=True,
        default='',
        help_text=_('Descrição adicional sobre o trabalho.'),
    )

    abstract = models.TextField(
        _('Abstract'),
        help_text=_('Resumo em inglês ou português conforme normas do evento.'),
    )

    resumo = models.TextField(
        _('Resumo'),
        blank=True,
        default='',
        help_text=_('Resumo executivo do trabalho.'),
    )

    palavras_chave = models.CharField(
        _('Palavras-chave'),
        max_length=500,
        help_text=_('Palavras-chave separadas por vírgula.'),
    )

    tipo = models.CharField(
        _('Tipo de Submissão'),
        max_length=50,
        choices=TipoSubmissao.choices,
        default=TipoSubmissao.ARTIGO,
    )

    status = models.CharField(
        _('Status'),
        max_length=30,
        choices=StatusSubmissao.choices,
        default=StatusSubmissao.RASCUNHO,
        db_index=True,
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Submissão')
        verbose_name_plural = _('Submissões')
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['evento', 'status']),
            models.Index(fields=['autor_principal', 'status']),
            models.Index(fields=['area', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.titulo} ({self.get_status_display()})'

    def clean(self):
        super().clean()

        if self.tipo == TipoSubmissao.OUTRO and hasattr(self, 'tipo_personalizado'):
            if not getattr(self, 'tipo_personalizado', '').strip():
                raise ValidationError(
                    {'tipo_personalizado': _('Informe o tipo personalizado quando selecionar "Outro".')}
                )

        if self.status == StatusSubmissao.SUBMETIDA and not self.versoes.exists():
            raise ValidationError(
                _('Uma submissão não pode ser submetida sem um arquivo anexado.')
            )

    @property
    def pode_editar(self) -> bool:
        """Verifica se a submissão pode ser editada."""
        return self.status in {StatusSubmissao.RASCUNHO, StatusSubmissao.CORRECOES_SOLICITADAS}

    @property
    def pode_submeter(self) -> bool:
        """Verifica se a submissão pode ser finalizada e submetida."""
        if self.status not in {StatusSubmissao.RASCUNHO, StatusSubmissao.CORRECOES_SOLICITADAS}:
            return False
        
        regra_submissao = getattr(self.evento, 'regra_submissao', None)
        if not regra_submissao or not regra_submissao.aceita_submissao:
            return False
        
        agora = timezone.now()
        if regra_submissao.data_hora_inicio and regra_submissao.data_hora_fim:
            return regra_submissao.data_hora_inicio <= agora <= regra_submissao.data_hora_fim
        
        return False


class SubmissaoAutor(models.Model):

    id = models.BigAutoField(primary_key=True)

    submissao = models.ForeignKey(
        Submissao,
        on_delete=models.CASCADE,
        related_name='autores',
        verbose_name=_('Submissão'),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissoes_como_coautor',
        verbose_name=_('Usuário'),
    )

    tipo_participacao = models.CharField(
        _('Tipo de Participação'),
        max_length=20,
        choices=TipoParticipacaoAutor.choices,
        default=TipoParticipacaoAutor.COAUTOR,
    )

    ordem_autoria = models.PositiveIntegerField(
        _('Ordem de Autoria'),
        null=True,
        blank=True,
        help_text=_('Ordem de aparição nos certificados e documentos.')
    )

    lattes_url = models.URLField(
        _('Currículo Lattes'),
        max_length=500,
        blank=True,
        default='',
        help_text=_('URL do currículo Lattes do autor.'),
    )

    linkedin_url = models.URLField(
        _('Perfil LinkedIn'),
        max_length=500,
        blank=True,
        default='',
        help_text=_('URL do perfil LinkedIn do autor.'),
    )

    afiliacao_institucional = models.CharField(
        _('Afiliação Institucional'),
        max_length=255,
        blank=True,
        default='',
        help_text=_('Universidade ou instituição de vínculo.'),
    )

    maiór_titulacao = models.CharField(
        _('Maior Titulação'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Grau acadêmico do autor (e.g., Mestrado, Doutorado).'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Autor de Submissão')
        verbose_name_plural = _('Autores de Submissão')
        ordering = ['ordem_autoria', 'criado_em']
        unique_together = [['submissao', 'usuario']]

    def __str__(self) -> str:
        nome = getattr(self.usuario, 'nome_completo', None) or (
            self.usuario.get_full_name() if hasattr(self.usuario, 'get_full_name') else str(self.usuario)
        )
        return f'{nome} ({self.get_tipo_participacao_display()}) - {self.submissao.titulo}'


class SubmissaoVersao(models.Model):

    id = models.BigAutoField(primary_key=True)

    submissao = models.ForeignKey(
        Submissao,
        on_delete=models.CASCADE,
        related_name='versoes',
        verbose_name=_('Submissão'),
    )

    numero_versao = models.PositiveIntegerField(
        _('Número da Versão'),
        help_text=_('Número sequencial de versão (1 para original, 2 para revisado, etc).'),
    )

    caminho_arquivo = models.FileField(
        _('Arquivo'),
        upload_to='submissoes/%Y/%m/',
        help_text=_('Arquivo PDF ou DOCX enviado nesta versão.'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('Versão de Submissão')
        verbose_name_plural = _('Versões de Submissão')
        ordering = ['numero_versao']
        unique_together = [['submissao', 'numero_versao']]

    def __str__(self) -> str:
        return f'{self.submissao.titulo} (v{self.numero_versao})'


class Avaliacao(models.Model):

    id = models.BigAutoField(primary_key=True)

    submissao = models.ForeignKey(
        Submissao,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        verbose_name=_('Submissão'),
    )

    avaliador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='avaliacoes_realizadas',
        verbose_name=_('Avaliador'),
    )

    status_parecer = models.CharField(
        _('Status do Parecer'),
        max_length=30,
        choices=StatusParecer.choices,
        default=StatusParecer.NECESSITA_CORRECAO,
    )

    observacoes = models.TextField(
        _('Observações'),
        help_text=_('Feedback detalhado e observações dos revisores para o autor.'),
    )

    pontuacao = models.DecimalField(
        _('Pontuação'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Nota consolidada dos critérios técnicos.'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Avaliação')
        verbose_name_plural = _('Avaliações')
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['submissao', 'status_parecer']),
            models.Index(fields=['avaliador', 'status_parecer']),
        ]

    def __str__(self) -> str:
        avaliador_nome = (
            getattr(self.avaliador, 'nome_completo', None)
            or (self.avaliador.get_full_name() if hasattr(self.avaliador, 'get_full_name') else str(self.avaliador))
            if self.avaliador else 'Sem avaliador'
        )
        return f'Parecer de {avaliador_nome} - {self.submissao.titulo}'

    def clean(self):
        super().clean()

        if not self.observacoes.strip():
            raise ValidationError(
                {'observacoes': _('As observações são obrigatórias para emitir um parecer.')}
            )

        if self.status_parecer == StatusParecer.NECESSITA_CORRECAO and self.pontuacao is None:
            raise ValidationError(
                {'pontuacao': _('A pontuação é obrigatória quando se solicita correção.')}
            )


class Local(models.Model):

    id = models.BigAutoField(primary_key=True)

    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='locais_apresentacao',
        verbose_name=_('Evento'),
    )

    nome = models.CharField(
        _('Nome do Local'),
        max_length=150,
    )

    descricao = models.TextField(
        _('Descrição'),
        blank=True,
        default='',
        help_text=_('Descrição das características do local.'),
    )

    capacidade = models.PositiveIntegerField(
        _('Capacidade'),
        null=True,
        blank=True,
        help_text=_('Número máximo de pessoas que o local pode acomodar.'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Local de Apresentação')
        verbose_name_plural = _('Locais de Apresentação')
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome


class Apresentacao(models.Model):

    id = models.BigAutoField(primary_key=True)

    submissao = models.ForeignKey(
        Submissao,
        on_delete=models.CASCADE,
        related_name='apresentacoes',
        verbose_name=_('Submissão'),
    )

    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        related_name='apresentacoes',
        verbose_name=_('Local'),
    )

    inicio = models.DateTimeField(
        _('Data e Horário de Início'),
        help_text=_('Data e horário agendado para a apresentação.'),
    )

    duracao_minutos = models.PositiveIntegerField(
        _('Duração (minutos)'),
        help_text=_('Duração estimada da apresentação em minutos.'),
    )

    criado_em = models.DateTimeField(_('Criado em'), auto_now_add=True)
    atualizado_em = models.DateTimeField(_('Atualizado em'), auto_now=True)

    class Meta:
        verbose_name = _('Apresentação')
        verbose_name_plural = _('Apresentações')
        ordering = ['inicio']
        indexes = [
            models.Index(fields=['local', 'inicio']),
            models.Index(fields=['submissao', 'inicio']),
        ]

    def __str__(self) -> str:
        return f'{self.submissao.titulo} - {self.local.nome} ({self.inicio.strftime("%d/%m/%Y %H:%M")})'

    def clean(self):
        super().clean()

        if self.duracao_minutos <= 0:
            raise ValidationError(
                {'duracao_minutos': _('A duração deve ser maior que zero.')}
            )

        if self.submissao.status != StatusSubmissao.APROVADA:
            raise ValidationError(
                _('Apenas submissões aprovadas podem ter apresentações agendadas.')
            )

        sobreposicoes = Apresentacao.objects.filter(
            local=self.local,
            inicio__lte=self.inicio,
            apresentacoes__gt=self.inicio - models.F('duracao_minutos'),
        ).exclude(pk=self.pk)

        if sobreposicoes.exists():
            raise ValidationError(
                _('Conflito de horário: outro trabalho já está agendado neste local neste horário.')
            )

    @property
    def fim(self) -> models.DateTimeField:
        """Calcula o horário de término da apresentação."""
        from datetime import timedelta
        return self.inicio + timedelta(minutes=self.duracao_minutos)


