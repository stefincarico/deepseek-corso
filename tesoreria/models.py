from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from contabilita.models import PianoDeiConti, MovimentoContabile
from django.db.models import Sum
from django.utils import timezone

class ContoBancario(models.Model):
    """
    Modello per rappresentare un conto bancario o di cassa.
    Equivale al libretto di ogni conto che gestisci.
    """
    
    # Tipi di conto
    TIPO_CONTO = [
        ('bancario', 'Conto Bancario'),
        ('cassa', 'Cassa'),
        ('paypal', 'PayPal/Conto Online'),
        ('altro', 'Altro'),
    ]
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome Conto",
        help_text="Nome identificativo del conto (es: Banca Intesa Conto Corrente)"
    )
    
    tipo_conto = models.CharField(
        max_length=10,
        choices=TIPO_CONTO,
        default='bancario',
        verbose_name="Tipo Conto"
    )
    
    # Dati bancari (opzionali per cassa)
    intestatario = models.CharField(
        max_length=200,
        verbose_name="Intestatario",
        blank=True
    )
    
    iban = models.CharField(
        max_length=27,
        verbose_name="IBAN",
        blank=True,
        validators=[RegexValidator(
            regex=r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$',
            message='Inserire un IBAN valido'
        )]
    )
    
    nome_banca = models.CharField(
        max_length=100,
        verbose_name="Nome Banca",
        blank=True
    )
    
    # Collega questo conto di tesoreria a un conto del piano dei conti
    conto_contabile = models.ForeignKey(
        PianoDeiConti,
        on_delete=models.PROTECT,
        verbose_name="Conto Contabile Associato",
        null=True, blank=True, # Rendilo opzionale per ora
        limit_choices_to={'codice__startswith': '1.1.0'} # Mostra solo conti di liquidità (Cassa, Banche)
    )
    

    # Stato del conto
    attivo = models.BooleanField(
        default=True,
        verbose_name="Conto Attivo",
        help_text="Se deselezionato, il conto non sarà più utilizzabile per nuovi movimenti"
    )
    
    @property
    def saldo(self):
        """Calcola il saldo dinamicamente dai movimenti contabili."""
        if not self.conto_contabile:
            return Decimal('0.00')
        
        movimenti = MovimentoContabile.objects.filter(conto=self.conto_contabile)
        dare = movimenti.filter(tipo_movimento='dare').aggregate(tot=Sum('importo'))['tot'] or Decimal('0.00')
        avere = movimenti.filter(tipo_movimento='avere').aggregate(tot=Sum('importo'))['tot'] or Decimal('0.00')
        return dare - avere

    def verifica_disponibilita(self, importo):
        """Verifica se il conto ha sufficiente disponibilità"""
        return self.saldo >= importo
    
    # Validazioni
    def clean(self):
        # Se è cassa, pulisci i campi bancari
        if self.tipo_conto == 'cassa':
            self.iban = ''
            self.nome_banca = ''
    
    def __str__(self):
        return f"{self.nome}"
    
    class Meta:
        verbose_name = "Conto Bancario"
        verbose_name_plural = "Conti Bancari"
        ordering = ['tipo_conto', 'nome']


class Incasso(models.Model):
    """
    Modello per rappresentare un singolo incasso su una scadenza di fattura.
    Permette di gestire incassi multipli e parziali sulla stessa scadenza.
    """
    
    # Relazione con la scadenza della fattura
    scadenza = models.ForeignKey(
        'fatture.ScadenzaFattura',  # Referenza all'app fatture
        on_delete=models.CASCADE,
        related_name='incassi',
        verbose_name="Scadenza Fattura",
        help_text="Seleziona la scadenza a cui associare l'incasso"
    )
    
    # Relazione con il conto bancario
    conto_bancario = models.ForeignKey(
        ContoBancario,
        on_delete=models.PROTECT,
        related_name='incassi',
        verbose_name="Conto di Accredito",
        help_text="Seleziona il conto su cui è stato incassato l'importo"
    )
    
    # Dati dell'incasso
    data_incasso = models.DateField(
        verbose_name="Data Incasso",
        default=timezone.localdate,
        help_text="Data in cui è avvenuto materialmente l'incasso"
    )
    
    importo_incassato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Incassato",
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Importo effettivamente incassato"
    )
    
    # Metodo di pagamento
    METODO_PAGAMENTO = [
        ('bonifico', 'Bonifico Bancario'),
        ('assegno', 'Assegno'),
        ('contanti', 'Contanti'),
        ('pos', 'Carta di Credito/POS'),
        ('ria', 'RID/Riba'),
        ('altro', 'Altro'),
    ]
    
    metodo_pagamento = models.CharField(
        max_length=10,
        choices=METODO_PAGAMENTO,
        default='bonifico',
        verbose_name="Metodo di Pagamento"
    )
    
    note = models.TextField(
        blank=True,
        verbose_name="Note",
        help_text="Eventuali note sull'incasso (riferimenti, causale, etc.)"
    )
    
    def delete(self, *args, **kwargs):
        """
        Override del metodo delete per:
        1. Stornare l'importo dal conto bancario
        2. Aggiornare lo stato della scadenza
        """
        # Storna l'importo dal conto bancario
        self.conto_bancario.aggiorna_saldo(self.importo_incassato, 'addebito')
        
        # Cancella l'incasso
        super().delete(*args, **kwargs)
    
    # Validazioni
    def __str__(self):
        return f"Incasso {self.scadenza.fattura.numero} - €{self.importo_incassato} del {self.data_incasso}"
    
    class Meta:
        verbose_name = "Incasso"
        verbose_name_plural = "Incassi"
        ordering = ['-data_incasso']


class Spesa(models.Model):
    """Modello per rappresentare una singola spesa/pagamento su una scadenza di acquisto."""
    
    scadenza = models.ForeignKey(
        'acquisti.ScadenzaFatturaAcquisto',
        on_delete=models.CASCADE,
        related_name='pagamenti',
        verbose_name="Scadenza Fattura di Acquisto"
    )
    
    conto_bancario = models.ForeignKey(
        ContoBancario,
        on_delete=models.PROTECT,
        related_name='spese',
        verbose_name="Conto di Addebito"
    )
    
    data_pagamento = models.DateField(
        verbose_name="Data Pagamento",
        default=timezone.localdate
    )
    
    importo_pagato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Importo Pagato",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    metodo_pagamento = models.CharField(
        max_length=10,
        choices=Incasso.METODO_PAGAMENTO,
        default='bonifico',
        verbose_name="Metodo di Pagamento"
    )
    
    note = models.TextField(blank=True, verbose_name="Note")

    def __str__(self):
        return f"Pagamento {self.scadenza.fattura_acquisto.numero} - €{self.importo_pagato} del {self.data_pagamento}"

    class Meta:
        verbose_name = "Spesa/Pagamento"
        verbose_name_plural = "Spese/Pagamenti"
        ordering = ['-data_pagamento']
