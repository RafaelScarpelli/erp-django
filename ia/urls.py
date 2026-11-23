from django.urls import path

from . import views

app_name = 'ia'

urlpatterns = [
    # Usuário
    path('assistente/', views.AssistenteView.as_view(), name='assistente'),
    path('assistente/perguntar/', views.AssistentePerguntarView.as_view(), name='assistente-perguntar'),
    path('assistente/limpar/', views.LimparHistoricoView.as_view(), name='assistente-limpar'),
    path('meu-consumo/', views.MeuConsumoView.as_view(), name='meu-consumo'),

    # Administração
    path('requisicoes/', views.RequisicaoListView.as_view(), name='requisicao-list'),
    path('configuracao/', views.ConfiguracaoView.as_view(), name='configuracao'),
    path('configuracao/testar/', views.TestarConexaoView.as_view(), name='testar-conexao'),
    path('usuarios/', views.UsuarioIAListView.as_view(), name='usuario-list'),
    path('usuarios/<int:usuario_pk>/cota/', views.CotaUsuarioUpdateView.as_view(), name='cota-update'),
]
