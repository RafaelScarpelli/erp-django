import random
import string

from django.conf import settings
from django.db import models


class StatusNotaFiscal(models.TextChoices):
    EMITIDA = 'EMITIDA', 'Emitida'
    CANCELADA = 'CANCELADA', 'Cancelada'


def gerar_chave_acesso_fake():
    """
    Gera uma 'chave de acesso' de 44 dígitos no MESMO FORMATO de uma chave
    de NFe real, mas 100% simulada/aleatória — não é validada nem enviada
    para nenhum órgão. Serve apenas para dar realismo ao mini-ERP, já que
    a integração real com a SEFAZ está fora do escopo deste projeto.
    """
    return ''.join(random.choices(string.digits, k=44))


class NotaFiscal(models.Model):
    """
    Representação SIMULADA de uma Nota Fiscal eletrônica.

    Não há qualquer integração com a SEFAZ ou webservices fiscais reais:
    a 'emissão' apenas grava um número sequencial e uma chave de acesso
    fake, sem validade jurídica. O objetivo é modelar o fluxo de negócio
    (uma venda finalizada gera uma nota, que pode ser cancelada) sem
    depender de serviços externos.
    """
    venda = models.OneToOneField(
        'vendas.Venda', on_delete=models.PROTECT, related_name='nota_fiscal'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='notas_fiscais'
    )
    numero = models.PositiveIntegerField(unique=True)
    serie = models.CharField(max_length=3, default='1')
    chave_acesso = models.CharField(max_length=44, unique=True, default=gerar_chave_acesso_fake)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=StatusNotaFiscal.choices, default=StatusNotaFiscal.EMITIDA)
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)

    def cancelar(self):
        from django.utils import timezone
        self.status = StatusNotaFiscal.CANCELADA
        self.data_cancelamento = timezone.now()
        self.save()

    @property
    def chave_acesso_formatada(self):
        """Quebra a chave em blocos de 4 dígitos, como no DANFE real."""
        return ' '.join(self.chave_acesso[i:i + 4] for i in range(0, len(self.chave_acesso), 4))

    def __str__(self):
        return f'NF-e nº {self.numero}/{self.serie} — Venda #{self.venda_id}'

    class Meta:
        verbose_name = 'Nota Fiscal'
        verbose_name_plural = 'Notas Fiscais'
        ordering = ['-data_emissao']
