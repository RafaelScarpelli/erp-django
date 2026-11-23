from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from vendas.models import Cliente
from .models import ContaPagar, ContaReceber, Fornecedor


class DonoDoRegistroTests(TestCase):
    """Somente quem lançou a conta pode listar, ver, alterar e excluir — inclusive Gerente/Admin."""

    def setUp(self):
        self.dono = User.objects.create_user('dono', password='x')
        self.outro = User.objects.create_user('outro', password='x')
        self.outro.groups.add(Group.objects.get_or_create(name='Gerente')[0])
        forn = Fornecedor.objects.create(nome='Forn', cnpj='00.000.000/0001-00')
        cli = Cliente.objects.create(nome='Cli', cpf_cnpj='000.000.000-00')
        self.cp = ContaPagar.objects.create(fornecedor=forn, usuario=self.dono, descricao='Luz-do-dono', valor=10, vencimento=date.today())
        self.cr = ContaReceber.objects.create(cliente=cli, usuario=self.dono, descricao='Rec-do-dono', valor=10, vencimento=date.today())

    def test_outro_usuario_nao_ve_nem_mexe(self):
        self.client.force_login(self.outro)
        self.assertNotContains(self.client.get(reverse('financeiro:conta-pagar-list')), 'Luz-do-dono')
        self.assertNotContains(self.client.get(reverse('financeiro:conta-receber-list')), 'Rec-do-dono')
        for nome, obj in [('conta-pagar', self.cp), ('conta-receber', self.cr)]:
            for acao in ('detail', 'update', 'delete'):
                r = self.client.get(reverse(f'financeiro:{nome}-{acao}', args=[obj.pk]))
                self.assertEqual(r.status_code, 404, f'{nome}-{acao}')
        r = self.client.post(reverse('financeiro:conta-pagar-delete', args=[self.cp.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(ContaPagar.objects.filter(pk=self.cp.pk).exists())

    def test_dono_acessa_e_recebe_mensagem_ao_excluir(self):
        self.client.force_login(self.dono)
        self.assertContains(self.client.get(reverse('financeiro:conta-pagar-detail', args=[self.cp.pk])), 'Luz-do-dono')
        r = self.client.post(reverse('financeiro:conta-pagar-delete', args=[self.cp.pk]), follow=True)
        self.assertContains(r, 'excluída com sucesso')

    def test_filtro_e_paginacao_preservam_parametros(self):
        self.client.force_login(self.dono)
        for i in range(12):
            ContaPagar.objects.create(fornecedor=self.cp.fornecedor, usuario=self.dono, descricao=f'agua {i}', valor=1, vencimento=date.today())
        r = self.client.get(reverse('financeiro:conta-pagar-list') + '?descricao=agua')
        self.assertContains(r, '?descricao=agua&amp;page=2')
