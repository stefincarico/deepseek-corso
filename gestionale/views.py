from django.shortcuts import render
from django.db.models import Sum, Count, Q, F, Value
from django.utils import timezone
from decimal import Decimal

def dashboard(request):
    """
    Vista per la dashboard principale del gestionale.
    Mostra i KPI (Key Performance Indicators) più importanti.
    """
    from fatture.models import Fattura, ScadenzaFattura
    from clienti.models import Cliente
    from tesoreria.models import ContoBancario, Incasso
    from fornitori.models import Fornitore
    from acquisti.models import FatturaAcquisto
    
    # Calcolo del credito clienti (ottimizzato)
    crediti_aggregati = Fattura.objects.exclude(stato='pagata').aggregate(
        imponibile=Sum('importo_totale'),
        iva=Sum(F('importo_totale') * F('aliquota_iva') / 100)
    )
    credito_clienti = (crediti_aggregati['imponibile'] or Decimal('0.00')) + (crediti_aggregati['iva'] or Decimal('0.00'))

    # Calcolo del saldo totale dei conti
    saldo_totale_conti = ContoBancario.objects.aggregate(
        totale=Sum('saldo_attuale')
    )['totale'] or Decimal('0.00')

    # Calcolo Acquisti Totali (imponibile)
    acquisti_totali = FatturaAcquisto.objects.aggregate(
        totale=Sum('importo_totale')
    )['totale'] or Decimal('0.00')

    # Calcolo Debiti Fornitori
    debiti_aggregati = FatturaAcquisto.objects.exclude(stato='pagata').aggregate(
        imponibile=Sum('importo_totale'),
        iva=Sum(F('importo_totale') * F('aliquota_iva') / 100)
    )
    debiti_fornitori = (debiti_aggregati['imponibile'] or Decimal('0.00')) + (debiti_aggregati['iva'] or Decimal('0.00'))

    # KPI PRINCIPALI
    context = {
        # Totale fatturato
        'fatturato_totale': Fattura.objects.aggregate(
            totale=Sum('importo_totale')
        )['totale'] or Decimal('0.00'),
        'credito_clienti': credito_clienti,
        'attivo_circolante': credito_clienti + saldo_totale_conti,
        'acquisti_totali': acquisti_totali,
        'debiti_fornitori': debiti_fornitori,
        
        # Numero clienti attivi
        'numero_clienti': Cliente.objects.filter(stato='attivo').count(),
        # Numero fornitori attivi
        'numero_fornitori': Fornitore.objects.filter(stato='attivo').count(),
        
        # Prossime scadenze (7 giorni)
        'prossime_scadenze': ScadenzaFattura.objects.filter(
            data_scadenza__range=[
                timezone.now().date(),
                timezone.now().date() + timezone.timedelta(days=7)
            ],
            stato='da_pagare'
        ).order_by('data_scadenza')[:5],
        'saldo_totale': saldo_totale_conti,
        
        # Incassi recenti (ultimi 5)
        'incassi_recenti': Incasso.objects.select_related(
            'scadenza__fattura__cliente', 'conto_bancario'
        ).order_by('-data_incasso')[:5]
    }
    
    return render(request, 'dashboard.html', context)