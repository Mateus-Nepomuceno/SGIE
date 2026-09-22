import django.db.models.deletion
import eventos.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Evento",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "nome",
                    models.CharField(
                        help_text="Título com até 100 caracteres e todas as palavras iniciadas em maiúscula.",
                        max_length=100,
                        validators=[eventos.validators.validar_titulo_evento],
                        verbose_name="Nome do Evento",
                    ),
                ),
                (
                    "descricao",
                    models.TextField(
                        help_text="Descrição detalhada do evento sem limite de caracteres.",
                        verbose_name="Descrição",
                    ),
                ),
                (
                    "data",
                    models.DateField(
                        help_text="Data de realização do evento.",
                        verbose_name="Data de Realização",
                    ),
                ),
                (
                    "data_original",
                    models.DateField(
                        blank=True,
                        help_text="Registro histórico da primeira data estipulada para cálculo de prazos de alteração.",
                        null=True,
                        verbose_name="Data Original",
                    ),
                ),
                (
                    "hora_inicio",
                    models.TimeField(
                        help_text="Horário militar previsto para o início (ex: 14:00).",
                        verbose_name="Horário de Início",
                    ),
                ),
                (
                    "hora_inicio_original",
                    models.TimeField(
                        blank=True,
                        help_text="Horário de início estipulado originalmente.",
                        null=True,
                        verbose_name="Horário de Início Original",
                    ),
                ),
                (
                    "hora_fim",
                    models.TimeField(
                        help_text="Horário militar previsto para o término (ex: 18:00).",
                        verbose_name="Horário de Fim",
                    ),
                ),
                (
                    "local_tipo",
                    models.CharField(
                        choices=[
                            ("Auditório", "Auditório"),
                            ("Sala 1", "Sala 1"),
                            ("Laboratório 2", "Laboratório 2"),
                            ("Outro", "Outro"),
                        ],
                        default="Auditório",
                        max_length=50,
                        verbose_name="Tipo de Local",
                    ),
                ),
                (
                    "local",
                    models.CharField(
                        help_text="Descrição do local de realização (ou texto livre para opção Outro).",
                        max_length=255,
                        verbose_name="Local",
                    ),
                ),
                (
                    "modalidade",
                    models.CharField(
                        choices=[
                            ("Presencial", "Presencial"),
                            ("On-line", "On-line"),
                            ("Híbrido", "Híbrido"),
                        ],
                        default="Presencial",
                        max_length=20,
                        verbose_name="Modalidade",
                    ),
                ),
                (
                    "capacidade",
                    models.PositiveIntegerField(
                        help_text="Quantidade máxima de participantes (até 10.000).",
                        validators=[eventos.validators.validar_capacidade],
                        verbose_name="Capacidade Máxima",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Rascunho", "Rascunho"),
                            ("Configuração", "Configuração"),
                            ("Publicado", "Publicado"),
                            ("Inscrições abertas", "Inscrições abertas"),
                            ("Em realização", "Em realização"),
                            ("Finalizado", "Finalizado"),
                            ("Arquivado", "Arquivado"),
                            ("Cancelado", "Cancelado"),
                        ],
                        db_index=True,
                        default="Rascunho",
                        max_length=30,
                        verbose_name="Status",
                    ),
                ),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("Congresso", "Congresso"),
                            ("Simpósio", "Simpósio"),
                            ("Seminário", "Seminário"),
                            ("Feira", "Feira"),
                            ("Conferência", "Conferência"),
                            ("Festival", "Festival"),
                            ("Competição", "Competição"),
                            ("Workshop", "Workshop"),
                            ("Oficina", "Oficina"),
                            ("Curso", "Curso"),
                            ("Mini-curso", "Mini-curso"),
                            ("Palestra", "Palestra"),
                            ("Roda de Conversa", "Roda de Conversa"),
                            ("Treinamento", "Treinamento"),
                            ("Lançamento de Produto", "Lançamento de Produto"),
                            ("Outro", "Outro"),
                        ],
                        default="Congresso",
                        max_length=50,
                        verbose_name="Categoria",
                    ),
                ),
                (
                    "categoria_personalizada",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text='Preenchido quando a categoria selecionada for "Outro".',
                        max_length=100,
                        verbose_name="Categoria Personalizada",
                    ),
                ),
                (
                    "e_gratuito",
                    models.BooleanField(
                        default=True,
                        help_text="Define se o evento é gratuito ou possui cobrança de inscrição.",
                        verbose_name="Gratuito",
                    ),
                ),
                (
                    "preco",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        max_digits=10,
                        verbose_name="Preço da Inscrição (R$)",
                    ),
                ),
                (
                    "visibilidade",
                    models.CharField(
                        choices=[("Público", "Público"), ("Privado", "Privado")],
                        default="Público",
                        max_length=20,
                        verbose_name="Visibilidade",
                    ),
                ),
                (
                    "programacao_geral",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Descrição textual resumida da programação do evento.",
                        verbose_name="Programação Geral",
                    ),
                ),
                (
                    "motivo_cancelamento",
                    models.TextField(
                        blank=True, default="", verbose_name="Motivo do Cancelamento"
                    ),
                ),
                (
                    "cancelado_em",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data/Hora de Cancelamento"
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "usuario_representante",
                    models.ForeignKey(
                        help_text="Usuário organizador responsável pela criação e gestão do evento.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos_representados",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário Representante",
                    ),
                ),
            ],
            options={
                "verbose_name": "Evento",
                "verbose_name_plural": "Eventos",
                "ordering": ["-data", "-hora_inicio"],
            },
        ),
        migrations.CreateModel(
            name="EquipeOrganizadora",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=150, verbose_name="Nome do Organizador"
                    ),
                ),
                (
                    "email_publico",
                    models.EmailField(max_length=254, verbose_name="E-mail Público"),
                ),
                (
                    "papel_funcao",
                    models.CharField(
                        blank=True,
                        default="Organizador",
                        max_length=100,
                        verbose_name="Função na Organização",
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizadores",
                        to="eventos.evento",
                        verbose_name="Evento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Integrante da Equipe Organizadora",
                "verbose_name_plural": "Integrantes da Equipe Organizadora",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="RegraSubmissao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "aceita_submissao",
                    models.BooleanField(
                        default=False, verbose_name="Aceita Submissão de Trabalhos"
                    ),
                ),
                (
                    "data_hora_inicio",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Início do Período de Submissão",
                    ),
                ),
                (
                    "data_hora_fim",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Fim do Período de Submissão",
                    ),
                ),
                (
                    "evento",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="regra_submissao",
                        to="eventos.evento",
                        verbose_name="Evento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Regra de Submissão",
                "verbose_name_plural": "Regras de Submissão",
            },
        ),
    ]
