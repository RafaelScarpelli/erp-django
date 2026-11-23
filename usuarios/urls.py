from django.urls import path
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Alteração de senha do usuário logado
    path(
        'senha/alterar/',
        PasswordChangeView.as_view(
            template_name='usuarios/password_change_form.html',
            success_url='/senha/alterar/feito/',
        ),
        name='password_change',
    ),
    path(
        'senha/alterar/feito/',
        PasswordChangeDoneView.as_view(
            template_name='usuarios/password_change_done.html',
        ),
        name='password_change_done',
    ),
]
