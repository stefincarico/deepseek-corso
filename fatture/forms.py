from django import forms
from django.forms import inlineformset_factory
from .models import Fattura, ScadenzaFattura
from clienti.models import Cliente

class FatturaForm(forms.ModelForm):
    class Meta:
        model = Fattura
        fields = ['cliente', 'numero', 'data_emissione', 'importo_totale', 'aliquota_iva', 'descrizione']
        widgets = {
            'data_emissione': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(stato='attivo')


class ScadenzaFatturaForm(forms.ModelForm):
    class Meta:
        model = ScadenzaFattura
        fields = ['data_scadenza', 'importo']
        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }


ScadenzaFatturaFormSet = inlineformset_factory(
    Fattura,
    ScadenzaFattura,
    form=ScadenzaFatturaForm, # Specifica il form da usare
    extra=1,
    can_delete=True,
)