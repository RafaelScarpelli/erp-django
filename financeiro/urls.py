from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Fornecedores
    path('fornecedores/', views.FornecedorListView.as_view(), name='fornecedor-list'),
    path('fornecedores/novo/', views.FornecedorCreateView.as_view(), name='fornecedor-create'),
    path('fornecedores/<int:pk>/editar/', views.FornecedorUpdateView.as_view(), name='fornecedor-update'),
    path('fornecedores/<int:pk>/excluir/', views.FornecedorDeleteView.as_view(), name='fornecedor-delete'),

    # Contas a Pagar
    path('contas-pagar/', views.ContaPagarListView.as_view(), name='conta-pagar-list'),
    path('contas-pagar/<int:pk>/', views.ContaPagarDetailView.as_view(), name='conta-pagar-detail'),
    path('contas-pagar/nova/', views.ContaPagarCreateView.as_view(), name='conta-pagar-create'),
    path('contas-pagar/<int:pk>/editar/', views.ContaPagarUpdateView.as_view(), name='conta-pagar-update'),
    path('contas-pagar/<int:pk>/excluir/', views.ContaPagarDeleteView.as_view(), name='conta-pagar-delete'),
    path('contas-pagar/<int:pk>/baixar/', views.ContaPagarBaixarView.as_view(), name='conta-pagar-baixar'),

    # Contas a Receber
    path('contas-receber/', views.ContaReceberListView.as_view(), name='conta-receber-list'),
    path('contas-receber/<int:pk>/', views.ContaReceberDetailView.as_view(), name='conta-receber-detail'),
    path('contas-receber/nova/', views.ContaReceberCreateView.as_view(), name='conta-receber-create'),
    path('contas-receber/<int:pk>/editar/', views.ContaReceberUpdateView.as_view(), name='conta-receber-update'),
    path('contas-receber/<int:pk>/excluir/', views.ContaReceberDeleteView.as_view(), name='conta-receber-delete'),
    path('contas-receber/<int:pk>/baixar/', views.ContaReceberBaixarView.as_view(), name='conta-receber-baixar'),

    # Caixa (extrato somente leitura)
    path('caixa/', views.MovimentoCaixaListView.as_view(), name='caixa-list'),
]
