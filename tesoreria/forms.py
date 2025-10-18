from django import forms
from .models import Incasso, Spesa, ContoBancario
from decimal import Decimal

class IncassoForm(forms.ModelForm):
    # Campo non mappato sul modello, usato solo per la validazione
    residuo_scadenza = forms.DecimalField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Incasso
        fields = [
            'residuo_scadenza', # Aggiunto per l'ordine
            'data_incasso', 
            'importo_incassato', 
            'conto_bancario', 
            'metodo_pagamento', 
            'note'
        ]
        widgets = {
            'data_incasso': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['conto_bancario'].queryset = ContoBancario.objects.filter(attivo=True)

    def clean_importo_incassato(self):
        """
        Validazione custom per l'importo incassato.
        Verifica che non superi il residuo passato tramite il form.
        """
        importo_incassato = self.cleaned_data.get('importo_incassato')
        residuo_scadenza = self.cleaned_data.get('residuo_scadenza')

        if importo_incassato and residuo_scadenza and importo_incassato > residuo_scadenza:
            raise forms.ValidationError(f"L'importo incassato non può superare il residuo di €{residuo_scadenza}.")

        return importo_incassato


class SpesaForm(forms.ModelForm):
    """Form per la registrazione di un pagamento a fornitore."""
    residuo_scadenza = forms.DecimalField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Spesa
        fields = [
            'residuo_scadenza',
            'data_pagamento', 
            'importo_pagato', 
            'conto_bancario', 
            'metodo_pagamento', 
            'note'
        ]
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_importo_pagato(self):
        importo_pagato = self.cleaned_data.get('importo_pagato')
        residuo_scadenza = self.cleaned_data.get('residuo_scadenza')
        if importo_pagato and residuo_scadenza and importo_pagato > residuo_scadenza:
            raise forms.ValidationError(f"L'importo pagato non può superare il debito residuo di €{residuo_scadenza}.")
        return importo_pagato