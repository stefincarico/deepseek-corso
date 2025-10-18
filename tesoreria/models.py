from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
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
    
    # Saldo del conto
    saldo_attuale = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Attuale",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Stato del conto
    attivo = models.BooleanField(
        default=True,
        verbose_name="Conto Attivo",
        help_text="Se deselezionato, il conto non sarà più utilizzabile per nuovi movimenti"
    )
    
    # Metodi per la gestione del saldo
    def aggiorna_saldo(self, importo, operazione='accredito'):
        """
        Aggiorna il saldo del conto in modo sicuro.
        operazione: 'accredito' o 'addebito'
        """
        if operazione == 'accredito':
            self.saldo_attuale += importo
        elif operazione == 'addebito':
            if self.saldo_attuale >= importo:
                self.saldo_attuale -= importo
            else:
                raise ValidationError(f"Saldo insufficiente sul conto {self.nome}")
        else:
            raise ValidationError("Operazione non valida")
        
        self.save()
    
    def verifica_disponibilita(self, importo):
        """Verifica se il conto ha sufficiente disponibilità"""
        return self.saldo_attuale >= importo
    
    # Validazioni
    def clean(self):
        # Se è un conto bancario, richiedi IBAN
        if self.tipo_conto == 'bancario' and not self.iban:
            raise ValidationError("Per i conti bancari è richiesto l'IBAN")
        
        # Se è cassa, pulisci i campi bancari
        if self.tipo_conto == 'cassa':
            self.iban = ''
            self.nome_banca = ''
    
    def __str__(self):
        return f"{self.nome} - Saldo: €{self.saldo_attuale:,.2f}"
    
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
