"""
Renderização SEGURA de Markdown das respostas da IA.

A resposta da IA é conteúdo não confiável (pode conter HTML/JS injetado via
prompt injection). Fluxo: Markdown -> HTML (python-markdown) -> sanitização
com nh3 (allowlist de tags/atributos, remove <script>, on*=, javascript: etc).
"""
import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

TAGS_PERMITIDAS = {
    'p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
}
ATRIBUTOS_PERMITIDOS = {'a': {'href', 'title'}, 'th': {'align'}, 'td': {'align'}}


def markdown_para_html_seguro(texto):
    html = md.markdown(texto or '', extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])
    return nh3.clean(
        html,
        tags=TAGS_PERMITIDAS,
        attributes=ATRIBUTOS_PERMITIDOS,
        url_schemes={'http', 'https', 'mailto'},
        link_rel='noopener noreferrer nofollow',
    )


@register.filter(name='markdown_seguro')
def markdown_seguro(texto):
    return mark_safe(markdown_para_html_seguro(texto))  # noqa: S308 — já sanitizado pelo nh3
