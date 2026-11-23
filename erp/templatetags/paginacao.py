"""
Templatetags próprias de paginação.

O problema: o partial de paginação gerava links "?page=2", descartando os
filtros do django-filter (?status=PAGA&descricao=luz). Ao trocar de página o
usuário perdia a busca.

`{% url_com_params page=2 %}` devolve a query string ATUAL com o parâmetro
informado substituído (ou removido, se o valor for vazio/None), preservando
todos os outros parâmetros — inclusive campos de filtro com vários valores.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_com_params(context, **kwargs):
    request = context.get('request')
    if request is None:
        params_str = '&'.join(f'{k}={v}' for k, v in kwargs.items() if v not in (None, ''))
        return f'?{params_str}' if params_str else '?'

    query = request.GET.copy()
    for chave, valor in kwargs.items():
        if valor in (None, ''):
            query.pop(chave, None)
        else:
            query[chave] = valor
    codificado = query.urlencode()
    return f'?{codificado}' if codificado else '?'


@register.simple_tag(takes_context=True)
def params_sem_pagina(context):
    """Query string atual sem o parâmetro `page` (útil para links de ordenação/exportação)."""
    request = context.get('request')
    if request is None:
        return ''
    query = request.GET.copy()
    query.pop('page', None)
    return query.urlencode()


@register.filter
def tem_filtro_ativo(request):
    """True se existe algum parâmetro de filtro preenchido (ignora `page`)."""
    if request is None:
        return False
    return any(v for k, v in request.GET.items() if k != 'page')
