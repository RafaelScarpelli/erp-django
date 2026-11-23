from django.urls import path
from . import views

app_name = 'fiscal'

urlpatterns = [
    path('', views.NotaFiscalListView.as_view(), name='nota-list'),
    path('<int:pk>/', views.NotaFiscalDetailView.as_view(), name='nota-detail'),
    path('<int:pk>/cancelar/', views.NotaFiscalCancelarView.as_view(), name='nota-cancelar'),
    path('vendas/<int:venda_pk>/emitir/', views.NotaFiscalEmitirView.as_view(), name='nota-emitir'),
]
