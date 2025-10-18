from django.shortcuts import render
from .models import ContoBancario, Incasso
from fatture.models import Fattura
from contabilita.models import RegistrazioneContabile

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
