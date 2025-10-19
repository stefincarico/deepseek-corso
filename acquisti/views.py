from django.shortcuts import render, get_object_or_404, redirect
from .models import FatturaAcquisto, ScadenzaFatturaAcquisto
from tesoreria.forms import SpesaForm
from tesoreria.models import Spesa
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from .forms import FatturaAcquistoForm, ScadenzaFatturaAcquistoFormSet
from django.contrib import messages
from django.db import transaction


def lista_fatture_acquisto(request):
    """Mostra un elenco di tutte le fatture di acquisto."""
    fatture = FatturaAcquisto.objects.select_related('fornitore').order_by('-data_documento')
    context = {
        'fatture': fatture,
        'titolo_pagina': 'Elenco Fatture Fornitori'
    }
    return render(request, 'acquisti/lista_fatture_acquisto.html', context)

def dettaglio_fattura_acquisto(request, pk):
    """Mostra la pagina di dettaglio di una singola fattura di acquisto."""
    fattura = get_object_or_404(FatturaAcquisto.objects.select_related('fornitore'), pk=pk)

    if request.method == 'POST':
        form = SpesaForm(request.POST)
        if form.is_valid():
            scadenza_id = request.POST.get('scadenza_id')
            scadenza = get_object_or_404(ScadenzaFatturaAcquisto, id=scadenza_id)
            try:
                spesa = form.save(commit=False)
                spesa.scadenza = scadenza
                spesa.clean() # Chiama la validazione del modello
                spesa.save()
                return redirect('acquisti:dettaglio_fattura_acquisto', pk=fattura.pk)
            except ValidationError as e:
                form.add_error(None, e)
    
    spesa_form = form if request.method == 'POST' and not form.is_valid() else SpesaForm()

    scadenze = fattura.scadenze_acquisto.annotate(
        totale_pagato=Coalesce(Sum('pagamenti__importo_pagato'), Decimal('0.00'))
    ).annotate(
        residuo_calcolato=F('importo') - F('totale_pagato')
    ).order_by('data_scadenza')
    
    pagamenti = Spesa.objects.filter(scadenza__fattura_acquisto=fattura).select_related('conto_bancario').order_by('data_pagamento')

    context = {
        'fattura': fattura,
        'spesa_form': spesa_form,
        'scadenze': scadenze,
        'pagamenti': pagamenti,
        'titolo_pagina': f"Dettaglio Fattura Acquisto N. {fattura.numero}"
    }
    return render(request, 'acquisti/dettaglio_fattura_acquisto.html', context)


def fattura_acquisto_create(request):
    """Crea una nuova fattura di acquisto in stato 'da_registrare'."""
    if request.method == 'POST':
        form = FatturaAcquistoForm(request.POST)
        formset = ScadenzaFatturaAcquistoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    fattura = form.save(commit=False)
                    fattura.stato = 'da_registrare'
                    fattura.save()
                    formset.instance = fattura
                    formset.save()
                    messages.success(request, "Fattura di acquisto creata come bozza con successo.")
                    return redirect('acquisti:dettaglio_fattura_acquisto', pk=fattura.pk)
            except Exception as e:
                messages.error(request, f"Si è verificato un errore: {e}")
        else:
            messages.error(request, "Errore nella compilazione del form. Controlla i campi.")
    else:
        form = FatturaAcquistoForm()
        formset = ScadenzaFatturaAcquistoFormSet()

    context = {
        'form': form,
        'formset': formset,
        'titolo_pagina': 'Crea Nuova Fattura di Acquisto'
    }
    return render(request, 'acquisti/fattura_acquisto_form.html', context)

def fattura_acquisto_update(request, pk):
    """Modifica una fattura di acquisto in stato 'da_registrare' e permette di finalizzarla."""
    fattura = get_object_or_404(FatturaAcquisto, pk=pk)

    if fattura.stato != 'da_registrare':
        messages.error(request, "Questa fattura non è in stato 'Da Registrare' e non può essere modificata.")
        return redirect('acquisti:dettaglio_fattura_acquisto', pk=fattura.pk)

    if request.method == 'POST':
        form = FatturaAcquistoForm(request.POST, instance=fattura)
        formset = ScadenzaFatturaAcquistoFormSet(request.POST, instance=fattura)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    fattura_salvata = form.save(commit=False)
                    
                    if 'finalizza' in request.POST:
                        totale_scadenze = sum(data.get('importo', Decimal('0.00')) for data in formset.cleaned_data if data and not data.get('DELETE'))
                        if totale_scadenze != fattura_salvata.totale_complessivo():
                            raise ValidationError(f"La somma delle scadenze (€{totale_scadenze}) non corrisponde al totale fattura (€{fattura_salvata.totale_complessivo()}).")
                        
                        fattura_salvata.stato = 'registrata'
                        messages.success(request, "Fattura di acquisto finalizzata e registrata con successo!")
                    else:
                        messages.success(request, "Bozza della fattura di acquisto aggiornata.")

                    fattura_salvata.save()
                    formset.save()
                    return redirect('acquisti:dettaglio_fattura_acquisto', pk=fattura.pk)

            except ValidationError as e:
                messages.error(request, e.message)
            except Exception as e:
                messages.error(request, f"Si è verificato un errore imprevisto: {e}")
    else:
        form = FatturaAcquistoForm(instance=fattura)
        formset = ScadenzaFatturaAcquistoFormSet(instance=fattura)

    context = {
        'form': form,
        'formset': formset,
        'fattura': fattura,
        'titolo_pagina': f'Modifica Bozza Fattura Acquisto N. {fattura.numero}'
    }
    return render(request, 'acquisti/fattura_acquisto_form.html', context)
