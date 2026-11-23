from django.contrib.auth.mixins import UserPassesTestMixin


class GroupRequiredMixin(UserPassesTestMixin):
    """
    Restringe o acesso a uma view a usuários que pertençam a pelo menos um
    dos grupos informados em `group_required`, ou que sejam superusuário.

    Uso:
        class ProdutoCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
            group_required = ['Administrador', 'Gerente']
    """
    group_required = []
    raise_exception = False
    permission_denied_message = 'Você não tem permissão para acessar esta página.'
    login_url = 'login'

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not self.group_required:
            return True
        return user.groups.filter(name__in=self.group_required).exists()

    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect

        if self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
            return redirect('dashboard')
        return super().handle_no_permission()


class DonoRequiredMixin:
    """
    Restringe o queryset da view aos registros cadastrados pelo próprio
    usuário logado (campo `usuario` do model, configurável em `campo_dono`).

    Usado em List/Detail/Update/Delete: como o filtro é aplicado no
    get_queryset(), tentar abrir o registro de outro usuário pela URL
    resulta em 404 — nem a existência do registro é revelada.

    Em CreateView, preenche o dono automaticamente no form_valid().
    """
    campo_dono = 'usuario'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.campo_dono: self.request.user})

    def form_valid(self, form):
        instancia = getattr(form, 'instance', None)  # DeleteView usa um Form simples
        if instancia is not None and not instancia.pk:
            setattr(instancia, self.campo_dono, self.request.user)
        return super().form_valid(form)


def user_in_groups(user, group_names):
    """Helper simples para usar em templates/views fora de CBVs."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=group_names).exists()


def is_gerencial(user):
    """
    Define quem tem visão 'gerencial' (vê tudo, não só o que cadastrou).
    Usado tanto para liberar CRUD de cadastros quanto para não filtrar
    vendas por usuário.
    """
    return user_in_groups(user, ['Administrador', 'Gerente'])
