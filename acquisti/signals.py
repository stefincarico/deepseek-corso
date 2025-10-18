from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FatturaAcquisto
from contabilita.models import RegistrazioneContabile, MovimentoContabile, PianoDeiConti

@receiver(post_save, sender=FatturaAcquisto)
def contabilizza_fattura_acquisto(sender, instance, created, **kwargs):
    """
    Crea la scrittura contabile quando una fattura di acquisto viene registrata.
    Si attiva quando lo stato è 'registrata'.
    """
    # Controlla che la fattura sia registrata e che non esista già una scrittura contabile
    if instance.stato == 'registrata' and not RegistrazioneContabile.objects.filter(riferimento=f"Fatt. Acquisto n.{instance.numero}").exists():
        
        # Conti di riferimento
        conto_fornitori = PianoDeiConti.objects.get(codice='2.1.01') # Debiti v/Fornitori
        conto_acquisti = PianoDeiConti.objects.get(codice='3.1.01') # Acquisti Merci (esempio)
        conto_iva = PianoDeiConti.objects.get(codice='2.1.02') # Debiti Tributari (per IVA a credito)

        # Crea la registrazione contabile
        reg = RegistrazioneContabile.objects.create(
            data_registrazione=instance.data_documento,
            descrizione=f"Registrazione fattura acquisto n. {instance.numero} da {instance.fornitore.ragione_sociale}",
            riferimento=f"Fatt. Acquisto n.{instance.numero}",
            stato='registrata'
        )

        # DARE: Acquisti Merci (per l'imponibile)
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_acquisti, tipo_movimento='dare', importo=instance.importo_totale
        )
        # DARE: IVA a Credito
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_iva, tipo_movimento='dare', importo=instance.calcola_iva()
        )
        # AVERE: Debiti v/Fornitori (per il totale complessivo)
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_fornitori, tipo_movimento='avere', importo=instance.totale_complessivo()
        )