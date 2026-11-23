from django.contrib import admin

from .models import Fornecedor, ContaPagar, ContaReceber, MovimentoCaixa


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'telefone', 'email')
    search_fields = ('nome', 'cnpj')


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'fornecedor', 'valor', 'vencimento', 'status')
    list_filter = ('status',)


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'cliente', 'valor', 'vencimento', 'status')
    list_filter = ('status',)


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'valor', 'origem', 'data', 'usuario')
    list_filter = ('tipo',)
    readonly_fields = ('data',)
