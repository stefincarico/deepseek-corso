from django.shortcuts import render
from .models import ContoBancario, Incasso
from fatture.models import Fattura

def saldi_conti(request):
    """Mostra un elenco di tutti i conti con i relativi saldi."""
    conti = ContoBancario.objects.filter(attivo=True)
    context = {
        'conti': conti,
        'titolo_pagina': 'Saldi Conti'
    }
    return render(request, 'tesoreria/saldi_conti.html', context)

def lista_movimenti(request):
    """Mostra un elenco combinato di movimenti contabili (fatture) e di tesoreria (incassi)."""
    
    # 1. Recupera le fatture emesse (movimenti contabili)
    fatture_emesse = Fattura.objects.select_related('cliente').exclude(stato='bozza')
    movimenti_contabili = []
    for fattura in fatture_emesse:
        movimenti_contabili.append({
            'data': fattura.data_emissione,
            'tipo': 'Emissione Fattura',
            'descrizione': f"Fattura n. {fattura.numero} a {fattura.cliente.ragione_sociale}",
            'conto': 'Crediti v/Clienti',
            'importo_entrata': fattura.importo_totale,
            'importo_uscita': None,
            'is_contabile': True, # Flag per il template
        })

    # 2. Recupera gli incassi (movimenti di tesoreria)
    incassi = Incasso.objects.select_related(
        'scadenza__fattura__cliente', 
        'conto_bancario'
    )
    movimenti_tesoreria = []
    for incasso in incassi:
        movimenti_tesoreria.append({
            'data': incasso.data_incasso,
            'tipo': 'Incasso',
            'descrizione': f"Incasso da {incasso.scadenza.fattura.cliente.ragione_sociale} (Fatt. {incasso.scadenza.fattura.numero})",
            'conto': incasso.conto_bancario.nome,
            'importo_entrata': incasso.importo_incassato,
            'importo_uscita': None,
            'is_contabile': False,
        })

    # 3. Unisce e ordina tutti i movimenti per data
    movimenti_combinati = sorted(movimenti_contabili + movimenti_tesoreria, key=lambda x: x['data'], reverse=True)

    context = {
        'movimenti': movimenti_combinati,
        'titolo_pagina': 'Elenco Movimenti di Tesoreria'
    }
    return render(request, 'tesoreria/lista_movimenti.html', context)
