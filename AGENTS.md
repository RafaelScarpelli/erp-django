# AGENTS.md — Guia para agentes de IA neste repositório

Este arquivo orienta agentes de IA (Claude Code, Codex, Copilot, Cursor etc.) que trabalham no **mini-ERP**.
Leia-o inteiro antes de alterar código. Skills detalhadas ficam em `.agents/skills/`.

## Visão geral
- Django 6.0 + PostgreSQL (SQLite se `DB_NAME` não estiver definido), Bootstrap 5, Crispy Forms, jQuery.
- Idioma do código, comentários, mensagens e UI: **português do Brasil**.
- Apps:
  | App | Responsabilidade |
  |---|---|
  | `usuarios` | login, dashboard, grupos (Administrador/Gerente/Vendedor), mixins de permissão |
  | `vendas` | clientes, produtos, categorias, vendas, movimentação de estoque |
  | `financeiro` | fornecedores, contas a pagar/receber (por dono), caixa |
  | `fiscal` | NF-e **simulada** (sem SEFAZ) |
  | `ia` | **única** porta de entrada para IA: config, auditoria, cotas, assistente |
  | `erp` | settings, urls, templatetags de paginação, mixins de mensagens, filtros base |

## Comandos
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver          # Debug Toolbar ativo com DEBUG=True
python manage.py test               # rode SEMPRE antes de concluir uma tarefa
python manage.py makemigrations --check --dry-run   # nenhuma migration pendente
```

## Regras obrigatórias
1. **IA só via `ia.services.chamar_ia()`.** Nunca importe `requests` para chamar provedores fora de
   `ia/provedores.py`, nunca leia a chave da API fora do app `ia`. Ver skill `usar-ia`.
2. **Registros com dono** (`ContaPagar`, `ContaReceber`): use `DonoRequiredMixin` em TODAS as views
   (list/detail/update/delete/create). Acesso de terceiros deve resultar em 404.
3. **Mensagens**: toda criação/alteração/exclusão usa o framework de mensagens — `MensagemCadastroMixin`
   (com `success_message`) e `MensagemExclusaoMixin` de `erp/mixins.py`.
4. **Listas**: `FilterView` + `filterset_class` (herdando `erp.filtros.FiltroBootstrap`) + `paginate_by`
   + `{% include 'partials/filtros.html' with filtro=filter %}` + `{% include 'partials/pagination.html' %}`.
   Nunca escreva `href="?page=N"` à mão: use `{% url_com_params page=N %}` (preserva filtros).
5. **Queries**: todo FK exibido em loop de template exige `select_related`; relações reversas/M2M,
   `prefetch_related`. Confira no Debug Toolbar (painel SQL → "similar/duplicated"). Registre em
   `docs/OTIMIZACOES.md`.
6. **Front-end**: estender `base.html`; jQuery e plugins (DataTables, jQuery Mask, Bootbox) já estão
   carregados. Exclusões usam `class="js-confirmar-exclusao" data-nome="..."`; ações POST usam
   `<form class="js-confirmar" data-mensagem="...">`. Não use `alert()`/`confirm()` nativos.
7. **AJAX**: sempre enviar `X-CSRFToken: ERP.csrfToken()`. Nunca use `@csrf_exempt`.
8. **Conteúdo da IA é não confiável**: renderize só com o filtro `markdown_seguro` / função
   `markdown_para_html_seguro` (Markdown + nh3). Nunca `|safe` em texto vindo da IA ou do usuário.
9. **Segredos**: nada de chave/senha no código. Use variáveis de ambiente (`python-decouple`) ou a tela
   de Configuração da IA. Não commite `.env`.
10. **Commits**: siga a skill `mensagens-de-commit` (Conventional Commits em português).

## Estilo
- PEP 8, 4 espaços, linhas até ~110 colunas, aspas simples.
- CBVs com mixins na ordem: `LoginRequiredMixin`, `GroupRequiredMixin`/`DonoRequiredMixin`, mixins de mensagem, view genérica.
- Templates com as variáveis CSS do `base.html` (`--green-primary`, `--bg-card`...). Ícones Tabler (`ti ti-*`).

## Skills disponíveis
| Skill | Quando usar |
|---|---|
| `.agents/skills/mensagens-de-commit` | ao criar qualquer commit |
| `.agents/skills/nova-tela-crud` | ao criar um CRUD/listagem nova |
| `.agents/skills/usar-ia` | ao adicionar qualquer funcionalidade que use IA |
| `.agents/skills/deploy-gae` | ao publicar no Google App Engine |

## O que NÃO fazer
- Não criar lançamentos manuais de `MovimentacaoEstoque`/`MovimentoCaixa` (são gerados pelo sistema).
- Não integrar com a SEFAZ real (fora do escopo; NF-e é simulada).
- Não remover a restrição por dono nem as verificações de grupo para "facilitar testes".
