"""
Adaptadores HTTP de cada provedor de IA.

USO INTERNO do app `ia`: o restante do sistema chama somente
`ia.services.chamar_ia()`. Cada função recebe a configuração, as instruções
de sistema e a lista de mensagens no formato
    [{'role': 'user' | 'assistant', 'content': '...'}]
e devolve (texto, tokens_entrada, tokens_saida).
"""
import requests

from .models import Provedor

URL_PADRAO = {
    Provedor.GEMINI: 'https://generativelanguage.googleapis.com/v1beta',
    Provedor.OPENAI: 'https://api.openai.com/v1',
    Provedor.ANTHROPIC: 'https://api.anthropic.com/v1',
}


class ErroProvedor(Exception):
    pass


def _post(url, config, **kwargs):
    try:
        resp = requests.post(url, timeout=config.timeout_segundos, **kwargs)
    except requests.Timeout:
        raise ErroProvedor(f'Tempo limite de {config.timeout_segundos}s excedido.')
    except requests.RequestException as exc:
        raise ErroProvedor(f'Falha de conexão com o provedor: {exc.__class__.__name__}')

    if resp.status_code >= 400:
        # Não devolve o corpo inteiro (pode ecoar dados sensíveis); só um trecho.
        raise ErroProvedor(f'HTTP {resp.status_code}: {resp.text[:300]}')
    try:
        return resp.json()
    except ValueError:
        raise ErroProvedor('Resposta do provedor não é um JSON válido.')


def _gemini(config, instrucoes, mensagens):
    base = (config.base_url or URL_PADRAO[Provedor.GEMINI]).rstrip('/')
    url = f'{base}/models/{config.modelo}:generateContent'
    corpo = {
        'contents': [
            {'role': 'model' if m['role'] == 'assistant' else 'user', 'parts': [{'text': m['content']}]}
            for m in mensagens
        ],
        'generationConfig': {
            'temperature': float(config.temperatura),
            'maxOutputTokens': config.max_tokens_resposta,
        },
    }
    if instrucoes:
        corpo['systemInstruction'] = {'parts': [{'text': instrucoes}]}

    dados = _post(url, config, json=corpo, headers={'x-goog-api-key': config.api_key})
    try:
        partes = dados['candidates'][0]['content']['parts']
        texto = ''.join(p.get('text', '') for p in partes)
    except (KeyError, IndexError):
        raise ErroProvedor('Resposta do Gemini sem conteúdo (pode ter sido bloqueada pelo filtro de segurança).')
    uso = dados.get('usageMetadata', {})
    return texto, uso.get('promptTokenCount', 0), uso.get('candidatesTokenCount', 0)


def _openai(config, instrucoes, mensagens):
    base = (config.base_url or URL_PADRAO[Provedor.OPENAI]).rstrip('/')
    msgs = ([{'role': 'system', 'content': instrucoes}] if instrucoes else []) + list(mensagens)
    corpo = {
        'model': config.modelo,
        'messages': msgs,
        'temperature': float(config.temperatura),
        'max_tokens': config.max_tokens_resposta,
    }
    dados = _post(f'{base}/chat/completions', config, json=corpo,
                  headers={'Authorization': f'Bearer {config.api_key}'})
    try:
        texto = dados['choices'][0]['message']['content'] or ''
    except (KeyError, IndexError):
        raise ErroProvedor('Resposta do provedor sem conteúdo.')
    uso = dados.get('usage', {})
    return texto, uso.get('prompt_tokens', 0), uso.get('completion_tokens', 0)


def _anthropic(config, instrucoes, mensagens):
    base = (config.base_url or URL_PADRAO[Provedor.ANTHROPIC]).rstrip('/')
    corpo = {
        'model': config.modelo,
        'max_tokens': config.max_tokens_resposta,
        'temperature': float(config.temperatura),
        'messages': list(mensagens),
    }
    if instrucoes:
        corpo['system'] = instrucoes
    dados = _post(f'{base}/messages', config, json=corpo, headers={
        'x-api-key': config.api_key,
        'anthropic-version': '2023-06-01',
    })
    texto = ''.join(b.get('text', '') for b in dados.get('content', []) if b.get('type') == 'text')
    uso = dados.get('usage', {})
    return texto, uso.get('input_tokens', 0), uso.get('output_tokens', 0)


ADAPTADORES = {
    Provedor.GEMINI: _gemini,
    Provedor.OPENAI: _openai,
    Provedor.ANTHROPIC: _anthropic,
}


def enviar(config, instrucoes, mensagens):
    adaptador = ADAPTADORES.get(config.provedor)
    if adaptador is None:
        raise ErroProvedor(f'Provedor desconhecido: {config.provedor}')
    return adaptador(config, instrucoes, mensagens)
