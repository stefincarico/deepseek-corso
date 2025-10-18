from django import forms
from .models import RegistrazioneContabile, MovimentoContabile, PianoDeiConti
from decimal import Decimal

class RegistrazioneForm(forms.ModelForm):
    """Form per la testata della registrazione contabile."""
    class Meta:
        model = RegistrazioneContabile
        fields = ['data_registrazione', 'descrizione', 'riferimento']
        widgets = {
            'data_registrazione': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 2}),
        }

class MovimentoForm(forms.ModelForm):
    """Form per una singola riga di movimento (Dare/Avere)."""
    class Meta:
        model = MovimentoContabile
        fields = ['conto', 'tipo_movimento', 'importo', 'note']
        widgets = {
            # Trasforma il campo note da un'area di testo a un input a riga singola
            'note': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra i conti per mostrare solo quelli "foglia" (non-mastro) e attivi.
        self.fields['conto'].queryset = PianoDeiConti.objects.filter(sottoconti__isnull=True, attivo=True).order_by('codice')

# Un FormSet è una collezione di form, perfetta per gestire un numero variabile di righe di movimento.
MovimentoFormSet = forms.inlineformset_factory(
    RegistrazioneContabile,
    MovimentoContabile,
    form=MovimentoForm,
    extra=2,  # Mostra 2 righe vuote per iniziare
    can_delete=True, # Permette di eliminare le righe
    min_num=2 # Richiede almeno 2 righe (una Dare e una Avere)
)