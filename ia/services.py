"""
Serviço central de IA.

>>> from ia.services import chamar_ia
>>> resp = chamar_ia(request.user, [{'role': 'user', 'content': 'Olá'}], origem='assistente')
>>> resp.texto, resp.total_tokens

`chamar_ia` é a ÚNICA função que o resto do sistema deve usar. Ela:
  1. lê a configuração do banco (ConfiguracaoIA);
  2. verifica se a IA está ligada e se o usuário está habilitado;
  3. confere a cota mensal de tokens do usuário;
  4. chama o provedor configurado;
  5. grava a auditoria (RequisicaoIA) — sucesso, erro ou bloqueio.
"""
import time
from dataclasses import dataclass

from django.db.models import Sum
from django.utils import timezone

from . import provedores
from .models import ConfiguracaoIA, CotaUsuarioIA, RequisicaoIA, StatusRequisicao

LIMITE_TEXTO_AUDITORIA = 4000


class IAErro(Exception):
    """Erro genérico de IA (mensagem segura para mostrar ao usuário)."""


class IADesabilitada(IAErro):
    pass


class CotaExcedida(IAErro):
    pass


@dataclass
class RespostaIA:
    texto: str
    tokens_entrada: int
    tokens_saida: int
    requisicao: RequisicaoIA

    @property
    def total_tokens(self):
        return self.tokens_entrada + self.tokens_saida


# ---------------- Cota / consumo ----------------

def inicio_do_mes(agora=None):
    agora = timezone.localtime(agora or timezone.now())
    return agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def consumo_mes(usuario):
    """Total de tokens consumidos pelo usuário no mês corrente."""
    return (
        RequisicaoIA.objects
        .filter(usuario=usuario, criado_em__gte=inicio_do_mes())
        .aggregate(t=Sum('total_tokens'))['t'] or 0
    )


def obter_cota(usuario):
    cota, _ = CotaUsuarioIA.objects.get_or_create(usuario=usuario)
    return cota


def resumo_consumo(usuario, config=None):
    config = config or ConfiguracaoIA.obter()
    cota = obter_cota(usuario)
    limite = cota.limite_efetivo(config)
    usado = consumo_mes(usuario)
    percentual = min(100, round(usado * 100 / limite)) if limite else 100
    return {
        'habilitado': cota.habilitado,
        'limite': limite,
        'usado': usado,
        'restante': max(0, limite - usado),
        'percentual': percentual,
        'cota_propria': cota.limite_mensal_tokens is not None,
    }


# ---------------- Auditoria ----------------

def _auditar(usuario, config, origem, pergunta, status, **campos):
    return RequisicaoIA.objects.create(
        usuario=usuario,
        origem=origem,
        provedor=config.provedor,
        modelo=config.modelo,
        pergunta=(pergunta or '')[:LIMITE_TEXTO_AUDITORIA],
        status=status,
        **campos,
    )


# ---------------- Porta de entrada ----------------

def chamar_ia(usuario, mensagens, *, instrucoes='', origem='sistema', ignorar_cota=False):
    """
    Envia `mensagens` ([{'role': 'user'|'assistant', 'content': str}, ...])
    ao provedor configurado e devolve um RespostaIA.

    Levanta IADesabilitada, CotaExcedida ou IAErro (sempre auditados).
    """
    config = ConfiguracaoIA.obter()
    ultima_pergunta = next((m['content'] for m in reversed(mensagens) if m['role'] == 'user'), '')

    # 1) IA ligada e configurada?
    if not config.ativo or not config.api_key:
        motivo = 'A IA está desabilitada ou sem chave de API configurada.'
        _auditar(usuario, config, origem, ultima_pergunta, StatusRequisicao.BLOQUEADA, erro=motivo)
        raise IADesabilitada(motivo)

    # 2) Usuário habilitado + cota
    cota = obter_cota(usuario)
    if not cota.habilitado:
        motivo = 'Seu usuário não está habilitado para usar a IA. Fale com o administrador.'
        _auditar(usuario, config, origem, ultima_pergunta, StatusRequisicao.BLOQUEADA, erro=motivo)
        raise IADesabilitada(motivo)

    if not ignorar_cota:
        limite = cota.limite_efetivo(config)
        usado = consumo_mes(usuario)
        if usado >= limite:
            motivo = f'Cota mensal de tokens atingida ({usado:,} de {limite:,}).'.replace(',', '.')
            _auditar(usuario, config, origem, ultima_pergunta, StatusRequisicao.BLOQUEADA, erro=motivo)
            raise CotaExcedida(motivo)

    # 3) Chamada ao provedor
    inicio = time.monotonic()
    try:
        texto, tok_in, tok_out = provedores.enviar(config, instrucoes, mensagens)
    except provedores.ErroProvedor as exc:
        duracao = int((time.monotonic() - inicio) * 1000)
        _auditar(usuario, config, origem, ultima_pergunta, StatusRequisicao.ERRO,
                 erro=str(exc)[:LIMITE_TEXTO_AUDITORIA], duracao_ms=duracao)
        raise IAErro('Não foi possível obter resposta da IA agora. Tente novamente em instantes.') from exc

    duracao = int((time.monotonic() - inicio) * 1000)
    tok_in, tok_out = int(tok_in or 0), int(tok_out or 0)

    # 4) Auditoria de sucesso
    requisicao = _auditar(
        usuario, config, origem, ultima_pergunta, StatusRequisicao.SUCESSO,
        resposta=texto[:LIMITE_TEXTO_AUDITORIA],
        tokens_entrada=tok_in, tokens_saida=tok_out, total_tokens=tok_in + tok_out,
        duracao_ms=duracao,
    )
    return RespostaIA(texto=texto, tokens_entrada=tok_in, tokens_saida=tok_out, requisicao=requisicao)


def testar_conexao(usuario):
    """Chamada mínima para validar provedor/modelo/chave. Não consome cota do usuário."""
    return chamar_ia(
        usuario,
        [{'role': 'user', 'content': 'Teste de conexão. Responda apenas com a palavra OK.'}],
        origem='teste_conexao',
        ignorar_cota=True,
    )
