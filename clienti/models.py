from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from decimal import Decimal

class Cliente(models.Model):
    """
    Modello per l'anagrafica clienti.
    Equivale alla scheda cliente nel tuo archivio cartaceo.
    """
    
    # Dati anagrafici base
    ragione_sociale = models.CharField(
        max_length=200,
        verbose_name="Ragione Sociale",
        help_text="Nome completo dell'azienda o della persona"
    )
    
    # Indirizzo
    indirizzo = models.CharField(
        max_length=255,
        verbose_name="Indirizzo",
        blank=True
    )
    
    citta = models.CharField(
        max_length=100,
        verbose_name="Città",
        blank=True
    )
    
    cap = models.CharField(
        max_length=5,
        verbose_name="CAP",
        blank=True,
        validators=[RegexValidator(r'^\d{5}$', 'Il CAP deve avere 5 numeri')]
    )
    
    provincia = models.CharField(
        max_length=2,
        verbose_name="Provincia",
        blank=True,
        help_text="Sigla provincia (es: RM)"
    )
    
    # Dati fiscali
    partita_iva = models.CharField(
        max_length=11,
        verbose_name="Partita IVA",
        unique=True,
        validators=[RegexValidator(r'^\d{11}$', 'La P.IVA deve avere 11 numeri')],
        help_text="Partita IVA (11 cifre)"
    )
    
    codice_fiscale = models.CharField(
        max_length=16,
        verbose_name="Codice Fiscale",
        blank=True,
        help_text="Codice Fiscale (16 caratteri)"
    )
    
    # Contatti
    email = models.EmailField(
        verbose_name="Email",
        blank=True
    )
    
    telefono = models.CharField(
        max_length=20,
        verbose_name="Telefono",
        blank=True
    )
    
    # Stato del cliente
    STATO_CLIENTE = [
        ('attivo', 'Attivo'),
        ('inattivo', 'Inattivo'),
        ('bloccato', 'Bloccato'),
    ]
    
    stato = models.CharField(
        max_length=10,
        choices=STATO_CLIENTE,
        default='attivo',
        verbose_name="Stato Cliente"
    )
    
    # Metodi utili
    def indirizzo_completo(self):
        """Restituisce l'indirizzo completo formattato"""
        parts = [self.indirizzo, self.citta, self.cap, self.provincia]
        return ", ".join(filter(None, parts))
    
    def fatturato_totale(self):
        """Calcola il fatturato totale per questo cliente"""
        from fatture.models import Fattura
        # Usiamo l'aggregazione per efficienza
        totale = self.fatture.aggregate(totale=Sum('importo_totale'))['totale']
        return totale or Decimal('0.00')
    
    def credito_residuo(self):
        """Calcola il credito totale residuo del cliente in modo ottimizzato."""
        # Calcola il totale fatturato IVA inclusa
        aggregati = self.fatture.aggregate(
            totale_imponibile=Sum('importo_totale'),
            totale_iva=Sum(F('importo_totale') * F('aliquota_iva') / 100)
        )
        fatturato_complessivo = (aggregati['totale_imponibile'] or Decimal('0.00')) + (aggregati['totale_iva'] or Decimal('0.00'))
        
        # Calcola il totale incassato attraversando le relazioni
        incassato = self.fatture.aggregate(
            totale_incassato=Sum('scadenze__incassi__importo_incassato')
        )['totale_incassato'] or Decimal('0.00')
        
        return fatturato_complessivo - incassato
    
    # Validazione: almeno P.IVA o Codice Fiscale
    def clean(self):
        if not self.partita_iva and not self.codice_fiscale:
            raise ValidationError("Inserire almeno Partita IVA o Codice Fiscale")
    
    def __str__(self):
        return f"{self.ragione_sociale} - P.IVA: {self.partita_iva}"
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clienti"
        ordering = ['ragione_sociale']