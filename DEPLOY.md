# Deploy no Google App Engine

Ambiente **standard**, runtime `python313`, banco **Cloud SQL (PostgreSQL)**.

**Link de acesso:** `https://SEU-PROJETO.rj.r.appspot.com`  ← substitua após o deploy.

## 1. Pré-requisitos
- Conta no Google Cloud com faturamento ativo e o [gcloud CLI](https://cloud.google.com/sdk/docs/install).
```bash
gcloud auth login
gcloud projects create SEU-PROJETO      # ou use um existente
gcloud config set project SEU-PROJETO
gcloud services enable appengine.googleapis.com sqladmin.googleapis.com
gcloud app create --region=southamerica-east1
```

## 2. Banco (Cloud SQL PostgreSQL)
```bash
gcloud sql instances create erp-db --database-version=POSTGRES_16 \
    --tier=db-f1-micro --region=southamerica-east1
gcloud sql databases create erp --instance=erp-db
gcloud sql users create erp --instance=erp-db --password=SENHA-FORTE
gcloud sql instances describe erp-db --format="value(connectionName)"   # SEU-PROJETO:southamerica-east1:erp-db
```

## 3. Configurar o `app.yaml`
Preencha `SECRET_KEY`, `DB_PASSWORD`, `DB_HOST` (`/cloudsql/<connectionName>`) e `cloud_sql_instances`.
Gere uma SECRET_KEY com:
```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```
> Não commite o `app.yaml` com valores reais. Alternativa: Secret Manager.

## 4. Migrations e superusuário (via Cloud SQL Auth Proxy, da sua máquina)
```bash
./cloud-sql-proxy SEU-PROJETO:southamerica-east1:erp-db &
DB_NAME=erp DB_USER=erp DB_PASSWORD=SENHA-FORTE DB_HOST=127.0.0.1 python manage.py migrate
DB_NAME=erp DB_USER=erp DB_PASSWORD=SENHA-FORTE DB_HOST=127.0.0.1 python manage.py createsuperuser
```

## 5. Estáticos e deploy
```bash
python manage.py collectstatic --noinput
gcloud app deploy
gcloud app browse
```

## 6. Pós-deploy
1. Entre com o superusuário, abra **Configuração da IA**, informe provedor/modelo/chave, marque
   "IA habilitada", salve e clique em **Testar conexão**.
2. Crie os usuários no `/admin/` e coloque-os nos grupos Administrador / Gerente / Vendedor.

## Problemas comuns
| Sintoma | Causa provável |
|---|---|
| 400 Bad Request | domínio fora de `ALLOWED_HOSTS` |
| 403 CSRF ao logar | `CSRF_TRUSTED_ORIGINS` sem o domínio https |
| CSS/JS não carregam | faltou `collectstatic` antes do `gcloud app deploy` |
| 500 ao abrir | veja `gcloud app logs tail -s default` (geralmente conexão com o Cloud SQL) |
