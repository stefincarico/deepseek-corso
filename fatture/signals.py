from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fattura
from contabilita.models import RegistrazioneContabile, MovimentoContabile, PianoDeiConti

@receiver(post_save, sender=Fattura)
def contabilizza_fattura_emessa(sender, instance, created, **kwargs):
    """
    Crea la scrittura contabile quando una fattura viene emessa.
    Si attiva quando lo stato passa da 'bozza' a 'emessa'.
    """
    # Controlla se la fattura è stata appena creata o se il suo stato è cambiato
    if instance.stato == 'emessa' and not RegistrazioneContabile.objects.filter(riferimento=f"Fattura n.{instance.numero}").exists():
        
        # Conti di riferimento
        conto_clienti = PianoDeiConti.objects.get(codice='1.1.03') # Crediti v/Clienti
        conto_ricavi = PianoDeiConti.objects.get(codice='4.1.02') # Ricavi Vendite Servizi (esempio)
        conto_iva_debito = PianoDeiConti.objects.get(codice='2.1.02') # Debiti Tributari (per l'IVA)

        # Crea la registrazione contabile
        reg = RegistrazioneContabile.objects.create(
            data_registrazione=instance.data_emissione,
            descrizione=f"Emissione fattura n. {instance.numero} a {instance.cliente.ragione_sociale}",
            riferimento=f"Fattura n.{instance.numero}",
            stato='registrata'
        )

        # DARE: Crediti v/Clienti (per il totale complessivo)
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_clienti, tipo_movimento='dare', importo=instance.totale_complessivo()
        )
        # AVERE: Ricavi (per l'imponibile)
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_ricavi, tipo_movimento='avere', importo=instance.importo_totale
        )
        # AVERE: IVA a Debito
        MovimentoContabile.objects.create(
            registrazione=reg, conto=conto_iva_debito, tipo_movimento='avere', importo=instance.calcola_iva()
        )