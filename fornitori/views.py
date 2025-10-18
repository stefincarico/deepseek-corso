from django.shortcuts import render, get_object_or_404, redirect
from .models import Fornitore
from acquisti.models import FatturaAcquisto, ScadenzaFatturaAcquisto
from tesoreria.models import Spesa
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.core.exceptions import ValidationError

def lista_fornitori(request):
    """Mostra un elenco di tutti i fornitori con i totali di debito."""
    fornitori = Fornitore.objects.annotate(
        # Calcoliamo il totale acquistato (IVA inclusa)
        total_acquistato=Coalesce(Sum('fatture_acquisto__importo_totale'), Decimal('0.00')),
        total_iva=Coalesce(Sum(F('fatture_acquisto__importo_totale') * F('fatture_acquisto__aliquota_iva') / 100), Decimal('0.00')),
        # Calcoliamo il totale pagato
        total_pagato=Coalesce(Sum('fatture_acquisto__scadenze_acquisto__pagamenti__importo_pagato'), Decimal('0.00'))
    ).annotate(
        # Debito Residuo = (Acquistato + IVA) - Pagato
        total_debito=(F('total_acquistato') + F('total_iva')) - F('total_pagato')
    ).order_by('ragione_sociale')

    context = {
        'fornitori': fornitori,
        'titolo_pagina': 'Elenco Fornitori'
    }
    return render(request, 'fornitori/lista_fornitori.html', context)

def dettaglio_fornitore(request, pk):
    """Mostra la scheda di dettaglio di un singolo fornitore (partitario)."""
    fornitore = get_object_or_404(Fornitore, pk=pk)

    # Sezione: Elenco documenti di acquisto
    documenti_acquisto = FatturaAcquisto.objects.filter(fornitore=fornitore).order_by('-data_documento')

    # Sezione: Scadenziario Aperto
    scadenze_aperte = ScadenzaFatturaAcquisto.objects.filter(
        fattura_acquisto__fornitore=fornitore
    ).annotate(
        totale_pagato=Coalesce(Sum('pagamenti__importo_pagato'), Decimal('0.00'))
    ).annotate(
        residuo_calcolato=F('importo') - F('totale_pagato')
    ).filter(residuo_calcolato__gt=0).select_related('fattura_acquisto').order_by('data_scadenza')

    # Sezione: Registro movimenti
    movimenti_contabili = []
    for fattura in documenti_acquisto:
        movimenti_contabili.append({
            'data': fattura.data_documento,
            'tipo': 'Fattura di Acquisto',
            'descrizione': f"Fattura n. {fattura.numero}",
            'importo_dare': fattura.totale_complessivo(), # Aumento dei costi
            'importo_avere': None,
        })

    pagamenti_fornitore = Spesa.objects.filter(scadenza__fattura_acquisto__fornitore=fornitore).select_related(
        'scadenza__fattura_acquisto', 'conto_bancario'
    )
    movimenti_tesoreria = []
    for pagamento in pagamenti_fornitore:
        movimenti_tesoreria.append({
            'data': pagamento.data_pagamento,
            'tipo': 'Pagamento',
            'descrizione': f"Pagamento Fatt. {pagamento.scadenza.fattura_acquisto.numero} da {pagamento.conto_bancario.nome}",
            'importo_dare': None,
            'importo_avere': pagamento.importo_pagato, # Uscita di cassa
        })

    movimenti_combinati = sorted(movimenti_contabili + movimenti_tesoreria, key=lambda x: x['data'])

    context = {
        'fornitore': fornitore,
        'documenti_acquisto': documenti_acquisto,
        'scadenze_aperte': scadenze_aperte,
        'movimenti': movimenti_combinati,
        'titolo_pagina': f"Partitario Fornitore: {fornitore.ragione_sociale}"
    }
    return render(request, 'fornitori/dettaglio_fornitore.html', context)
