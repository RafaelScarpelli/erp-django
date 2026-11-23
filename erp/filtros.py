import django_filters
from django import forms


class FiltroBootstrap(django_filters.FilterSet):
    """
    FilterSet base: aplica as classes do Bootstrap (form-control / form-select)
    nos widgets, para os filtros ficarem no mesmo visual escuro do sistema.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.form.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple, forms.NullBooleanSelect)):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')


class DataInput(forms.DateInput):
    input_type = 'date'
