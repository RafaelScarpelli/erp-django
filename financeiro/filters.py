import django_filters

from erp.filtros import FiltroBootstrap, DataInput
from .models import ContaPagar, ContaReceber, Fornecedor, StatusConta


class ContaPagarFilter(FiltroBootstrap):
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    fornecedor = django_filters.ModelChoiceFilter(
        queryset=Fornecedor.objects.order_by('nome'), label='Fornecedor', empty_label='Todos'
    )
    status = django_filters.ChoiceFilter(
        choices=[(StatusConta.PENDENTE, 'Pendente'), (StatusConta.PAGA, 'Paga')],
        label='Status', empty_label='Todos',
    )
    vencimento_de = django_filters.DateFilter(field_name='vencimento', lookup_expr='gte', label='Vence de', widget=DataInput())
    vencimento_ate = django_filters.DateFilter(field_name='vencimento', lookup_expr='lte', label='Vence até', widget=DataInput())

    class Meta:
        model = ContaPagar
        fields = ['descricao', 'fornecedor', 'status', 'vencimento_de', 'vencimento_ate']


class ContaReceberFilter(FiltroBootstrap):
    descricao = django_filters.CharFilter(lookup_expr='icontains', label='Descrição')
    cliente = django_filters.CharFilter(field_name='cliente__nome', lookup_expr='icontains', label='Cliente')
    status = django_filters.ChoiceFilter(
        choices=[(StatusConta.PENDENTE, 'Pendente'), (StatusConta.RECEBIDA, 'Recebida')],
        label='Status', empty_label='Todos',
    )
    vencimento_de = django_filters.DateFilter(field_name='vencimento', lookup_expr='gte', label='Vence de', widget=DataInput())
    vencimento_ate = django_filters.DateFilter(field_name='vencimento', lookup_expr='lte', label='Vence até', widget=DataInput())

    class Meta:
        model = ContaReceber
        fields = ['descricao', 'cliente', 'status', 'vencimento_de', 'vencimento_ate']
