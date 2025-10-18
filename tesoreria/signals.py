from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Incasso, Spesa
from contabilita.models import RegistrazioneContabile, MovimentoContabile, PianoDeiConti
from fatture.models import ScadenzaFattura
from acquisti.models import ScadenzaFatturaAcquisto

@receiver(post_save, sender=Incasso)
def gestisci_post_save_incasso(sender, instance, created, **kwargs):
    """
    Dopo aver salvato un Incasso, aggiorna lo stato della scadenza/fattura
    e, se è un nuovo incasso, crea la scrittura contabile.
    """
    if created:
        # Crea la registrazione contabile
        reg = RegistrazioneContabile.objects.create(
            data_registrazione=instance.data_incasso,
            descrizione=f"Incasso fattura {instance.scadenza.fattura.numero}",
            stato='registrata'
        )
        # DARE: Cassa/Banca (aumenta)
        MovimentoContabile.objects.create(
            registrazione=reg,
            conto=instance.conto_bancario.conto_contabile,
            tipo_movimento='dare',
            importo=instance.importo_incassato
        )
        # AVERE: Crediti v/Clienti (diminuisce)
        conto_clienti = PianoDeiConti.objects.get(codice='1.1.03')
        MovimentoContabile.objects.create(
            registrazione=reg,
            conto=conto_clienti,
            tipo_movimento='avere',
            importo=instance.importo_incassato
        )

    # Aggiorna gli stati della fattura e della scadenza
    scadenza = instance.scadenza
    importo_residuo = scadenza.importo_residuo()

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

    fattura = scadenza.fattura
    fattura.save() # Il metodo save della fattura ricalcola già lo stato

@receiver(post_delete, sender=Incasso)
def gestisci_post_delete_incasso(sender, instance, **kwargs):
    """
    Dopo aver cancellato un Incasso, crea la scrittura di storno
    e aggiorna gli stati.
    """
    # Qui andrebbe la logica per creare una scrittura di storno.
    # Per ora, ci limitiamo ad aggiornare gli stati.
    gestisci_post_save_incasso(sender, instance, created=False, **kwargs)


@receiver(post_save, sender=Spesa)
def gestisci_post_save_spesa(sender, instance, created, **kwargs):
    """
    Dopo aver salvato una Spesa, aggiorna gli stati e crea la scrittura contabile.
    """
    if created:
        # Crea la registrazione contabile
        reg = RegistrazioneContabile.objects.create(
            data_registrazione=instance.data_pagamento,
            descrizione=f"Pagamento fattura fornitore {instance.scadenza.fattura_acquisto.numero}",
            stato='registrata'
        )
        # DARE: Debiti v/Fornitori (diminuisce)
        conto_fornitori = PianoDeiConti.objects.get(codice='2.1.01')
        MovimentoContabile.objects.create(
            registrazione=reg,
            conto=conto_fornitori,
            tipo_movimento='dare',
            importo=instance.importo_pagato
        )
        # AVERE: Cassa/Banca (diminuisce)
        MovimentoContabile.objects.create(
            registrazione=reg,
            conto=instance.conto_bancario.conto_contabile,
            tipo_movimento='avere',
            importo=instance.importo_pagato
        )

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
    """Dopo aver cancellato una Spesa, aggiorna gli stati."""
    gestisci_post_save_spesa(sender, instance, created=False, **kwargs)