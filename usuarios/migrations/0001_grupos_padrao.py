from django.db import migrations

GRUPOS = ['Administrador', 'Gerente', 'Vendedor']


def criar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for nome in GRUPOS:
        Group.objects.get_or_create(name=nome)


def remover_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GRUPOS).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_grupos, remover_grupos),
    ]
