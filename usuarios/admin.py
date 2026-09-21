from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CodigoRecuperacao, PapelContextual, PerfilOrganizador, Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administração customizada para o modelo Usuario."""

    list_display = [
        'id',
        'email',
        'cpf',
        'nome_completo',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_organizador_status',
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'cpf', 'nome_completo']
    ordering = ['id']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Dados Pessoais'), {'fields': ('nome_completo', 'cpf', 'data_nascimento', 'telefone')}),
        (
            _('Permissões'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        (_('Datas Importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'cpf',
                    'nome_completo',
                    'data_nascimento',
                    'telefone',
                    'password',
                ),
            },
        ),
    )

    @admin.display(description=_('Organizador Homologado'), boolean=True)
    @staticmethod
    def is_organizador_status(obj: Usuario) -> bool:
        return obj.is_organizador()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('perfil_organizador')


@admin.register(PerfilOrganizador)
class PerfilOrganizadorAdmin(admin.ModelAdmin):
    """Administração dos perfis de organizador com ação de homologação rápida."""

    list_select_related = ['usuario']
    list_display = ['id', 'usuario', 'homologado', 'atualizado_em']
    list_filter = ['homologado']
    search_fields = ['usuario__email', 'usuario__cpf', 'usuario__nome_completo']
    actions = ['homologar_perfis', 'desomologar_perfis']

    @admin.action(description=_('Homologar organizadores selecionados'))
    def homologar_perfis(self, request, queryset):
        atualizados = queryset.update(homologado=True)
        self.message_user(request, _('%(count)d perfil(is) homologado(s) com sucesso.') % {'count': atualizados})

    @admin.action(description=_('Revogar homologação dos organizadores selecionados'))
    def desomologar_perfis(self, request, queryset):
        atualizados = queryset.update(homologado=False)
        self.message_user(request, _('%(count)d perfil(is) desomologado(s) com sucesso.') % {'count': atualizados})


@admin.register(CodigoRecuperacao)
class CodigoRecuperacaoAdmin(admin.ModelAdmin):
    """Administração dos códigos de recuperação emitidos."""

    list_select_related = ['usuario']
    list_display = ['id', 'usuario', 'codigo', 'canal', 'criado_em', 'expira_em', 'utilizado', 'valido_agora']
    list_filter = ['utilizado', 'canal']
    search_fields = ['usuario__email', 'usuario__cpf', 'codigo']
    readonly_fields = ['criado_em', 'expira_em', 'codigo']

    @admin.display(description=_('Válido no Momento'), boolean=True)
    @staticmethod
    def valido_agora(obj: CodigoRecuperacao) -> bool:
        return obj.is_valido()


@admin.register(PapelContextual)
class PapelContextualAdmin(admin.ModelAdmin):
    """Administração de papéis contextuais associados a eventos."""

    list_select_related = ['usuario']
    list_display = ['id', 'usuario', 'evento_id', 'papel', 'ativo', 'atribuido_em']
    list_filter = ['papel', 'ativo', 'evento_id']
    search_fields = ['usuario__email', 'usuario__cpf', 'usuario__nome_completo']
