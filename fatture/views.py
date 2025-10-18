from django.shortcuts import render, get_object_or_404, redirect
from .models import Fattura, ScadenzaFattura
from django.utils import timezone
from tesoreria.models import Incasso
from tesoreria.forms import IncassoForm
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal

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
    if request.method == 'POST':
        form = IncassoForm(request.POST)
        if form.is_valid():
            scadenza_id = request.POST.get('scadenza_id')
            scadenza = get_object_or_404(ScadenzaFattura, id=scadenza_id)
            try:
                incasso = form.save(commit=False)
                incasso.scadenza = scadenza
                incasso.save() # Il segnale si occupa del resto
                return redirect('fatture:scadenziario')
            except ValidationError as e:
                form.add_error(None, e)
    
    incasso_form = form if request.method == 'POST' and not form.is_valid() else IncassoForm()

    scadenze_aperte = ScadenzaFattura.objects.annotate(
        totale_incassato=Coalesce(Sum('incassi__importo_incassato'), Decimal('0.00'))
    ).annotate(
        residuo_calcolato=F('importo') - F('totale_incassato')
    ).filter(residuo_calcolato__gt=0).select_related('fattura__cliente').order_by('data_scadenza')

    context = {
        'scadenze': scadenze_aperte,
        'incasso_form': incasso_form,
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
            try:
                incasso = form.save(commit=False)
                incasso.scadenza = scadenza
                incasso.save()
                return redirect('fatture:dettaglio_fattura', pk=fattura.pk)
            except ValidationError as e:
                form.add_error(None, e)
    
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
