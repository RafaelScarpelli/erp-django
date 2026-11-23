# mini-ERP

Sistema de gestão (vendas, estoque, financeiro, NF-e simulada) em Django 6, com assistente de IA.

**Acesso online (Google App Engine):** `https://SEU-PROJETO.rj.r.appspot.com` — ver [DEPLOY.md](DEPLOY.md)

## Rodando localmente
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # ajuste o banco (sem DB_NAME usa SQLite)
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Testes: `python manage.py test`

## Requisitos atendidos
| Requisito | Onde |
|---|---|
| Debug Toolbar + `select_related`/`prefetch_related` | `erp/settings.py`, [docs/OTIMIZACOES.md](docs/OTIMIZACOES.md) |
| Django Filter em ListViews (Vendas, Produtos, Clientes, Contas a Pagar, Contas a Receber, Requisições IA) | `*/filters.py`, `FilterView` nas views |
| Paginação + filtros com templatetag própria que preserva a busca | `erp/templatetags/paginacao.py` (`url_com_params`), `templates/partials/pagination.html` |
| Registros por usuário (só o dono lista/vê/altera/exclui) — `ContaPagar` e `ContaReceber` | `usuarios/mixins.py::DonoRequiredMixin`, `financeiro/views.py`, `financeiro/tests.py` |
| Framework de mensagens em cadastro, alteração e exclusão | `erp/mixins.py`, `templates/base.html` |
| Plugins jQuery: **DataTables**, **jQuery Mask**, **Bootbox** | `templates/base.html`, `static/js/erp.js` |
| Deploy Google App Engine | `app.yaml`, `.gcloudignore`, [DEPLOY.md](DEPLOY.md) |
| AGENTS.md + skills (incl. commits) | [AGENTS.md](AGENTS.md), `.agents/skills/*/SKILL.md` |
| App `ia`: config editável, auditoria, cota mensal, telas | `ia/` — Requisições, Configuração (Testar conexão), IA por usuário, Meu consumo |
| Assistente com `chamar_ia`, `contexto_projeto.md`, limites, histórico, janela de 5, AJAX+CSRF, Markdown sanitizado | `ia/assistente.py`, `ia/contexto_projeto.md`, `templates/ia/assistente.html`, `ia/templatetags/ia_extras.py` |
| Auditoria TestAI | [docs/AUDITORIA_TESTAI.md](docs/AUDITORIA_TESTAI.md) |

## Perfis
`Administrador`, `Gerente` e `Vendedor` (criados pela migration `usuarios/0001_grupos_padrao`).
Adicione os usuários aos grupos em `/admin/`.

## Configurando a IA
Entre como Administrador → **Configuração da IA** → escolha o provedor (Gemini, OpenAI-compatível ou
Anthropic), modelo e chave → marque "IA habilitada" → **Salvar** → **Testar conexão**.
