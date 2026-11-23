import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, UpdateView
from django_filters.views import FilterView

from erp.mixins import MensagemCadastroMixin
from usuarios.mixins import GroupRequiredMixin
from . import assistente
from .filters import RequisicaoIAFilter
from .forms import ConfiguracaoIAForm, CotaUsuarioIAForm
from .models import ConfiguracaoIA, CotaUsuarioIA, MensagemAssistente, RequisicaoIA, StatusRequisicao
from .services import IAErro, inicio_do_mes, resumo_consumo, testar_conexao
from .templatetags.ia_extras import markdown_para_html_seguro

GRUPOS_ADMIN_IA = ['Administrador']
User = get_user_model()


# ====================== Telas administrativas ======================

class RequisicaoListView(LoginRequiredMixin, GroupRequiredMixin, FilterView):
    """Auditoria: todas as chamadas feitas à IA, com filtros."""
    model = RequisicaoIA
    filterset_class = RequisicaoIAFilter
    template_name = 'ia/requisicao_list.html'
    context_object_name = 'requisicoes'
    paginate_by = 20
    group_required = GRUPOS_ADMIN_IA

    def get_queryset(self):
        return RequisicaoIA.objects.select_related('usuario').order_by('-criado_em')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.filterset.qs if hasattr(self, 'filterset') else self.get_queryset()
        ctx['totais'] = qs.aggregate(
            chamadas=Count('id'),
            tokens=Sum('total_tokens'),
            erros=Count('id', filter=~Q(status=StatusRequisicao.SUCESSO)),
        )
        return ctx


class ConfiguracaoView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    model = ConfiguracaoIA
    form_class = ConfiguracaoIAForm
    template_name = 'ia/configuracao.html'
    success_url = reverse_lazy('ia:configuracao')
    success_message = 'Configuração da IA salva com sucesso!'
    group_required = GRUPOS_ADMIN_IA

    def get_object(self, queryset=None):
        return ConfiguracaoIA.obter()

    def form_valid(self, form):
        form.instance.atualizado_por = self.request.user
        return super().form_valid(form)


class TestarConexaoView(LoginRequiredMixin, GroupRequiredMixin, View):
    """POST via AJAX (com CSRF) — testa a configuração SALVA."""
    group_required = GRUPOS_ADMIN_IA
    raise_exception = True

    def post(self, request):
        try:
            resp = testar_conexao(request.user)
        except IAErro as exc:
            ultima = RequisicaoIA.objects.filter(origem='teste_conexao').order_by('-id').first()
            detalhe = ultima.erro if ultima else ''
            return JsonResponse({'ok': False, 'mensagem': str(exc), 'detalhe': detalhe[:300]}, status=400)
        return JsonResponse({
            'ok': True,
            'mensagem': 'Conexão realizada com sucesso!',
            'resposta': resp.texto[:200],
            'modelo': resp.requisicao.modelo,
            'duracao_ms': resp.requisicao.duracao_ms,
            'tokens': resp.total_tokens,
        })


class UsuarioIAListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """IA por usuário: habilitação, cota e consumo do mês de cada usuário."""
    template_name = 'ia/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    group_required = GRUPOS_ADMIN_IA

    def get_queryset(self):
        # Uma única query: usuário + cota (select_related) + consumo do mês (annotate).
        return (
            User.objects.filter(is_active=True)
            .select_related('cota_ia')
            .annotate(
                consumo_mes=Sum('requisicoes_ia__total_tokens',
                                filter=Q(requisicoes_ia__criado_em__gte=inicio_do_mes())),
                chamadas_mes=Count('requisicoes_ia',
                                   filter=Q(requisicoes_ia__criado_em__gte=inicio_do_mes())),
            )
            .order_by('username')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        config = ConfiguracaoIA.obter()
        ctx['cota_padrao'] = config.cota_mensal_padrao
        linhas = []
        for u in ctx['usuarios']:
            cota = getattr(u, 'cota_ia', None)
            limite = cota.limite_mensal_tokens if cota and cota.limite_mensal_tokens is not None else config.cota_mensal_padrao
            usado = u.consumo_mes or 0
            linhas.append({
                'usuario': u,
                'habilitado': cota.habilitado if cota else True,
                'cota_propria': bool(cota and cota.limite_mensal_tokens is not None),
                'limite': limite,
                'usado': usado,
                'chamadas': u.chamadas_mes,
                'percentual': min(100, round(usado * 100 / limite)) if limite else 100,
            })
        ctx['linhas'] = linhas
        return ctx


class CotaUsuarioUpdateView(LoginRequiredMixin, GroupRequiredMixin, MensagemCadastroMixin, UpdateView):
    model = CotaUsuarioIA
    form_class = CotaUsuarioIAForm
    template_name = 'ia/cota_form.html'
    success_url = reverse_lazy('ia:usuario-list')
    group_required = GRUPOS_ADMIN_IA

    def get_object(self, queryset=None):
        usuario = User.objects.get(pk=self.kwargs['usuario_pk'])
        cota, _ = CotaUsuarioIA.objects.get_or_create(usuario=usuario)
        return cota

    def get_success_message(self, cleaned_data):
        return f'Cota de IA de "{self.object.usuario}" atualizada.'


# ====================== Telas do usuário ======================

class MeuConsumoView(LoginRequiredMixin, ListView):
    template_name = 'ia/meu_consumo.html'
    context_object_name = 'requisicoes'
    paginate_by = 15

    def get_queryset(self):
        return RequisicaoIA.objects.filter(usuario=self.request.user).order_by('-criado_em')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resumo'] = resumo_consumo(self.request.user)
        ctx['chamadas_mes'] = RequisicaoIA.objects.filter(
            usuario=self.request.user, criado_em__gte=inicio_do_mes()
        ).count()
        return ctx


class AssistenteView(LoginRequiredMixin, TemplateView):
    template_name = 'ia/assistente.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ultimas = list(
            MensagemAssistente.objects.filter(usuario=self.request.user).order_by('-criado_em', '-id')[:50]
        )
        ultimas.reverse()
        ctx['historico'] = ultimas
        ctx['resumo'] = resumo_consumo(self.request.user)
        ctx['ia_ativa'] = ConfiguracaoIA.obter().ativo
        ctx['janela'] = assistente.settings.IA_JANELA_HISTORICO
        return ctx


class AssistentePerguntarView(LoginRequiredMixin, View):
    """
    Endpoint AJAX: recebe {"pergunta": "..."} em JSON. Proteção CSRF padrão
    do Django (header X-CSRFToken enviado pelo JS). Responde JSON com o HTML
    da resposta já convertido de Markdown e SANITIZADO.
    """
    raise_exception = True

    def post(self, request):
        try:
            dados = json.loads(request.body or '{}')
        except ValueError:
            return JsonResponse({'ok': False, 'erro': 'Requisição inválida.'}, status=400)

        pergunta = (dados.get('pergunta') or '').strip()
        if not pergunta:
            return JsonResponse({'ok': False, 'erro': 'Digite uma pergunta.'}, status=400)
        if len(pergunta) > assistente.TAMANHO_MAX_PERGUNTA:
            return JsonResponse(
                {'ok': False, 'erro': f'Pergunta muito longa (máx. {assistente.TAMANHO_MAX_PERGUNTA} caracteres).'},
                status=400,
            )

        try:
            msg, resposta = assistente.perguntar(request.user, pergunta)
        except IAErro as exc:
            return JsonResponse({'ok': False, 'erro': str(exc)}, status=429 if 'Cota' in str(exc) else 503)

        resumo = resumo_consumo(request.user)
        return JsonResponse({
            'ok': True,
            'resposta_html': markdown_para_html_seguro(msg.conteudo),
            'tokens': resposta.total_tokens,
            'consumo': {'usado': resumo['usado'], 'limite': resumo['limite'], 'percentual': resumo['percentual']},
        })


class LimparHistoricoView(LoginRequiredMixin, View):
    def post(self, request):
        apagadas, _ = MensagemAssistente.objects.filter(usuario=request.user).delete()
        messages.success(request, f'Histórico do assistente limpo ({apagadas} mensagens removidas).')
        return redirect('ia:assistente')
