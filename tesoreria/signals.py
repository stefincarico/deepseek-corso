from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Incasso, Spesa
from fatture.models import ScadenzaFattura
from acquisti.models import ScadenzaFatturaAcquisto

@receiver(post_save, sender=Incasso)
def gestisci_post_save_incasso(sender, instance, created, **kwargs):
    """
    Dopo aver salvato un Incasso:
    1. Se è un nuovo incasso, aggiorna il saldo del conto.
    2. Aggiorna lo stato della scadenza e della fattura.
    """
    # 1. Aggiorna il saldo del conto solo alla creazione
    if created:
        instance.conto_bancario.aggiorna_saldo(instance.importo_incassato, 'accredito')

    # 2. Aggiorna gli stati
    scadenza = instance.scadenza
    
    importo_residuo = scadenza.importo_residuo()

    # Aggiorna lo stato della scadenza
    if importo_residuo <= 0:
        scadenza.stato = 'pagata'
        scadenza.data_pagamento = instance.data_incasso
    elif importo_residuo < scadenza.importo:
        scadenza.stato = 'parzialmente_pagata'
        scadenza.data_pagamento = None
    else:
        scadenza.stato = 'da_pagare'
        scadenza.data_pagamento = None
    
    scadenza.save(update_fields=['stato', 'data_pagamento'])

    # Aggiorna anche lo stato della fattura collegata
    fattura = scadenza.fattura
    fattura.save() # Il metodo save della fattura ricalcola già lo stato

@receiver(post_delete, sender=Incasso)
def gestisci_post_delete_incasso(sender, instance, **kwargs):
    """
    Dopo aver cancellato un Incasso, storna l'importo dal conto
    e aggiorna gli stati.
    """
    # Storna l'importo dal saldo del conto
    instance.conto_bancario.aggiorna_saldo(instance.importo_incassato, 'addebito')
    
    # Richiama la stessa logica di aggiornamento stati
    gestisci_post_save_incasso(sender, instance, created=False, **kwargs)


@receiver(post_save, sender=Spesa)
def gestisci_post_save_spesa(sender, instance, created, **kwargs):
    """
    Dopo aver salvato una Spesa:
    1. Se è un nuovo pagamento, aggiorna il saldo del conto.
    2. Aggiorna lo stato della scadenza e della fattura di acquisto.
    """
    if created:
        instance.conto_bancario.aggiorna_saldo(instance.importo_pagato, 'addebito')

    scadenza = instance.scadenza
    importo_residuo = scadenza.importo_residuo()

    if importo_residuo <= 0:
        scadenza.stato = 'pagata'
        scadenza.data_pagamento = instance.data_pagamento
    elif importo_residuo < scadenza.importo:
        scadenza.stato = 'parzialmente_pagata'
        scadenza.data_pagamento = None
    else:
        scadenza.stato = 'da_pagare'
        scadenza.data_pagamento = None
    
    scadenza.save(update_fields=['stato', 'data_pagamento'])

    fattura = scadenza.fattura_acquisto
    fattura.save()

@receiver(post_delete, sender=Spesa)
def gestisci_post_delete_spesa(sender, instance, **kwargs):
    """
    Dopo aver cancellato una Spesa, riaccredita l'importo sul conto
    e aggiorna gli stati.
    """
    instance.conto_bancario.aggiorna_saldo(instance.importo_pagato, 'accredito')
    gestisci_post_save_spesa(sender, instance, created=False, **kwargs)