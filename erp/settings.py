"""
Django settings for erp project.

Configuração lida de variáveis de ambiente (python-decouple), para funcionar
tanto localmente quanto no Google App Engine (ver DEPLOY.md).
"""

import os
from pathlib import Path

from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# Rodando no Google App Engine? (variável definida automaticamente pelo GAE)
NO_GAE = os.getenv('GAE_APPLICATION') is not None

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-43%ox^x-@#xn)kqsfqcgc4g6wwk3rthnn&rx(n&2cyr+(7w46j',
)

DEBUG = config('DEBUG', default=not NO_GAE, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.appspot.com', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='https://*.appspot.com', cast=Csv())

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'erp',
    'vendas',
    'usuarios',
    'financeiro',
    'fiscal',
    'ia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Django Debug Toolbar — ativo somente quando DEBUG=True (nunca em produção/GAE).
# Requisito: identificar queries repetidas e otimizá-las com select_related /
# prefetch_related. As otimizações aplicadas estão documentadas em
# docs/OTIMIZACOES.md.
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'erp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Calcula os grupos do usuário UMA vez por requisição (antes o
                # base.html fazia várias queries repetidas com has_group).
                'usuarios.context_processors.grupos_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'erp.wsgi.application'


# Database
# - Local: PostgreSQL com DB_NAME/DB_USER/DB_PASSWORD no .env.
#   Sem DB_NAME definido, cai para SQLite (útil para testes rápidos).
# - GAE: DB_HOST=/cloudsql/<PROJETO>:<REGIAO>:<INSTANCIA> (socket do Cloud SQL).

DB_NAME = config('DB_NAME', default='')

if DB_NAME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # destino do collectstatic (servido pelo app.yaml no GAE)

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Framework de mensagens: mapeia o nível ERROR para a classe "danger"
# (usada no base.html para pintar o alerta de vermelho).
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

# Segurança extra em produção
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ===== IA =====
# A chave/modelo/provedor ficam no banco (tela "Configuração da IA").
# Aqui só os parâmetros do assistente que não precisam ser editáveis.
IA_JANELA_HISTORICO = 5  # nº de mensagens anteriores enviadas à IA
IA_CONTEXTO_PROJETO = BASE_DIR / 'ia' / 'contexto_projeto.md'
