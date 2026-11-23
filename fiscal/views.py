from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView

from usuarios.mixins import is_gerencial
from vendas.models import Venda, StatusVenda
from .models import NotaFiscal, StatusNotaFiscal

PAGINACAO_PADRAO = 10


class NotaFiscalListView(LoginRequiredMixin, ListView):
    """
    Lista as notas fiscais. Vendedor comum só vê as notas das vendas que
    ele mesmo registrou; Administrador/Gerente veem todas (mesma regra
    aplicada em Venda, já que NotaFiscal depende diretamente dela).
    """
    model = NotaFiscal
    template_name = 'fiscal/nota_list.html'
    context_object_name = 'notas'
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        qs = NotaFiscal.objects.select_related('venda', 'venda__cliente', 'usuario')
        if not is_gerencial(self.request.user):
            qs = qs.filter(venda__usuario=self.request.user)
        return qs


class NotaFiscalDetailView(LoginRequiredMixin, DetailView):
    model = NotaFiscal
    template_name = 'fiscal/nota_detail.html'
    context_object_name = 'nota'

    def get_queryset(self):
        qs = NotaFiscal.objects.select_related('venda', 'venda__cliente', 'usuario').prefetch_related(
            'venda__itens__produto'
        )
        if not is_gerencial(self.request.user):
            qs = qs.filter(venda__usuario=self.request.user)
        return qs


class NotaFiscalEmitirView(LoginRequiredMixin, View):
    """
    'Emite' (simula) a nota fiscal de uma venda. Não existe formulário:
    a nota é gerada automaticamente a partir dos dados da venda, como
    aconteceria numa integração real com a SEFAZ — aqui só sem a parte
    de integração de verdade.
    """

    def post(self, request, venda_pk):
        vendas_qs = Venda.objects.all()
        if not is_gerencial(request.user):
            vendas_qs = vendas_qs.filter(usuario=request.user)
        venda = get_object_or_404(vendas_qs, pk=venda_pk)

        if venda.status == StatusVenda.CANCELADA:
            messages.error(request, 'Não é possível emitir nota fiscal de uma venda cancelada.')
            return redirect('vendas:venda-detail', pk=venda.pk)

        if hasattr(venda, 'nota_fiscal'):
            messages.error(request, f'A Venda #{venda.pk} já possui a Nota Fiscal nº {venda.nota_fiscal.numero}.')
            return redirect('fiscal:nota-detail', pk=venda.nota_fiscal.pk)

        with transaction.atomic():
            ultimo_numero = NotaFiscal.objects.aggregate(m=Max('numero'))['m'] or 0
            nota = NotaFiscal.objects.create(
                venda=venda,
                usuario=request.user,
                numero=ultimo_numero + 1,
                valor_total=venda.valor_total,
            )

        messages.success(request, f'Nota Fiscal nº {nota.numero} emitida (simulada) com sucesso!')
        return redirect('fiscal:nota-detail', pk=nota.pk)


class NotaFiscalCancelarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        qs = NotaFiscal.objects.all()
        if not is_gerencial(request.user):
            qs = qs.filter(venda__usuario=request.user)
        nota = get_object_or_404(qs, pk=pk)

        if nota.status == StatusNotaFiscal.CANCELADA:
            messages.error(request, 'Esta nota fiscal já está cancelada.')
            return redirect('fiscal:nota-detail', pk=pk)

        nota.cancelar()
        messages.success(request, f'Nota Fiscal nº {nota.numero} cancelada.')
        return redirect('fiscal:nota-detail', pk=pk)
