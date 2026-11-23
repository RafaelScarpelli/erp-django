"""
App `ia` — ÚNICA porta de entrada do sistema para Inteligência Artificial.

Nenhum outro app deve chamar a API de um provedor diretamente: tudo passa
por `ia.services.chamar_ia()`, que lê a configuração do banco, confere a
cota mensal do usuário, faz a chamada e grava a auditoria.
"""
from django.conf import settings
from django.db import models


class Provedor(models.TextChoices):
    GEMINI = 'GEMINI', 'Google Gemini'
    OPENAI = 'OPENAI', 'OpenAI / compatível (Groq, OpenRouter, Ollama...)'
    ANTHROPIC = 'ANTHROPIC', 'Anthropic Claude'


class ConfiguracaoIA(models.Model):
    """
    Configuração editável em tela (singleton — sempre pk=1).
    Use ConfiguracaoIA.obter() para ler.
    """
    ativo = models.BooleanField('IA habilitada', default=False)
    provedor = models.CharField(max_length=20, choices=Provedor.choices, default=Provedor.GEMINI)
    modelo = models.CharField(max_length=100, default='gemini-2.5-flash',
                              help_text='Nome do modelo no provedor (ex.: gemini-2.5-flash, gpt-4o-mini).')
    base_url = models.URLField('URL base da API', blank=True,
                               help_text='Opcional. Deixe em branco para usar a URL padrão do provedor.')
    api_key = models.CharField('Chave da API', max_length=255, blank=True)
    temperatura = models.DecimalField(max_digits=3, decimal_places=2, default=0.3)
    max_tokens_resposta = models.PositiveIntegerField('Máx. tokens por resposta', default=800)
    timeout_segundos = models.PositiveIntegerField('Timeout (s)', default=30)
    cota_mensal_padrao = models.PositiveIntegerField(
        'Cota mensal padrão (tokens)', default=50000,
        help_text='Limite de tokens por usuário/mês quando ele não tem cota própria.',
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )

    class Meta:
        verbose_name = 'Configuração da IA'
        verbose_name_plural = 'Configuração da IA'

    def __str__(self):
        return f'{self.get_provedor_display()} — {self.modelo}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obter(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def api_key_mascarada(self):
        if not self.api_key:
            return '(não configurada)'
        return f'{self.api_key[:4]}…{self.api_key[-4:]}' if len(self.api_key) > 10 else '••••'


class CotaUsuarioIA(models.Model):
    """IA por usuário: habilita/desabilita e define a cota mensal individual."""
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cota_ia')
    habilitado = models.BooleanField('Pode usar a IA', default=True)
    limite_mensal_tokens = models.PositiveIntegerField(
        'Cota mensal (tokens)', null=True, blank=True,
        help_text='Em branco = usa a cota padrão da configuração.',
    )

    class Meta:
        verbose_name = 'Cota de IA do usuário'
        verbose_name_plural = 'Cotas de IA por usuário'

    def __str__(self):
        return f'Cota IA — {self.usuario}'

    def limite_efetivo(self, config=None):
        if self.limite_mensal_tokens is not None:
            return self.limite_mensal_tokens
        return (config or ConfiguracaoIA.obter()).cota_mensal_padrao


class StatusRequisicao(models.TextChoices):
    SUCESSO = 'SUCESSO', 'Sucesso'
    ERRO = 'ERRO', 'Erro'
    BLOQUEADA = 'BLOQUEADA', 'Bloqueada'


class RequisicaoIA(models.Model):
    """Auditoria de CADA chamada à IA (inclusive as bloqueadas e com erro)."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='requisicoes_ia'
    )
    origem = models.CharField(max_length=50, help_text='Quem chamou: assistente, teste_conexao...')
    provedor = models.CharField(max_length=20, choices=Provedor.choices)
    modelo = models.CharField(max_length=100)
    pergunta = models.TextField(blank=True)
    resposta = models.TextField(blank=True)
    tokens_entrada = models.PositiveIntegerField(default=0)
    tokens_saida = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=StatusRequisicao.choices)
    erro = models.TextField(blank=True)
    duracao_ms = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Requisição à IA'
        verbose_name_plural = 'Requisições à IA'
        ordering = ['-criado_em']
        indexes = [models.Index(fields=['usuario', 'criado_em'])]

    def __str__(self):
        return f'#{self.pk} {self.origem} — {self.status}'


class PapelMensagem(models.TextChoices):
    USUARIO = 'user', 'Usuário'
    ASSISTENTE = 'assistant', 'Assistente'


class MensagemAssistente(models.Model):
    """Histórico do assistente, separado por usuário."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensagens_assistente')
    papel = models.CharField(max_length=10, choices=PapelMensagem.choices)
    conteudo = models.TextField()
    requisicao = models.ForeignKey(RequisicaoIA, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem do assistente'
        verbose_name_plural = 'Mensagens do assistente'
        ordering = ['criado_em', 'id']

    def __str__(self):
        return f'{self.usuario} [{self.papel}] {self.conteudo[:40]}'
