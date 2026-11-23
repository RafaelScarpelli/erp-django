import django_filters
from django.contrib.auth import get_user_model

from erp.filtros import FiltroBootstrap, DataInput
from .models import RequisicaoIA, StatusRequisicao


class RequisicaoIAFilter(FiltroBootstrap):
    usuario = django_filters.ModelChoiceFilter(
        queryset=get_user_model().objects.order_by('username'), label='Usuário', empty_label='Todos'
    )
    origem = django_filters.CharFilter(lookup_expr='icontains', label='Origem')
    status = django_filters.ChoiceFilter(choices=StatusRequisicao.choices, label='Status', empty_label='Todos')
    data_de = django_filters.DateFilter(field_name='criado_em', lookup_expr='date__gte', label='De', widget=DataInput())
    data_ate = django_filters.DateFilter(field_name='criado_em', lookup_expr='date__lte', label='Até', widget=DataInput())

    class Meta:
        model = RequisicaoIA
        fields = ['usuario', 'origem', 'status', 'data_de', 'data_ate']
