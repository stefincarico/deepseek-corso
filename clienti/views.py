from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.core.exceptions import ValidationError
from fatture.models import Fattura, ScadenzaFattura
from tesoreria.models import Incasso
from tesoreria.forms import IncassoForm


def lista_clienti(request):
    """Mostra un elenco di tutti i clienti con i totali fatturati e residui."""
    # Annotiamo il queryset per calcolare i totali in modo efficiente,
    # usando il totale fattura IVA inclusa per il calcolo del residuo.
    clienti = Cliente.objects.annotate(
        # Fatturato Totale (Imponibile) per la visualizzazione
        total_fatturato=Coalesce(Sum('fatture__importo_totale', distinct=True), Decimal('0.00')),
        # Totale IVA per calcolare il totale complessivo
        total_iva=Coalesce(Sum(F('fatture__importo_totale') * F('fatture__aliquota_iva') / 100, distinct=True), Decimal('0.00')),
        # Totale Incassato
        total_incassato=Coalesce(Sum('fatture__scadenze__incassi__importo_incassato'), Decimal('0.00'))
    ).annotate(
        # Credito Residuo = (Imponibile + IVA) - Incassato
        total_residuo=(F('total_fatturato') + F('total_iva')) - F('total_incassato')
    ).order_by('ragione_sociale')
    
    context = {
        'clienti': clienti,
        'titolo_pagina': 'Elenco Clienti'
    }
    return render(request, 'clienti/lista_clienti.html', context)

def dettaglio_cliente(request, pk):
    """Mostra la scheda di dettaglio di un singolo cliente (partitario)."""
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = IncassoForm(request.POST)
        if form.is_valid():
            scadenza_id = request.POST.get('scadenza_id')
            scadenza = get_object_or_404(ScadenzaFattura, id=scadenza_id)

            try:
                incasso = form.save(commit=False)
                incasso.scadenza = scadenza
                # La validazione dell'importo è già stata fatta nel form.
                # La validazione della data viene fatta qui.
                incasso.clean() 
                incasso.save()  # Il segnale post_save aggiornerà tutto
                return redirect('clienti:dettaglio_cliente', pk=cliente.pk)
            except ValidationError as e:
                form.add_error(None, e) # Mostra l'errore nel form

    # Sezione 2: Elenco documenti emessi
    documenti_emessi = Fattura.objects.filter(cliente=cliente).order_by('-data_emissione')

    # Passiamo un'istanza vuota del form al template in caso di GET
    # o se il form in POST non è valido (per mostrare gli errori)
    incasso_form = form if request.method == 'POST' and not form.is_valid() else IncassoForm()

    # Nuova Sezione: Scadenziario Aperto
    # CORREZIONE: Filtriamo in base al residuo calcolato, non allo stato.
    # Questo garantisce coerenza matematica.
    scadenze_aperte = ScadenzaFattura.objects.filter(fattura__cliente=cliente).annotate(
        # Calcoliamo il totale incassato per ogni scadenza
        totale_incassato=Coalesce(Sum('incassi__importo_incassato'), Decimal('0.00'))
    ).annotate(
        # Calcoliamo il residuo direttamente nella query per passarlo al template
        residuo_calcolato=F('importo') - F('totale_incassato')
    ).filter(
        # Mostriamo solo le scadenze dove l'importo è maggiore di quanto incassato
        residuo_calcolato__gt=0
    ).select_related('fattura').order_by('data_scadenza')

    # Sezione 3: Registro movimenti contabilizzati
    # 3a. Recupera le fatture emesse per il registro
    movimenti_contabili = []
    for fattura in documenti_emessi:
        movimenti_contabili.append({
            'data': fattura.data_emissione,
            'tipo': 'Emissione Fattura',
            'descrizione': f"Fattura n. {fattura.numero}",
            'importo_dare': fattura.totale_complessivo(),
            'importo_avere': None,
        })

    # 3b. Recupera gli incassi del cliente
    incassi_cliente = Incasso.objects.filter(scadenza__fattura__cliente=cliente).select_related(
        'scadenza__fattura', 'conto_bancario'
    )
    movimenti_tesoreria = []
    for incasso in incassi_cliente:
        movimenti_tesoreria.append({
            'data': incasso.data_incasso,
            'tipo': 'Incasso',
            'descrizione': f"Incasso Fatt. {incasso.scadenza.fattura.numero} su {incasso.conto_bancario.nome}",
            'importo_dare': None,
            'importo_avere': incasso.importo_incassato,
        })

    # 3c. Unisce e ordina tutti i movimenti per data
    movimenti_combinati = sorted(movimenti_contabili + movimenti_tesoreria, key=lambda x: x['data'])

    context = {
        'cliente': cliente,
        'documenti_emessi': documenti_emessi,
        'incasso_form': incasso_form,
        'scadenze_aperte': scadenze_aperte,
        'movimenti': movimenti_combinati,
        'titolo_pagina': f"Partitario Cliente: {cliente.ragione_sociale}"
    }
    return render(request, 'clienti/dettaglio_cliente.html', context)
