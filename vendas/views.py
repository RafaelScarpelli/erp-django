from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django_filters.views import FilterView

from erp.mixins import MensagemCadastroMixin, MensagemExclusaoMixin
from usuarios.mixins import GroupRequiredMixin, is_gerencial
from .filters import ClienteFilter, ProdutoFilter, VendaFilter
from .models import Cliente, Produto, Venda, Categoria, ItemVenda, MovimentacaoEstoque, TipoMovimentacao, StatusVenda
from .forms import ClienteForm, ProdutoForm, VendaForm, CategoriaForm

# Grupos com visão/gestão completa dos cadastros (produtos, categorias, clientes).
# Vendedores enxergam essas listas (precisam delas para vender), mas não podem
# criar/editar/excluir cadastros.
GRUPOS_GESTAO = ['Administrador', 'Gerente']

PAGINACAO_PADRAO = 10


# ===== CLIENTES =====

class ClienteListView(LoginRequiredMixin, FilterView):
    model = Cliente
    filterset_class = ClienteFilter
    template_name = 'vendas/cliente_list.html'
    context_object_name = 'clientes'
    ordering = ['nome']
    paginate_by = PAGINACAO_PADRAO


class ClienteCreateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, CreateView):
    success_message = 'Cliente "%(nome)s" cadastrado com sucesso!'
    model = Cliente
    form_class = ClienteForm
    template_name = 'vendas/cliente_form.html'
    success_url = reverse_lazy('vendas:cliente-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Novo Cliente'
        return ctx


class ClienteUpdateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    success_message = 'Cliente "%(nome)s" alterado com sucesso!'
    model = Cliente
    form_class = ClienteForm
    template_name = 'vendas/cliente_form.html'
    success_url = reverse_lazy('vendas:cliente-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Cliente'
        return ctx


class ClienteDeleteView(LoginRequiredMixin, GroupRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = Cliente
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('vendas:cliente-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Cliente'
        ctx['objeto'] = self.object.nome
        return ctx


# ===== PRODUTOS =====

class ProdutoListView(LoginRequiredMixin, FilterView):
    model = Produto
    filterset_class = ProdutoFilter
    template_name = 'vendas/produto_list.html'
    context_object_name = 'produtos'
    ordering = ['nome']
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related('categoria')


class ProdutoCreateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, CreateView):
    success_message = 'Produto "%(nome)s" cadastrado com sucesso!'
    model = Produto
    form_class = ProdutoForm
    template_name = 'vendas/produto_form.html'
    success_url = reverse_lazy('vendas:produto-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Novo Produto'
        return ctx


class ProdutoUpdateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    success_message = 'Produto "%(nome)s" alterado com sucesso!'
    model = Produto
    form_class = ProdutoForm
    template_name = 'vendas/produto_form.html'
    success_url = reverse_lazy('vendas:produto-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Produto'
        return ctx


class ProdutoDeleteView(LoginRequiredMixin, GroupRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = Produto
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('vendas:produto-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Produto'
        ctx['objeto'] = self.object.nome
        return ctx


# ===== CATEGORIAS =====

class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'vendas/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['nome']
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().annotate(total_produtos=Count('produtos'))


class CategoriaCreateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, CreateView):
    success_message = 'Categoria "%(nome)s" cadastrada com sucesso!'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'vendas/categoria_form.html'
    success_url = reverse_lazy('vendas:categoria-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nova Categoria'
        return ctx


class CategoriaUpdateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    success_message = 'Categoria "%(nome)s" alterada com sucesso!'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'vendas/categoria_form.html'
    success_url = reverse_lazy('vendas:categoria-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Categoria'
        return ctx


class CategoriaDeleteView(LoginRequiredMixin, GroupRequiredMixin, MensagemExclusaoMixin, DeleteView):
    model = Categoria
    template_name = 'vendas/confirm_delete.html'
    success_url = reverse_lazy('vendas:categoria-list')
    group_required = GRUPOS_GESTAO

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Excluir Categoria'
        ctx['objeto'] = self.object.nome
        return ctx


# ===== VENDAS =====
# Venda tem FK para User (usuario). Regra de negócio: um Vendedor comum só
# enxerga/mexe nas vendas que ele mesmo registrou; Administrador e Gerente
# enxergam todas (visão gerencial). Isso é resolvido em get_queryset(),
# então list, detail e a ação de cancelar já saem filtrados.

class VendaListView(LoginRequiredMixin, FilterView):
    model = Venda
    filterset_class = VendaFilter
    template_name = 'vendas/venda_list.html'
    context_object_name = 'vendas'
    ordering = ['-data']
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        qs = super().get_queryset().select_related('cliente', 'usuario')
        if not is_gerencial(self.request.user):
            qs = qs.filter(usuario=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['somente_minhas'] = not is_gerencial(self.request.user)
        return ctx


class VendaCreateView(LoginRequiredMixin, CreateView):
    model = Venda
    form_class = VendaForm
    template_name = 'vendas/venda_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nova Venda'
        ctx['produtos'] = Produto.objects.filter(estoque_atual__gt=0).select_related('categoria').order_by('nome')
        return ctx

    def form_valid(self, form):
        produto_ids = self.request.POST.getlist('produto_id')
        quantidades = self.request.POST.getlist('quantidade')

        # Valida que pelo menos um item foi adicionado
        itens = []
        for pid, qty in zip(produto_ids, quantidades):
            try:
                qty = int(qty)
                if qty > 0:
                    itens.append((int(pid), qty))
            except (ValueError, TypeError):
                continue

        if not itens:
            form.add_error(None, 'Adicione pelo menos um produto à venda.')
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                venda = form.save(commit=False)
                # "guardar" o usuário logado no atributo de chave estrangeira
                venda.usuario = self.request.user
                venda.save()

                # Otimização: busca todos os produtos da venda numa única query
                # (antes era 1 get_object_or_404 por item) e trava as linhas
                # para evitar venda simultânea do mesmo estoque.
                produtos = Produto.objects.select_for_update().in_bulk([pid for pid, _ in itens])

                total = 0
                for pid, qty in itens:
                    produto = produtos.get(pid)
                    if produto is None:
                        raise ValueError('Produto informado não existe mais.')

                    if qty > produto.estoque_atual:
                        raise ValueError(
                            f'Estoque insuficiente para "{produto.nome}". '
                            f'Disponível: {produto.estoque_atual}'
                        )

                    subtotal = produto.preco_venda * qty
                    ItemVenda.objects.create(
                        venda=venda,
                        produto=produto,
                        quantidade=qty,
                        preco_unitario=produto.preco_venda,
                        subtotal=subtotal,
                    )
                    produto.estoque_atual -= qty
                    produto.save()

                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        tipo=TipoMovimentacao.SAIDA,
                        quantidade=qty,
                        origem=f'Venda #{venda.pk}',
                    )

                    total += subtotal

                venda.valor_total = total
                venda.save()

        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        messages.success(self.request, f'Venda #{venda.pk} registrada com sucesso!')
        return redirect(reverse_lazy('vendas:venda-detail', kwargs={'pk': venda.pk}))


class VendaDetailView(LoginRequiredMixin, DetailView):
    model = Venda
    template_name = 'vendas/venda_detail.html'
    context_object_name = 'venda'

    def get_queryset(self):
        # select_related('nota_fiscal'): o template testa venda.nota_fiscal — sem isso era +1 query.
        qs = super().get_queryset().select_related('cliente', 'usuario', 'nota_fiscal').prefetch_related('itens__produto')
        if not is_gerencial(self.request.user):
            qs = qs.filter(usuario=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Venda #{self.object.pk}'
        return ctx


class VendaCancelarView(LoginRequiredMixin, View):
    """Cancela uma venda e devolve o estoque dos produtos."""

    def post(self, request, pk):
        qs = Venda.objects.all()
        if not is_gerencial(request.user):
            qs = qs.filter(usuario=request.user)
        venda = get_object_or_404(qs, pk=pk)

        if venda.status == StatusVenda.CANCELADA:
            messages.error(request, 'Esta venda já está cancelada.')
            return redirect('vendas:venda-detail', pk=pk)

        if venda.status == StatusVenda.FINALIZADA:
            messages.error(request, 'Vendas finalizadas não podem ser canceladas.')
            return redirect('vendas:venda-detail', pk=pk)

        with transaction.atomic():
            for item in venda.itens.select_related('produto').all():
                item.produto.estoque_atual += item.quantidade
                item.produto.save()

                MovimentacaoEstoque.objects.create(
                    produto=item.produto,
                    tipo=TipoMovimentacao.ENTRADA,
                    quantidade=item.quantidade,
                    origem=f'Cancelamento da Venda #{venda.pk}',
                )

            venda.status = StatusVenda.CANCELADA
            venda.save()

        messages.success(request, f'Venda #{venda.pk} cancelada. Estoque revertido.')
        return redirect('vendas:venda-detail', pk=pk)


# ===== MOVIMENTAÇÃO DE ESTOQUE (somente leitura, gerada automaticamente) =====

class MovimentacaoEstoqueListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """
    Não existe CRUD manual para MovimentacaoEstoque por regra de negócio:
    os registros são criados automaticamente pelo sistema (venda/cancelamento),
    então só faz sentido oferecer a listagem/consulta.
    """
    model = MovimentacaoEstoque
    template_name = 'vendas/movimentacao_list.html'
    context_object_name = 'movimentacoes'
    ordering = ['-data']
    paginate_by = PAGINACAO_PADRAO
    group_required = GRUPOS_GESTAO

    def get_queryset(self):
        return super().get_queryset().select_related('produto')


class ProdutoPrecoView(LoginRequiredMixin, View):
    """Retorna preço e estoque de um produto via AJAX."""

    def get(self, request, pk):
        produto = get_object_or_404(Produto, pk=pk)
        return JsonResponse({
            'preco': str(produto.preco_venda),
            'estoque': produto.estoque_atual,
            'nome': produto.nome,
        })
