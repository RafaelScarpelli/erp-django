"""
URL configuration for erp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('vendas/', include('vendas.urls', namespace='vendas')),
    path('financeiro/', include('financeiro.urls', namespace='financeiro')),
    path('fiscal/notas/', include('fiscal.urls', namespace='fiscal')),
    path('ia/', include('ia.urls', namespace='ia')),
    path('sobre/', login_required(TemplateView.as_view(
        template_name='sobre.html',
        extra_context={
            'tecnologias': [
                'Python 3.14',
                'Django 6.0',
                'PostgreSQL',
                'Bootstrap 5',
                'Django Crispy Forms',
                'psycopg2',
                'python-decouple',
                'django-filter',
                'Django Debug Toolbar',
                'jQuery 3.7 + DataTables, jQuery Mask e Bootbox',
                'IA generativa (Gemini / OpenAI / Anthropic) via app ia',
                'Google App Engine',
            ]
        }
    )), name='sobre'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
