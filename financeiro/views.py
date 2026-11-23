from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView

from erp.mixins import MensagemCadastroMixin, MensagemExclusaoMixin
from usuarios.mixins import GroupRequiredMixin, DonoRequiredMixin
from vendas.models import FormaPagamento
from .filters import ContaPagarFilter, ContaReceberFilter
from .forms import FornecedorForm, ContaPagarForm, ContaReceberForm
from .models import Fornecedor, ContaPagar, ContaReceber, MovimentoCaixa, StatusConta, TipoMovimentoCaixa

# Mesmo padrão de grupos usado no app vendas.
GRUPOS_GESTAO = ['Administrador', 'Gerente']
PAGINACAO_PADRAO = 10


# ===== FORNECEDORES (cadastro de apoio — igual padrão de Cliente/Categoria) =====

class FornecedorListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Fornecedor
    template_name = 'financeiro/fornecedor_list.html'
    context_object_name = 'fornecedores'
    ordering = ['nome']
    paginate_by = PAGINACAO_PADRAO
    group_required = GRUPOS_GESTAO


class FornecedorCreateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, CreateView):
    success_message = 'Fornecedor "%(nome)s" cadastrado com sucesso!'
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'financeiro/fornecedor_form.html'
    success_url = reverse_lazy('financeiro:fornecedor-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Novo Fornecedor'
        return ctx


class FornecedorUpdateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    success_message = 'Fornecedor "%(nome)s" alterado com sucesso!'
    model = Fornecedor
    form_class = FornecedorForm
    template_name = 'financeiro/fornecedor_form.html'
    success_url = reverse_lazy('financeiro:fornecedor-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Fornecedor'
        return ctx


class FornecedorDeleteView(LoginRequiredMixin, GroupRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = Fornecedor
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('financeiro:fornecedor-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Fornecedor'
        ctx['objeto'] = self.object.nome
        return ctx


# ===== CONTAS A PAGAR / A RECEBER =====
# Requisito: registros associados ao usuário que os cadastrou, e SOMENTE ele
# pode listar, visualizar, alterar e excluir. Isso é garantido pelo
# DonoRequiredMixin (usuarios/mixins.py), que filtra o queryset por
# usuario=request.user em TODAS as views abaixo — acessar o pk de outro
# usuário pela URL devolve 404. A baixa (pagar/receber) segue a mesma regra.


class ContaPagarListView(LoginRequiredMixin, DonoRequiredMixin, FilterView):
    model = ContaPagar
    filterset_class = ContaPagarFilter
    template_name = 'financeiro/conta_pagar_list.html'
    context_object_name = 'contas'
    ordering = ['vencimento']
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        # select_related: o template mostra conta.fornecedor.nome em cada linha (evita N+1).
        return super().get_queryset().select_related('fornecedor')


class ContaPagarDetailView(LoginRequiredMixin, DonoRequiredMixin, DetailView):
    model = ContaPagar
    template_name = 'financeiro/conta_pagar_detail.html'
    context_object_name = 'conta'

    def get_queryset(self):
        return super().get_queryset().select_related('fornecedor', 'usuario')


class ContaPagarCreateView(LoginRequiredMixin, DonoRequiredMixin, MensagemCadastroMixin, CreateView):
    model = ContaPagar
    form_class = ContaPagarForm
    template_name = 'financeiro/conta_pagar_form.html'
    success_url = reverse_lazy('financeiro:conta-pagar-list')
    success_message = 'Conta a pagar "%(descricao)s" lançada com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nova Conta a Pagar'
        return ctx


class ContaPagarUpdateView(LoginRequiredMixin, DonoRequiredMixin, MensagemCadastroMixin, UpdateView):
    model = ContaPagar
    form_class = ContaPagarForm
    template_name = 'financeiro/conta_pagar_form.html'
    success_url = reverse_lazy('financeiro:conta-pagar-list')
    success_message = 'Conta a pagar "%(descricao)s" alterada com sucesso!'

    def get_queryset(self):
        # Só contas pendentes podem ser editadas (e só as do próprio usuário — mixin).
        return super().get_queryset().filter(status=StatusConta.PENDENTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Conta a Pagar'
        return ctx


class ContaPagarDeleteView(LoginRequiredMixin, DonoRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = ContaPagar
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('financeiro:conta-pagar-list')
    success_message = 'Conta a pagar "{objeto}" excluída com sucesso.'

    def get_queryset(self):
        return super().get_queryset().filter(status=StatusConta.PENDENTE).select_related('fornecedor')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Conta a Pagar'
        ctx['objeto'] = self.object.descricao
        return ctx


class ContaPagarBaixarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        conta = get_object_or_404(
            ContaPagar.objects.select_related('fornecedor'), pk=pk, usuario=request.user
        )

        if conta.status == StatusConta.PAGA:
            messages.error(request, 'Esta conta já está paga.')
            return redirect('financeiro:conta-pagar-list')

        forma = request.POST.get('forma_pagamento') or FormaPagamento.DINHEIRO
        if forma not in FormaPagamento.values:
            forma = FormaPagamento.DINHEIRO
        conta.baixar(forma)
        messages.success(request, f'Conta "{conta.descricao}" baixada como paga.')
        return redirect('financeiro:conta-pagar-list')


class ContaReceberListView(LoginRequiredMixin, DonoRequiredMixin, FilterView):
    model = ContaReceber
    filterset_class = ContaReceberFilter
    template_name = 'financeiro/conta_receber_list.html'
    context_object_name = 'contas'
    ordering = ['vencimento']
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related('cliente', 'venda')


class ContaReceberDetailView(LoginRequiredMixin, DonoRequiredMixin, DetailView):
    model = ContaReceber
    template_name = 'financeiro/conta_receber_detail.html'
    context_object_name = 'conta'

    def get_queryset(self):
        return super().get_queryset().select_related('cliente', 'venda', 'usuario')


class ContaReceberCreateView(LoginRequiredMixin, DonoRequiredMixin, MensagemCadastroMixin, CreateView):
    model = ContaReceber
    form_class = ContaReceberForm
    template_name = 'financeiro/conta_receber_form.html'
    success_url = reverse_lazy('financeiro:conta-receber-list')
    success_message = 'Conta a receber "%(descricao)s" lançada com sucesso!'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nova Conta a Receber'
        return ctx


class ContaReceberUpdateView(LoginRequiredMixin, DonoRequiredMixin, MensagemCadastroMixin, UpdateView):
    model = ContaReceber
    form_class = ContaReceberForm
    template_name = 'financeiro/conta_receber_form.html'
    success_url = reverse_lazy('financeiro:conta-receber-list')
    success_message = 'Conta a receber "%(descricao)s" alterada com sucesso!'

    def get_queryset(self):
        return super().get_queryset().filter(status=StatusConta.PENDENTE)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Conta a Receber'
        return ctx


class ContaReceberDeleteView(LoginRequiredMixin, DonoRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = ContaReceber
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('financeiro:conta-receber-list')
    success_message = 'Conta a receber "{objeto}" excluída com sucesso.'

    def get_queryset(self):
        return super().get_queryset().filter(status=StatusConta.PENDENTE).select_related('cliente')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Conta a Receber'
        ctx['objeto'] = self.object.descricao
        return ctx


class ContaReceberBaixarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        conta = get_object_or_404(
            ContaReceber.objects.select_related('cliente'), pk=pk, usuario=request.user
        )

        if conta.status == StatusConta.RECEBIDA:
            messages.error(request, 'Esta conta já está recebida.')
            return redirect('financeiro:conta-receber-list')

        forma = request.POST.get('forma_recebimento') or FormaPagamento.DINHEIRO
        if forma not in FormaPagamento.values:
            forma = FormaPagamento.DINHEIRO
        conta.baixar(forma)
        messages.success(request, f'Conta "{conta.descricao}" baixada como recebida.')
        return redirect('financeiro:conta-receber-list')


# ===== CAIXA (extrato somente leitura, gerado automaticamente) =====

class MovimentoCaixaListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """
    Sem CRUD manual por regra de negócio: os movimentos são criados
    automaticamente quando uma conta é baixada. A view existe apenas
    para consulta/extrato — restrita a Administrador/Gerente.
    """
    model = MovimentoCaixa
    template_name = 'financeiro/caixa_list.html'
    context_object_name = 'movimentos'
    ordering = ['-data']
    paginate_by = PAGINACAO_PADRAO
    group_required = GRUPOS_GESTAO

    def get_queryset(self):
        return super().get_queryset().select_related('usuario')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        agregados = MovimentoCaixa.objects.aggregate(
            entradas=Sum('valor', filter=Q(tipo=TipoMovimentoCaixa.ENTRADA)),
            saidas=Sum('valor', filter=Q(tipo=TipoMovimentoCaixa.SAIDA)),
        )
        entradas = agregados['entradas'] or 0
        saidas = agregados['saidas'] or 0
        ctx['total_entradas'] = entradas
        ctx['total_saidas'] = saidas
        ctx['saldo'] = entradas - saidas
        return ctx
