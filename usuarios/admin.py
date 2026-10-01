from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import CodigoRecuperacao, PapelContextual, PerfilOrganizador, Usuario


class PerfilOrganizadorInline(admin.StackedInline):
    """Permite visualizar e homologar o perfil de organizador diretamente na edição do usuário."""

    model = PerfilOrganizador
    can_delete = False
    extra = 0
    verbose_name = _('Perfil de Organizador')
    verbose_name_plural = _('Perfil de Organizador')
    fields = [
        'homologado',
        'bio_do_organizador',
        'foto_de_perfil',
        'banner',
        'atualizado_em',
    ]
    readonly_fields = ['atualizado_em']


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Administração customizada para o modelo Usuario."""

    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    inlines = [PerfilOrganizadorInline]

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
    actions = ['homologar_como_organizador', 'revogar_homologacao_organizador']

    @admin.action(description=_('Homologar organizador do(s) usuário(s) selecionado(s)'))
    def homologar_como_organizador(self, request, queryset):
        total = 0
        for usuario in queryset:
            perfil, _ = PerfilOrganizador.objects.get_or_create(usuario=usuario)
            if not perfil.homologado:
                perfil.homologado = True
                perfil.save(update_fields=['homologado', 'atualizado_em'])
                total += 1
        self.message_user(request, _('%(count)d usuário(s) homologado(s) como organizador.') % {'count': total})

    @admin.action(description=_('Revogar homologação de organizador do(s) usuário(s) selecionado(s)'))
    def revogar_homologacao_organizador(self, request, queryset):
        atualizados = PerfilOrganizador.objects.filter(usuario__in=queryset, homologado=True).update(homologado=False)
        self.message_user(request, _('%(count)d usuário(s) desomologado(s) com sucesso.') % {'count': atualizados})

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
                    'password1',
                    'password2',
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
    list_display = ['usuario', 'homologado', 'preview_foto', 'atualizado_em']
    list_editable = ['homologado']
    list_filter = ['homologado']
    search_fields = ['usuario__email', 'usuario__cpf', 'usuario__nome_completo', 'bio_do_organizador']
    actions = ['homologar_perfis', 'desomologar_perfis']
    fields = ['usuario', 'homologado', 'bio_do_organizador', 'foto_de_perfil', 'banner', 'atualizado_em']
    readonly_fields = ['atualizado_em']

    @admin.display(description=_('Foto'))
    def preview_foto(self, obj):
        if obj.foto_de_perfil:
            return mark_safe(f'<img src="{obj.foto_de_perfil.url}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover;" />')
        return '—'

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
    list_display = ['id', 'usuario', 'codigo', 'canal', 'tentativas', 'criado_em', 'expira_em', 'utilizado', 'valido_agora']
    list_filter = ['utilizado', 'canal']
    search_fields = ['usuario__email', 'usuario__cpf', 'codigo']
    readonly_fields = ['criado_em', 'expira_em', 'codigo', 'tentativas']

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
