from django import forms
from django.forms import inlineformset_factory
from .models import FatturaAcquisto, ScadenzaFatturaAcquisto
from fornitori.models import Fornitore

class FatturaAcquistoForm(forms.ModelForm):
    class Meta:
        model = FatturaAcquisto
        fields = ['fornitore', 'numero', 'data_documento', 'data_ricezione', 'importo_totale', 'aliquota_iva', 'descrizione']
        widgets = {
            'data_documento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_ricezione': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fornitore'].queryset = Fornitore.objects.filter(stato='attivo')

class ScadenzaFatturaAcquistoForm(forms.ModelForm):
    class Meta:
        model = ScadenzaFatturaAcquisto
        fields = ['data_scadenza', 'importo']
        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

ScadenzaFatturaAcquistoFormSet = inlineformset_factory(
    FatturaAcquisto, ScadenzaFatturaAcquisto, form=ScadenzaFatturaAcquistoForm, extra=1, can_delete=True
)