from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class Fornitore(models.Model):
    """Modello per l'anagrafica fornitori."""
    
    ragione_sociale = models.CharField(
        max_length=200,
        verbose_name="Ragione Sociale"
    )
    
    indirizzo = models.CharField(max_length=255, verbose_name="Indirizzo", blank=True)
    citta = models.CharField(max_length=100, verbose_name="Città", blank=True)
    cap = models.CharField(
        max_length=5,
        verbose_name="CAP",
        blank=True,
        validators=[RegexValidator(r'^\d{5}$', 'Il CAP deve avere 5 numeri')]
    )
    provincia = models.CharField(max_length=2, verbose_name="Provincia", blank=True)
    
    partita_iva = models.CharField(
        max_length=11,
        verbose_name="Partita IVA",
        unique=True,
        validators=[RegexValidator(r'^\d{11}$', 'La P.IVA deve avere 11 numeri')]
    )
    
    codice_fiscale = models.CharField(max_length=16, verbose_name="Codice Fiscale", blank=True)
    
    email = models.EmailField(verbose_name="Email", blank=True)
    telefono = models.CharField(max_length=20, verbose_name="Telefono", blank=True)
    
    STATO_FORNITORE = [
        ('attivo', 'Attivo'),
        ('inattivo', 'Inattivo'),
        ('bloccato', 'Bloccato'),
    ]
    
    stato = models.CharField(
        max_length=10,
        choices=STATO_FORNITORE,
        default='attivo',
        verbose_name="Stato Fornitore"
    )
    
    def indirizzo_completo(self):
        parts = [self.indirizzo, self.citta, self.cap, self.provincia]
        return ", ".join(filter(None, parts))

    def clean(self):
        if not self.partita_iva and not self.codice_fiscale:
            raise ValidationError("Inserire almeno Partita IVA o Codice Fiscale")
    
    def __str__(self):
        return self.ragione_sociale
    
    class Meta:
        verbose_name = "Fornitore"
        verbose_name_plural = "Fornitori"
        ordering = ['ragione_sociale']