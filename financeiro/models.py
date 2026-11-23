from django.conf import settings
from django.db import models
from django.utils import timezone

from vendas.models import FormaPagamento


class StatusConta(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    PAGA     = 'PAGA',     'Paga'
    RECEBIDA = 'RECEBIDA', 'Recebida'


class TipoMovimentoCaixa(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    SAIDA   = 'SAIDA',   'Saída'


class Fornecedor(models.Model):
    nome     = models.CharField(max_length=255)
    cnpj     = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    email    = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']


class ContaPagar(models.Model):
    fornecedor      = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name='contas_pagar')
    usuario         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='contas_pagar_lancadas'
    )
    descricao       = models.CharField(max_length=255)
    valor           = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento      = models.DateField()
    data_pagamento  = models.DateField(null=True, blank=True)
    forma_pagamento = models.CharField(max_length=20, choices=FormaPagamento.choices, blank=True)
    status          = models.CharField(max_length=10, choices=StatusConta.choices, default=StatusConta.PENDENTE)

    def baixar(self, forma_pagamento):
        """Marca a conta como paga e gera o movimento de caixa correspondente (saída)."""
        self.status = StatusConta.PAGA
        self.data_pagamento = timezone.localdate()
        self.forma_pagamento = forma_pagamento
        self.save()
        MovimentoCaixa.objects.create(
            tipo=TipoMovimentoCaixa.SAIDA,
            valor=self.valor,
            origem=f'Pagamento — {self.descricao} ({self.fornecedor.nome})',
            usuario=self.usuario,
        )

    @property
    def atrasada(self):
        return self.status == StatusConta.PENDENTE and self.vencimento < timezone.localdate()

    def __str__(self):
        return f'{self.descricao} — R$ {self.valor} ({self.fornecedor.nome})'

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['vencimento']


class ContaReceber(models.Model):
    cliente          = models.ForeignKey('vendas.Cliente', on_delete=models.PROTECT, related_name='contas_receber')
    venda            = models.ForeignKey(
        'vendas.Venda', on_delete=models.SET_NULL, null=True, blank=True, related_name='contas_receber'
    )
    usuario          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='contas_receber_lancadas'
    )
    descricao        = models.CharField(max_length=255)
    valor            = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento       = models.DateField()
    data_recebimento = models.DateField(null=True, blank=True)
    forma_recebimento = models.CharField(max_length=20, choices=FormaPagamento.choices, blank=True)
    status           = models.CharField(max_length=10, choices=StatusConta.choices, default=StatusConta.PENDENTE)

    def baixar(self, forma_recebimento):
        """Marca a conta como recebida e gera o movimento de caixa correspondente (entrada)."""
        self.status = StatusConta.RECEBIDA
        self.data_recebimento = timezone.localdate()
        self.forma_recebimento = forma_recebimento
        self.save()
        MovimentoCaixa.objects.create(
            tipo=TipoMovimentoCaixa.ENTRADA,
            valor=self.valor,
            origem=f'Recebimento — {self.descricao} ({self.cliente.nome})',
            usuario=self.usuario,
        )

    @property
    def atrasada(self):
        return self.status == StatusConta.PENDENTE and self.vencimento < timezone.localdate()

    def __str__(self):
        return f'{self.descricao} — R$ {self.valor} ({self.cliente.nome})'

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['vencimento']


class MovimentoCaixa(models.Model):
    """
    Gerado automaticamente ao baixar uma ContaPagar/ContaReceber — não existe
    CRUD manual por regra de negócio (mesmo padrão de MovimentacaoEstoque no
    app vendas): serve apenas para consulta/extrato do caixa.
    """
    tipo    = models.CharField(max_length=10, choices=TipoMovimentoCaixa.choices)
    valor   = models.DecimalField(max_digits=10, decimal_places=2)
    data    = models.DateTimeField(auto_now_add=True)
    origem  = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='movimentos_caixa'
    )

    def __str__(self):
        return f'{self.tipo} — R$ {self.valor} — {self.origem}'

    class Meta:
        verbose_name = 'Movimento de Caixa'
        verbose_name_plural = 'Movimentos de Caixa'
        ordering = ['-data']
