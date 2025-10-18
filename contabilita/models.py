from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

class PianoDeiConti(models.Model):
    """
    Modello per il Piano dei Conti contabile.
    Rappresenta la mappa completa dei conti utilizzabili in prima nota.
    """
    
    # Classi del piano dei conti
    CLASSE_CONTO = [
        ('patrimoniale', 'Conto Patrimoniale'),
        ('economico', 'Conto Economico'),
        ('ordine', 'Conto d\'Ordine'),
    ]
    
    # Natura del conto (Dare/Avere)
    NATURA_CONTO = [
        ('dare', 'Dare (Attivo/Costi)'),
        ('avere', 'Avere (Passivo/Ricavi)'),
    ]
    
    codice = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Codice Conto",
        help_text="Codice del conto (es: 1.1.01, 2.2.03)"
    )
    
    descrizione = models.CharField(
        max_length=200,
        verbose_name="Descrizione Conto",
        help_text="Descrizione completa del conto"
    )
    
    classe = models.CharField(
        max_length=12,
        choices=CLASSE_CONTO,
        verbose_name="Classe Conto"
    )
    
    natura = models.CharField(
        max_length=5,
        choices=NATURA_CONTO,
        verbose_name="Natura Conto"
    )
    
    sottoconto_di = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sottoconti',
        verbose_name="Sottoconto di",
        help_text="Conto padre (per gerarchia)"
    )
    
    attivo = models.BooleanField(
        default=True,
        verbose_name="Conto Attivo",
        help_text="Se deselezionato, il conto non sarà più utilizzabile"
    )
    
    # Metodi per la gerarchia
    def livello(self):
        """Calcola il livello gerarchico del conto"""
        if not self.sottoconto_di:
            return 1
        return self.sottoconto_di.livello() + 1
    
    def conti_foglia(self):
        """Restituisce tutti i conti foglia sotto questo conto"""
        if self.sottoconti.exists():
            foglie = []
            for sottoconto in self.sottoconti.all():
                foglie.extend(sottoconto.conti_foglia())
            return foglie
        return [self]
    
    # Validazioni
    def clean(self):
        # Verifica che il codice sia nel formato corretto
        if not all(c.isdigit() or c == '.' for c in self.codice):
            raise ValidationError("Il codice conto può contenere solo numeri e punti")
        
        # Impedisce cicli nella gerarchia
        if self.sottoconto_di and self.sottoconto_di == self:
            raise ValidationError("Un conto non può essere sottoconto di se stesso")
    
    def __str__(self):
        return f"{self.codice} - {self.descrizione}"
    
    class Meta:
        verbose_name = "Conto del Piano dei Conti"
        verbose_name_plural = "Piano dei Conti"
        ordering = ['codice']


class RegistrazioneContabile(models.Model):
    """
    Modello per le registrazioni manuali in Prima Nota.
    Ogni registrazione deve rispettare il principio della partita doppia.
    """
    
    data_registrazione = models.DateField(
        verbose_name="Data Registrazione",
        help_text="Data della operazione contabile"
    )
    
    descrizione = models.TextField(
        verbose_name="Descrizione Operazione",
        help_text="Descrizione dettagliata dell'operazione"
    )
    
    # Metodi di pagamento per le operazioni di cassa/banca
    METODO_PAGAMENTO = [
        ('bonifico', 'Bonifico Bancario'),
        ('assegno', 'Assegno'),
        ('contanti', 'Contanti'),
        ('altro', 'Altro'),
    ]
    
    metodo_pagamento = models.CharField(
        max_length=10,
        choices=METODO_PAGAMENTO,
        default='bonifico',
        verbose_name="Metodo di Pagamento"
    )
    
    # Riferimento documento (numero fattura, bolletta, etc.)
    riferimento = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Riferimento Documento",
        help_text="Numero fattura, bolletta, etc."
    )
    
    # Stato della registrazione
    STATO_REGISTRAZIONE = [
        ('bozza', 'Bozza'),
        ('registrata', 'Registrata'),
        ('stornata', 'Stornata'),
    ]
    
    stato = models.CharField(
        max_length=10,
        choices=STATO_REGISTRAZIONE,
        default='bozza',
        verbose_name="Stato Registrazione"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metodo per verificare il pareggio
    def verifica_pareggio(self):
        """Verifica che la registrazione sia in pareggio (Dare = Avere)"""
        totale_dare = sum(mov.importo for mov in self.movimenti.filter(tipo_movimento='dare'))
        totale_avere = sum(mov.importo for mov in self.movimenti.filter(tipo_movimento='avere'))
        return totale_dare == totale_avere
    
    def totale_registrazione(self):
        """Calcola il totale della registrazione (somma dei movimenti in Dare)."""
        return sum(mov.importo for mov in self.movimenti.filter(tipo_movimento='dare'))
    totale_registrazione.short_description = "Totale"
    totale_registrazione.admin_order_field = 'movimenti__importo' # Permette un ordinamento approssimativo

    # Validazione partita doppia
    def clean(self):
        if self.pk:  # Solo se la registrazione è già stata salvata
            if not self.verifica_pareggio():
                raise ValidationError(
                    "La registrazione non è in pareggio! Il totale Dare deve essere uguale al totale Avere."
                )
    
    def __str__(self):
        return f"Reg. {self.data_registrazione} - {self.descrizione[:50]}"
    
    class Meta:
        verbose_name = "Registrazione Contabile"
        verbose_name_plural = "Registrazioni Contabili"
        ordering = ['-data_registrazione', '-created_at']


class MovimentoContabile(models.Model):
    """
    Modello per i singoli movimenti di una registrazione.
    Ogni registrazione ha almeno 2 movimenti (Dare e Avere).
    """
    
    registrazione = models.ForeignKey(
        RegistrazioneContabile,
        on_delete=models.CASCADE,
        related_name='movimenti',
        verbose_name="Registrazione"
    )
    
    conto = models.ForeignKey(
        PianoDeiConti,
        on_delete=models.PROTECT,
        verbose_name="Conto",
        help_text="Conto interessato dal movimento"
    )
    
    TIPO_MOVIMENTO = [
        ('dare', 'Dare'),
        ('avere', 'Avere'),
    ]
    
    tipo_movimento = models.CharField(
        max_length=5,
        choices=TIPO_MOVIMENTO,
        verbose_name="Tipo Movimento"
    )
    
    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Note aggiuntive per il singolo movimento
    note = models.TextField(
        blank=True,
        verbose_name="Note Movimento",
        help_text="Note specifiche per questo movimento"
    )
    
    def __str__(self):
        return f"{self.tipo_movimento.upper()} {self.conto.codice} - €{self.importo}"
    
    class Meta:
        verbose_name = "Movimento Contabile"
        verbose_name_plural = "Movimenti Contabili"
        ordering = ['registrazione', 'tipo_movimento']