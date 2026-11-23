from django.contrib import admin

from .models import ConfiguracaoIA, CotaUsuarioIA, RequisicaoIA, MensagemAssistente


@admin.register(ConfiguracaoIA)
class ConfiguracaoIAAdmin(admin.ModelAdmin):
    list_display = ('provedor', 'modelo', 'ativo', 'cota_mensal_padrao', 'atualizado_em')
    exclude = ('api_key',)  # chave só pela tela própria


@admin.register(CotaUsuarioIA)
class CotaUsuarioIAAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'habilitado', 'limite_mensal_tokens')
    list_select_related = ('usuario',)


@admin.register(RequisicaoIA)
class RequisicaoIAAdmin(admin.ModelAdmin):
    list_display = ('criado_em', 'usuario', 'origem', 'modelo', 'status', 'total_tokens', 'duracao_ms')
    list_filter = ('status', 'origem', 'provedor')
    list_select_related = ('usuario',)
    readonly_fields = [f.name for f in RequisicaoIA._meta.fields]


@admin.register(MensagemAssistente)
class MensagemAssistenteAdmin(admin.ModelAdmin):
    list_display = ('criado_em', 'usuario', 'papel')
    list_select_related = ('usuario',)
