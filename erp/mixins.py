"""
Mixins reutilizáveis de mensagens (django.contrib.messages) para
cadastro, alteração e exclusão.
"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect


class MensagemCadastroMixin(SuccessMessageMixin):
    """CreateView/UpdateView: mensagem de sucesso + mensagem de erro de validação."""
    mensagem_erro = 'Não foi possível salvar. Verifique os campos destacados.'

    def form_invalid(self, form):
        messages.error(self.request, self.mensagem_erro)
        return super().form_invalid(form)


class MensagemExclusaoMixin:
    """
    DeleteView: mensagem de sucesso após excluir e mensagem de erro amigável
    quando o registro está protegido por FK (on_delete=PROTECT).
    `success_message` aceita {objeto} para o str() do registro excluído.
    """
    success_message = '"{objeto}" excluído com sucesso.'
    mensagem_protegido = 'Não é possível excluir "{objeto}": existem registros vinculados a ele.'

    def form_valid(self, form):
        objeto = str(self.object)
        try:
            resposta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.mensagem_protegido.format(objeto=objeto))
            return redirect(self.get_success_url())
        messages.success(self.request, self.success_message.format(objeto=objeto))
        return resposta
