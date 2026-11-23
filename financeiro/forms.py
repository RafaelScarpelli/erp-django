from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

from .models import Fornecedor, ContaPagar, ContaReceber


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'telefone', 'email', 'endereco']
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nome', css_class='col-md-8'),
                Column('cnpj', css_class='col-md-4'),
            ),
            Row(
                Column('telefone', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
            ),
            Field('endereco'),
            Submit('submit', 'Salvar', css_class='btn-green mt-2'),
        )


class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = ['fornecedor', 'descricao', 'valor', 'vencimento']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('fornecedor'),
            Field('descricao'),
            Row(
                Column('valor', css_class='col-md-6'),
                Column('vencimento', css_class='col-md-6'),
            ),
            Submit('submit', 'Salvar', css_class='btn-green mt-2'),
        )


class ContaReceberForm(forms.ModelForm):
    class Meta:
        model = ContaReceber
        fields = ['cliente', 'venda', 'descricao', 'valor', 'vencimento']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['venda'].required = False
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('cliente', css_class='col-md-6'),
                Column('venda', css_class='col-md-6'),
            ),
            Field('descricao'),
            Row(
                Column('valor', css_class='col-md-6'),
                Column('vencimento', css_class='col-md-6'),
            ),
            Submit('submit', 'Salvar', css_class='btn-green mt-2'),
        )
