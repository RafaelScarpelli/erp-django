from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Submit, HTML
from django import forms

from .models import ConfiguracaoIA, CotaUsuarioIA


class ConfiguracaoIAForm(forms.ModelForm):
    # A chave nunca é devolvida ao navegador; em branco = mantém a atual.
    api_key = forms.CharField(
        label='Chave da API', required=False,
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        help_text='Deixe em branco para manter a chave atual.',
    )

    class Meta:
        model = ConfiguracaoIA
        fields = ['ativo', 'provedor', 'modelo', 'base_url', 'api_key', 'temperatura',
                  'max_tokens_resposta', 'timeout_segundos', 'cota_mensal_padrao']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.api_key:
            self.fields['api_key'].help_text = (
                f'Atual: {self.instance.api_key_mascarada}. Deixe em branco para manter.'
            )
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('ativo'),
            Row(Column('provedor', css_class='col-md-6'), Column('modelo', css_class='col-md-6')),
            Field('base_url'),
            Field('api_key'),
            Row(
                Column('temperatura', css_class='col-md-4'),
                Column('max_tokens_resposta', css_class='col-md-4'),
                Column('timeout_segundos', css_class='col-md-4'),
            ),
            Field('cota_mensal_padrao'),
        )

    def clean_temperatura(self):
        t = self.cleaned_data['temperatura']
        if t is not None and not (0 <= t <= 2):
            raise forms.ValidationError('A temperatura deve estar entre 0 e 2.')
        return t

    def save(self, commit=True):
        obj = super().save(commit=False)
        nova_chave = self.cleaned_data.get('api_key')
        if not nova_chave:
            obj.api_key = ConfiguracaoIA.obter().api_key
        if commit:
            obj.save()
        return obj


class CotaUsuarioIAForm(forms.ModelForm):
    class Meta:
        model = CotaUsuarioIA
        fields = ['habilitado', 'limite_mensal_tokens']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('habilitado'),
            Field('limite_mensal_tokens'),
            Submit('submit', 'Salvar', css_class='btn-green mt-2'),
        )
