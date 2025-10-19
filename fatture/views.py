from django.shortcuts import render, get_object_or_404, redirect
from .models import Fattura, ScadenzaFattura
from acquisti.models import ScadenzaFatturaAcquisto
from django.utils import timezone
from django.urls import reverse
from tesoreria.models import Incasso
from tesoreria.forms import IncassoForm, SpesaForm
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from .forms import FatturaForm, ScadenzaFatturaFormSet
from django.contrib import messages
from django.db import transaction

def lista_fatture(request):
    """Mostra un elenco di tutte le fatture."""
    fatture = Fattura.objects.select_related('cliente').order_by('-data_emissione')
    context = {
        'fatture': fatture,
        'titolo_pagina': 'Elenco Fatture'
    }
    return render(request, 'fatture/lista_fatture.html', context)

def scadenziario(request):
    """Mostra le scadenze delle fatture, divise tra scadute e da pagare."""
    # Gestione POST per entrambi i form
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'incasso':
            incasso_form = IncassoForm(request.POST)
            spesa_form = SpesaForm()
            if incasso_form.is_valid():
                scadenza_id = request.POST.get('scadenza_id')
                scadenza = get_object_or_404(ScadenzaFattura, id=scadenza_id)
                
                # CORREZIONE: Esegui la validazione qui, prima di salvare.
                if scadenza.fattura.stato == 'bozza':
                    incasso_form.add_error(None, "Operazione non permessa: non è possibile registrare un incasso per una fattura in stato 'Bozza'.")
                else:
                    incasso = incasso_form.save(commit=False)
                    incasso.scadenza = scadenza
                    incasso.save()
                    return redirect('fatture:scadenziario')
        elif form_type == 'spesa':
            spesa_form = SpesaForm(request.POST)
            incasso_form = IncassoForm()
            if spesa_form.is_valid():
                scadenza_id = request.POST.get('scadenza_id')
                scadenza = get_object_or_404(ScadenzaFatturaAcquisto, id=scadenza_id)

                if scadenza.fattura_acquisto.stato == 'da_registrare':
                    spesa_form.add_error(None, "Operazione non permessa: non è possibile registrare un pagamento per una fattura di acquisto non ancora registrata.")
                else:
                    spesa = spesa_form.save(commit=False)
                    spesa.scadenza = scadenza
                    spesa.save()
                    return redirect('fatture:scadenziario')
    else:
        incasso_form = IncassoForm()
        spesa_form = SpesaForm()

    # Gestione filtri GET
    tipo_filtro = request.GET.get('tipo', 'tutte')
    stato_filtro = request.GET.get('stato', 'tutte')
    data_da = request.GET.get('data_da')
    data_a = request.GET.get('data_a')

    scadenze_attive_qs = ScadenzaFattura.objects.annotate(
        residuo_calcolato=F('importo') - Coalesce(Sum('incassi__importo_incassato'), Decimal('0.00'))
    ).filter(residuo_calcolato__gt=0)

    scadenze_passive_qs = ScadenzaFatturaAcquisto.objects.annotate(
        residuo_calcolato=F('importo') - Coalesce(Sum('pagamenti__importo_pagato'), Decimal('0.00'))
    ).filter(residuo_calcolato__gt=0)

    # Applica filtri
    if stato_filtro == 'scadute':
        scadenze_attive_qs = scadenze_attive_qs.filter(data_scadenza__lt=timezone.now().date())
        scadenze_passive_qs = scadenze_passive_qs.filter(data_scadenza__lt=timezone.now().date())
    if data_da:
        scadenze_attive_qs = scadenze_attive_qs.filter(data_scadenza__gte=data_da)
        scadenze_passive_qs = scadenze_passive_qs.filter(data_scadenza__gte=data_da)
    if data_a:
        scadenze_attive_qs = scadenze_attive_qs.filter(data_scadenza__lte=data_a)
        scadenze_passive_qs = scadenze_passive_qs.filter(data_scadenza__lte=data_a)

    # Unifica i risultati
    scadenze_unificate = []
    if tipo_filtro in ['tutte', 'attive']:
        for s in scadenze_attive_qs.select_related('fattura__cliente'):
            scadenze_unificate.append({
                'tipo': 'attiva',
                'data_scadenza': s.data_scadenza,
                'riferimento_fattura': s.fattura.numero,
                'url_fattura': reverse('fatture:dettaglio_fattura', kwargs={'pk': s.fattura.pk}),
                'soggetto': s.fattura.cliente,
                'url_soggetto': s.fattura.cliente.get_absolute_url(),
                'importo_scadenza': s.importo,
                'residuo': s.residuo_calcolato,
                'is_scaduta': s.is_scaduta(),
                'pk': s.pk
            })

    if tipo_filtro in ['tutte', 'passive']:
        for s in scadenze_passive_qs.select_related('fattura_acquisto__fornitore'):
            scadenze_unificate.append({
                'tipo': 'passiva',
                'data_scadenza': s.data_scadenza,
                'riferimento_fattura': s.fattura_acquisto.numero,
                'url_fattura': reverse('acquisti:dettaglio_fattura_acquisto', kwargs={'pk': s.fattura_acquisto.pk}),
                'soggetto': s.fattura_acquisto.fornitore,
                'url_soggetto': s.fattura_acquisto.fornitore.get_absolute_url(),
                'importo_scadenza': s.importo,
                'residuo': s.residuo_calcolato,
                'is_scaduta': s.is_scaduta(),
                'pk': s.pk
            })

    # Ordina la lista combinata
    scadenze_unificate.sort(key=lambda x: x['data_scadenza'])

    context = {
        'scadenze': scadenze_unificate,
        'incasso_form': incasso_form,
        'spesa_form': spesa_form,
        'titolo_pagina': 'Scadenziario Aperto'
    }
    return render(request, 'fatture/scadenziario.html', context)

def dettaglio_fattura(request, pk):
    """Mostra la pagina di dettaglio di una singola fattura."""
    fattura = get_object_or_404(Fattura.objects.select_related('cliente'), pk=pk)

    if request.method == 'POST':
        form = IncassoForm(request.POST)
        if form.is_valid():
            scadenza_id = request.POST.get('scadenza_id')
            scadenza = get_object_or_404(ScadenzaFattura, id=scadenza_id)
            
            if scadenza.fattura.stato == 'bozza':
                form.add_error(None, "Operazione non permessa: non è possibile registrare un incasso per una fattura in stato 'Bozza'.")
            else:
                incasso = form.save(commit=False)
                incasso.scadenza = scadenza
                incasso.save()
                return redirect('fatture:dettaglio_fattura', pk=fattura.pk)
    
    incasso_form = form if request.method == 'POST' and not form.is_valid() else IncassoForm()
    
    # Recupera tutte le scadenze della fattura
    scadenze = fattura.scadenze.annotate(
        totale_incassato=Coalesce(Sum('incassi__importo_incassato'), Decimal('0.00'))
    ).annotate(
        residuo_calcolato=F('importo') - F('totale_incassato')
    ).order_by('data_scadenza')
    
    # Recupera tutti gli incassi relativi a questa fattura
    incassi = Incasso.objects.filter(scadenza__fattura=fattura).select_related('conto_bancario').order_by('data_incasso')

    context = {
        'fattura': fattura,
        'incasso_form': incasso_form,
        'scadenze': scadenze,
        'incassi': incassi,
        'titolo_pagina': f"Dettaglio Fattura N. {fattura.numero}"
    }
    return render(request, 'fatture/dettaglio_fattura.html', context)

def fattura_create(request):
    """Crea una nuova fattura in stato 'bozza'."""
    if request.method == 'POST':
        form = FatturaForm(request.POST)
        formset = ScadenzaFatturaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    fattura = form.save(commit=False)
                    fattura.stato = 'bozza' # Le nuove fatture sono sempre bozze
                    fattura.save()
                    formset.instance = fattura
                    formset.save()
                    messages.success(request, "Fattura creata come bozza con successo.")
                    return redirect('fatture:dettaglio_fattura', pk=fattura.pk)
            except Exception as e:
                messages.error(request, f"Si è verificato un errore: {e}")
        else:
            messages.error(request, "Errore nella compilazione del form. Controlla i campi.")
    else:
        form = FatturaForm()
        formset = ScadenzaFatturaFormSet()

    context = {
        'form': form,
        'formset': formset,
        'titolo_pagina': 'Crea Nuova Fattura'
    }
    return render(request, 'fatture/fattura_form.html', context)

def fattura_update(request, pk):
    """Modifica una fattura in stato 'bozza' e permette di finalizzarla."""
    fattura = get_object_or_404(Fattura, pk=pk)

    if fattura.stato != 'bozza':
        messages.error(request, "Questa fattura non è in stato 'bozza' e non può essere modificata.")
        return redirect('fatture:dettaglio_fattura', pk=fattura.pk)

    if request.method == 'POST':
        form = FatturaForm(request.POST, instance=fattura)
        formset = ScadenzaFatturaFormSet(request.POST, instance=fattura)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    fattura_salvata = form.save(commit=False)
                    
                    # Logica per il pulsante "Finalizza"
                    if 'finalizza' in request.POST:
                        # Controlla se la somma delle scadenze corrisponde al totale
                        totale_scadenze = sum(data.get('importo', Decimal('0.00')) for data in formset.cleaned_data if data and not data.get('DELETE'))
                        if totale_scadenze != fattura_salvata.totale_complessivo():
                            raise ValidationError(f"La somma delle scadenze (€{totale_scadenze}) non corrisponde al totale fattura (€{fattura_salvata.totale_complessivo()}).")
                        
                        fattura_salvata.stato = 'emessa'
                        messages.success(request, "Fattura finalizzata ed emessa con successo!")
                    else:
                        messages.success(request, "Bozza della fattura aggiornata.")

                    fattura_salvata.save()
                    formset.save()
                    return redirect('fatture:dettaglio_fattura', pk=fattura.pk)

            except ValidationError as e:
                messages.error(request, e.message)
            except Exception as e:
                messages.error(request, f"Si è verificato un errore imprevisto: {e}")
        else:
            messages.error(request, "Errore nella compilazione del form. Controlla i campi.")
    else:
        form = FatturaForm(instance=fattura)
        formset = ScadenzaFatturaFormSet(instance=fattura)

    context = {
        'form': form,
        'formset': formset,
        'fattura': fattura,
        'titolo_pagina': f'Modifica Bozza Fattura N. {fattura.numero}'
    }
    return render(request, 'fatture/fattura_form.html', context)
