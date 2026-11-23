from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from .mixins import is_gerencial


class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        # Import local para evitar import circular entre apps
        from vendas.models import Venda, Cliente, StatusVenda

        ctx = super().get_context_data(**kwargs)

        vendas_qs = Venda.objects.all()
        if not is_gerencial(self.request.user):
            vendas_qs = vendas_qs.filter(usuario=self.request.user)

        hoje = timezone.localdate()
        vendas_hoje_qs = vendas_qs.filter(
            data__date=hoje,
        ).exclude(status=StatusVenda.CANCELADA)

        total_hoje = vendas_hoje_qs.aggregate(total=Sum('valor_total'))['total'] or 0

        ctx['total_vendas_hoje'] = total_hoje
        ctx['pedidos_hoje'] = vendas_hoje_qs.count()
        ctx['total_clientes'] = Cliente.objects.count()
        ctx['ultimas_vendas'] = (
            vendas_qs.select_related('cliente', 'usuario').order_by('-data')[:5]
        )
        ctx['is_gerencial'] = is_gerencial(self.request.user)
        return ctx
