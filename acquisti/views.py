from django.shortcuts import render, get_object_or_404, redirect
from .models import FatturaAcquisto, ScadenzaFatturaAcquisto
from tesoreria.forms import SpesaForm
from tesoreria.models import Spesa
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal

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