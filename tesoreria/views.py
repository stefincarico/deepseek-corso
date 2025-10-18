from django.shortcuts import render, get_object_or_404
from .models import ContoBancario, Incasso
from fatture.models import Fattura
from contabilita.models import RegistrazioneContabile, MovimentoContabile
from decimal import Decimal

def saldi_conti(request):
    """Mostra un elenco di tutti i conti con i relativi saldi."""
    conti = ContoBancario.objects.filter(attivo=True)
    context = {
        'conti': conti,
        'titolo_pagina': 'Saldi Conti'
    }
    return render(request, 'tesoreria/saldi_conti.html', context)

def lista_movimenti(request):
    """Mostra il libro giornale con tutte le registrazioni contabili."""
    registrazioni = RegistrazioneContabile.objects.prefetch_related(
        'movimenti__conto'
    ).order_by('-data_registrazione', '-id')

    context = {
        'registrazioni': registrazioni,
        'titolo_pagina': 'Libro Giornale'
    }
    return render(request, 'tesoreria/lista_movimenti.html', context)

def estratto_conto(request, pk):
    """Mostra l'estratto conto di un singolo conto di tesoreria."""
    conto = get_object_or_404(ContoBancario, pk=pk)
    movimenti_con_saldo = []
    
    if conto.conto_contabile:
        movimenti = MovimentoContabile.objects.filter(
            conto=conto.conto_contabile
        ).select_related('registrazione').order_by('registrazione__data_registrazione', 'registrazione__id')

        saldo_progressivo = Decimal('0.00')
        for mov in movimenti:
            if mov.tipo_movimento == 'dare':
                saldo_progressivo += mov.importo
            else: # avere
                saldo_progressivo -= mov.importo
            
            movimenti_con_saldo.append({
                'movimento': mov,
                'saldo_progressivo': saldo_progressivo
            })

    context = {
        'conto': conto,
        'movimenti': movimenti_con_saldo,
        'titolo_pagina': f"Estratto Conto: {conto.nome}"
    }
    return render(request, 'tesoreria/estratto_conto.html', context)
