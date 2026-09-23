from django.contrib import admin
from .models import Inscricao

@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'evento', 'status', 'data_inscricao')
    list_filter = ('status', 'evento', 'data_inscricao')
    search_fields = ('usuario__email', 'usuario__first_name', 'evento__titulo')
    readonly_fields = ('data_inscricao',)
    list_select_related = ('usuario', 'evento')

    actions = ['marcar_como_pago', 'cancelar_inscricao']

    @admin.action(description='Marcar inscrições selecionadas como Pagas')
    def marcar_como_pago(self, request, queryset):
        queryset.update(status='confirmada')

    @admin.action(description='Cancelar inscrições selecionadas')
    def cancelar_inscricao(self, request, queryset):
        queryset.update(status='cancelada')
