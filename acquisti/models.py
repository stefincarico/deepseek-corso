from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class FatturaAcquisto(models.Model):
    """Modello per rappresentare una Fattura di Acquisto."""

    fornitore = models.ForeignKey(
        'fornitori.Fornitore',
        on_delete=models.PROTECT,
        related_name='fatture_acquisto',
        verbose_name="Fornitore"
    )
    numero = models.CharField(max_length=50, verbose_name="Numero Fattura")
    data_documento = models.DateField(verbose_name="Data Documento")
    data_ricezione = models.DateField(verbose_name="Data Ricezione", default=timezone.now)
    
    importo_totale = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Imponibile")
    aliquota_iva = models.DecimalField(max_digits=5, decimal_places=2, default=22.00, verbose_name="Aliquota IVA")
    
    descrizione = models.TextField(blank=True)
    
    STATO_FATTURA = [
        ('da_registrare', 'Da Registrare'),
        ('registrata', 'Registrata'),
        ('parzialmente_pagata', 'Parzialmente Pagata'),
        ('pagata', 'Pagata'),
    ]
    
    stato = models.CharField(max_length=20, choices=STATO_FATTURA, default='da_registrare')

    def totale_complessivo(self):
        """Calcola il totale solo se abbiamo i dati necessari, altrimenti restituisce 0."""
        if self.importo_totale is None or self.aliquota_iva is None:
            return Decimal('0.00')
        return self.importo_totale + (self.importo_totale * self.aliquota_iva / 100)

    def importo_pagato(self):
        """Calcola l'importo totale già pagato per questa fattura."""
        if not hasattr(self, 'scadenze_acquisto') or not self.scadenze_acquisto.exists():
            return Decimal('0.00')
        return sum(scadenza.importo_pagato() for scadenza in self.scadenze_acquisto.all())
    
    def importo_residuo(self):
        return self.totale_complessivo() - self.importo_pagato()

    def stato_automatico(self):
        if not self.pk:
            return 'da_registrare'
        importo_pagato = self.importo_pagato()
        if importo_pagato >= self.totale_complessivo():
            return 'pagata'
        elif importo_pagato > 0:
            return 'parzialmente_pagata'
        else:
            return 'registrata'

    def save(self, *args, **kwargs):
        self.stato = self.stato_automatico()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fattura Acquisto n. {self.numero} da {self.fornitore.ragione_sociale}"

    class Meta:
        verbose_name = "Fattura di Acquisto"
        verbose_name_plural = "Fatture di Acquisto"
        ordering = ['-data_documento']


class ScadenzaFatturaAcquisto(models.Model):
    """Modello per le scadenze di pagamento delle fatture di acquisto."""
    
    fattura_acquisto = models.ForeignKey(
        FatturaAcquisto,
        on_delete=models.CASCADE,
        related_name='scadenze_acquisto',
        verbose_name="Fattura di Riferimento"
    )
    data_scadenza = models.DateField(verbose_name="Data Scadenza Pagamento")
    importo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Importo Scadenza")
    
    STATO_SCADENZA = [
        ('da_pagare', 'Da Pagare'),
        ('parzialmente_pagata', 'Parzialmente Pagata'),
        ('pagata', 'Pagata'),
    ]
    
    stato = models.CharField(max_length=20, choices=STATO_SCADENZA, default='da_pagare')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data Effettivo Pagamento")

    def importo_pagato(self):
        if hasattr(self, 'pagamenti') and self.pagamenti.exists():
            return sum(pagamento.importo_pagato for pagamento in self.pagamenti.all())
        return Decimal('0.00')

    def importo_residuo(self):
        return self.importo - self.importo_pagato()

    def is_scaduta(self):
        if not self.data_scadenza:
            return False
        return (self.data_scadenza < timezone.now().date() and self.stato != 'pagata')

    def __str__(self):
        return f"Scadenza {self.fattura_acquisto.numero} - €{self.importo} del {self.data_scadenza}"

    class Meta:
        verbose_name = "Scadenza Fattura di Acquisto"
        verbose_name_plural = "Scadenze Fatture di Acquisto"
        ordering = ['data_scadenza']
