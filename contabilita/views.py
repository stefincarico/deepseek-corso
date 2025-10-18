from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrazioneForm, MovimentoFormSet
from .models import RegistrazioneContabile
from decimal import Decimal

def prima_nota(request):
    """
    Vista per la gestione della Prima Nota: inserimento e visualizzazione
    delle registrazioni contabili.
    """
    if request.method == 'POST':
        registrazione_form = RegistrazioneForm(request.POST)
        movimento_formset = MovimentoFormSet(request.POST)

        if registrazione_form.is_valid() and movimento_formset.is_valid():
            # Validazione della partita doppia: Totale DARE deve essere uguale a Totale AVERE
            totale_dare = Decimal('0.00')
            totale_avere = Decimal('0.00')
            
            for form in movimento_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    if form.cleaned_data['tipo_movimento'] == 'dare':
                        totale_dare += form.cleaned_data['importo']
                    else:
                        totale_avere += form.cleaned_data['importo']
            
            if totale_dare != totale_avere:
                messages.error(request, f"La registrazione non è bilanciata! Totale Dare: {totale_dare}, Totale Avere: {totale_avere}")
            else:
                # Salva la registrazione e i movimenti associati
                registrazione = registrazione_form.save(commit=False)
                registrazione.stato = 'registrata'
                registrazione.save()
                
                movimenti = movimento_formset.save(commit=False)
                for movimento in movimenti:
                    movimento.registrazione = registrazione
                    movimento.save()
                
                messages.success(request, "Registrazione contabile salvata con successo.")
                return redirect('contabilita:prima_nota')
        else:
            # Se i form non sono validi, mostra un messaggio generico
            messages.error(request, "Errore nella compilazione del form. Controlla i campi.")

    else:
        registrazione_form = RegistrazioneForm()
        movimento_formset = MovimentoFormSet()

    # Recupera le ultime registrazioni per la visualizzazione
    ultime_registrazioni = RegistrazioneContabile.objects.order_by('-data_registrazione', '-id')[:10]

    context = {
        'registrazione_form': registrazione_form,
        'movimento_formset': movimento_formset,
        'ultime_registrazioni': ultime_registrazioni,
        'titolo_pagina': 'Prima Nota'
    }
    return render(request, 'contabilita/prima_nota.html', context)