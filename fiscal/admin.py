from django.contrib import admin

from .models import NotaFiscal


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ('numero', 'serie', 'venda', 'valor_total', 'status', 'data_emissao')
    list_filter = ('status',)
    search_fields = ('numero', 'chave_acesso')
    readonly_fields = ('chave_acesso', 'data_emissao', 'data_cancelamento')
