def grupos_usuario(request):
    """
    Disponibiliza os grupos do usuário logado para TODOS os templates com uma
    única query por requisição.

    Otimização identificada com o Django Debug Toolbar: o base.html chamava
    `request.user|has_group:"..."` várias vezes e `request.user.groups.first`
    na topbar, gerando 3+ queries idênticas em toda página.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'grupos_usuario': [], 'eh_gerencial': False, 'eh_admin': False}

    grupos = list(user.groups.values_list('name', flat=True))
    return {
        'grupos_usuario': grupos,
        'grupo_principal': grupos[0] if grupos else 'sem grupo',
        'eh_gerencial': user.is_superuser or bool({'Administrador', 'Gerente'} & set(grupos)),
        'eh_admin': user.is_superuser or 'Administrador' in grupos,
    }
