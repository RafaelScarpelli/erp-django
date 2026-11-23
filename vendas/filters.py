import django_filters

from erp.filtros import FiltroBootstrap, DataInput
from .models import Produto, Venda, Cliente, Categoria, StatusVenda


class ProdutoFilter(FiltroBootstrap):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')
    categoria = django_filters.ModelChoiceFilter(
        queryset=Categoria.objects.order_by('nome'), label='Categoria', empty_label='Todas'
    )
    estoque_max = django_filters.NumberFilter(
        field_name='estoque_atual', lookup_expr='lte', label='Estoque até'
    )

    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'estoque_max']


class ClienteFilter(FiltroBootstrap):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')
    cpf_cnpj = django_filters.CharFilter(lookup_expr='icontains', label='CPF / CNPJ')

    class Meta:
        model = Cliente
        fields = ['nome', 'cpf_cnpj']


class VendaFilter(FiltroBootstrap):
    cliente = django_filters.ModelChoiceFilter(
        queryset=Cliente.objects.order_by('nome'), label='Cliente', empty_label='Todos'
    )
    status = django_filters.ChoiceFilter(choices=StatusVenda.choices, label='Status', empty_label='Todos')
    data_inicio = django_filters.DateFilter(
        field_name='data', lookup_expr='date__gte', label='De', widget=DataInput()
    )
    data_fim = django_filters.DateFilter(
        field_name='data', lookup_expr='date__lte', label='Até', widget=DataInput()
    )

    class Meta:
        model = Venda
        fields = ['cliente', 'status', 'data_inicio', 'data_fim']
