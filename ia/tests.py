from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ConfiguracaoIA, CotaUsuarioIA, MensagemAssistente, RequisicaoIA, StatusRequisicao
from .services import CotaExcedida, IADesabilitada, chamar_ia
from .templatetags.ia_extras import markdown_para_html_seguro


class ChamarIATests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='x')
        cfg = ConfiguracaoIA.obter()
        cfg.ativo, cfg.api_key, cfg.cota_mensal_padrao = True, 'chave-teste', 100
        cfg.save()

    def test_ia_desabilitada_e_auditada(self):
        ConfiguracaoIA.objects.update(ativo=False)
        with self.assertRaises(IADesabilitada):
            chamar_ia(self.user, [{'role': 'user', 'content': 'oi'}])
        self.assertEqual(RequisicaoIA.objects.get().status, StatusRequisicao.BLOQUEADA)

    @mock.patch('ia.provedores.enviar', return_value=('Olá!', 30, 20))
    def test_sucesso_grava_auditoria_e_tokens(self, _):
        resp = chamar_ia(self.user, [{'role': 'user', 'content': 'oi'}], origem='teste')
        self.assertEqual(resp.total_tokens, 50)
        req = RequisicaoIA.objects.get()
        self.assertEqual((req.status, req.total_tokens, req.origem), (StatusRequisicao.SUCESSO, 50, 'teste'))

    @mock.patch('ia.provedores.enviar', return_value=('ok', 60, 60))
    def test_cota_excedida_bloqueia(self, _):
        chamar_ia(self.user, [{'role': 'user', 'content': '1'}])  # consome 120 > 100
        with self.assertRaises(CotaExcedida):
            chamar_ia(self.user, [{'role': 'user', 'content': '2'}])

    def test_usuario_desabilitado(self):
        CotaUsuarioIA.objects.create(usuario=self.user, habilitado=False)
        with self.assertRaises(IADesabilitada):
            chamar_ia(self.user, [{'role': 'user', 'content': 'oi'}])


class AssistenteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('bia', password='x')
        cfg = ConfiguracaoIA.obter()
        cfg.ativo, cfg.api_key = True, 'k'
        cfg.save()
        self.client.force_login(self.user)

    @mock.patch('ia.provedores.enviar', return_value=('**Resposta**', 10, 5))
    def test_janela_de_5_mensagens(self, enviar):
        for i in range(8):
            MensagemAssistente.objects.create(usuario=self.user, papel='user' if i % 2 == 0 else 'assistant', conteudo=f'm{i}')
        r = self.client.post(reverse('ia:assistente-perguntar'), data='{"pergunta": "nova"}', content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('<strong>Resposta</strong>', r.json()['resposta_html'])
        mensagens_enviadas = enviar.call_args[0][2]
        self.assertLessEqual(len(mensagens_enviadas) - 1, 5)  # histórico <= janela
        self.assertEqual(mensagens_enviadas[-1]['content'], 'nova')
        self.assertEqual(mensagens_enviadas[0]['role'], 'user')

    def test_csrf_obrigatorio(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        r = c.post(reverse('ia:assistente-perguntar'), data='{"pergunta": "x"}', content_type='application/json')
        self.assertEqual(r.status_code, 403)

    def test_historico_isolado_por_usuario(self):
        outro = User.objects.create_user('caio', password='x')
        MensagemAssistente.objects.create(usuario=outro, papel='user', conteudo='segredo-do-caio')
        r = self.client.get(reverse('ia:assistente'))
        self.assertNotContains(r, 'segredo-do-caio')


class MarkdownSeguroTests(TestCase):
    def test_remove_script_e_javascript(self):
        html = markdown_para_html_seguro('oi <script>alert(1)</script> [x](javascript:alert(1)) <img src=x onerror=alert(1)>')
        self.assertNotIn('<script', html)
        self.assertNotIn('javascript:', html)
        self.assertNotIn('onerror', html)
