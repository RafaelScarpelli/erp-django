from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_names):
    """
    Uso no template: {% if request.user|has_group:"Administrador,Gerente" %}
    Superusuário sempre passa. Aceita uma lista de nomes separados por vírgula.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    nomes = [n.strip() for n in group_names.split(',')]
    return user.groups.filter(name__in=nomes).exists()
