from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Fattura(models.Model):
    """
    Modello per rappresentare una Fattura nel sistema.
    Contiene i dati generali della fattura.
    """

    cliente = models.ForeignKey(
        'clienti.Cliente',  # Referenza all'app clienti
        on_delete=models.PROTECT,  # Impedisce cancellazione se ci sono fatture
        related_name='fatture',
        verbose_name="Cliente",
        help_text="Seleziona il cliente a cui intestare la fattura"
    )
    
    numero = models.CharField(
        max_length=20,
        verbose_name="Numero Fattura"
    )
    
    data_emissione = models.DateField(
        verbose_name="Data Emissione"
    )
    
    importo_totale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Totale Fattura"
    )
    
    aliquota_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=22.00,
        verbose_name="Aliquota IVA"
    )
    
    descrizione = models.TextField(blank=True)
    
    STATO_FATTURA = [
        ('bozza', 'Bozza'),
        ('emessa', 'Emessa'),
        ('parzialmente_pagata', 'Parzialmente Pagata'),
        ('pagata', 'Pagata'),
    ]
    
    stato = models.CharField(
        max_length=20,
        choices=STATO_FATTURA,
        default='bozza'
    )

    def importo_incassato(self):
        """Calcola l'importo totale già incassato per questa fattura sommando gli incassi di tutte le sue scadenze."""
        if not hasattr(self, 'scadenze') or not self.scadenze.exists():
            return Decimal('0.00')
        
        total_incassato = sum(scadenza.importo_incassato() for scadenza in self.scadenze.all())
        return total_incassato
    
    def importo_residuo(self):
        """Calcola l'importo ancora da incassare per la fattura."""
        return self.totale_complessivo() - self.importo_incassato()
    
    def percentuale_incassata(self):
        """Calcola la percentuale già incassata della fattura."""
        if self.totale_complessivo() and self.totale_complessivo() > 0:
            return (self.importo_incassato() / self.totale_complessivo()) * 100
        return Decimal('0.00')
    
    def stato_automatico(self):
        """Determina lo stato automaticamente in base agli incassi"""
        if not self.pk:  # Se la fattura non è ancora salvata, è una bozza
            return 'bozza'
            
        importo_incassato = self.importo_incassato()
        
        if importo_incassato >= self.totale_complessivo():
            return 'pagata'
        elif importo_incassato > 0:
            return 'parzialmente_pagata'
        else:
            return 'emessa'
    
    # Override del metodo save per aggiornare lo stato automaticamente
    def save(self, *args, **kwargs):
        # Aggiorna lo stato in base agli incassi
        self.stato = self.stato_automatico()
        super().save(*args, **kwargs)
    
    # METODI CORRETTI - CON CONTROLLO None
    def calcola_iva(self):
        """Calcola l'IVA solo se abbiamo i dati necessari"""
        if self.importo_totale is None or self.aliquota_iva is None:
            return 0  # Evita l'errore se i dati non sono ancora stati inseriti
        return (self.importo_totale * self.aliquota_iva) / 100
    
    def totale_complessivo(self):
        """Calcola il totale solo se abbiamo i dati necessari"""
        if self.importo_totale is None:
            return 0  # Evita l'errore durante la creazione
        return self.importo_totale + self.calcola_iva()
    
    def totale_scadenze(self):
        """Calcola il totale delle scadenze solo se esistono"""
        if not hasattr(self, 'scadenze') or not self.scadenze.exists():
            return 0
        return sum(scadenza.importo for scadenza in self.scadenze.all())
    
    # Validazione: la somma delle scadenze deve essere uguale all'importo totale
    def clean(self):
        # Solo se la fattura è già salvata e ha scadenze
        if self.pk and hasattr(self, 'scadenze') and self.scadenze.exists():
            totale_scadenze = self.totale_scadenze()
            if totale_scadenze != self.totale_complessivo():
                raise ValidationError(
                    f"La somma delle scadenze ({totale_scadenze}) non corrisponde "
                    f"all'importo totale IVA inclusa della fattura ({self.totale_complessivo()})"
                )
    
    def __str__(self):
        if self.numero and self.importo_totale:
            return f"Fattura {self.numero} - €{self.importo_totale}"
        return f"Fattura (bozza)"


class ScadenzaFattura(models.Model):
    """
    Modello per rappresentare le singole scadenze di pagamento di una fattura.
    Una fattura può avere multiple scadenze (rate).
    """
    
    # Relazione con la fattura - "chiave esterna"
    fattura = models.ForeignKey(
        Fattura,
        on_delete=models.CASCADE,
        related_name='scadenze',
        verbose_name="Fattura di Riferimento"
    )
    
    data_scadenza = models.DateField(
        verbose_name="Data Scadenza Pagamento"
    )
    
    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Scadenza"
    )
    
    STATO_SCADENZA = [
        ('da_pagare', 'Da Pagare'),
        ('parzialmente_pagata', 'Parzialmente Pagata'),
        ('pagata', 'Pagata'),
        # Lo stato 'scaduta' è gestito dinamicamente da is_scaduta()
    ]
    
    stato = models.CharField(
        max_length=20,
        choices=STATO_SCADENZA,
        default='da_pagare'
    )
    
    data_pagamento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Effettiva Pagamento"
    )
    
    def importo_incassato(self):
        """Calcola l'importo totale già incassato per questa scadenza."""
        if hasattr(self, 'incassi') and self.incassi.exists():
            return sum(incasso.importo_incassato for incasso in self.incassi.all())
        return Decimal('0.00')

    def importo_residuo(self):
        """Calcola l'importo ancora da incassare per questa scadenza."""
        return self.importo - self.importo_incassato()

    def percentuale_incassata(self):
        """Calcola la percentuale già incassata per questa scadenza."""
        if self.importo > 0:
            return (self.importo_incassato() / self.importo) * 100
        return Decimal('0.00')
    # Metodo per verificare se la scadenza è scaduta
    def is_scaduta(self):
        if not self.data_scadenza:
            return False
        return (self.data_scadenza < timezone.now().date() 
                and self.stato != 'pagata')
    
    # Validazione: data pagamento non può essere prima della scadenza
    def clean(self):
        if self.data_pagamento and self.data_scadenza:
            if self.data_pagamento < self.data_scadenza:
                raise ValidationError(
                    "La data di pagamento non può essere precedente alla data di scadenza"
                )
    
    def __str__(self):
        if self.fattura and self.importo and self.data_scadenza:
            return f"Scadenza {self.fattura.numero} - €{self.importo} del {self.data_scadenza}"
        return "Scadenza (bozza)"
    
    class Meta:
        verbose_name = "Scadenza Fattura"
        verbose_name_plural = "Scadenze Fatture"
        ordering = ['data_scadenza']