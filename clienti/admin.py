from django.contrib import admin
from .models import Cliente
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from decimal import Decimal

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'ragione_sociale', 
        'partita_iva',
        'citta',
        'stato',
        'list_fatturato_totale',
        'list_credito_residuo',
    ]
    
    list_filter = ['stato', 'citta']
    search_fields = ['ragione_sociale', 'partita_iva', 'codice_fiscale']
    
    # readonly_fields per la vista di dettaglio.
    # Questi devono essere nomi di campi o metodi del modello o dell'admin.
    # Usiamo i metodi del modello 'Cliente' che sono già ottimizzati
    # per un singolo oggetto.
    readonly_fields = ['fatturato_totale', 'credito_residuo']

    def get_queryset(self, request):
        """
        Ottimizza il queryset per la vista elenco pre-calcolando i totali
        con una singola query usando annotate.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            # Calcola il totale fatturato per ogni cliente
            total_fatturato=Coalesce(Sum('fatture__importo_totale'), Decimal('0.00')),
            # Calcola il totale incassato per ogni cliente
            total_incassato=Coalesce(Sum('fatture__scadenze__incassi__importo_incassato'), Decimal('0.00'))
        ).annotate(
            # Calcola il residuo direttamente nel database
            total_residuo=F('total_fatturato') - F('total_incassato')
        )
        return queryset

    # Metodi per visualizzare i dati annotati nella VISTA ELENCO (list_display).
    # Usano gli attributi pre-calcolati da get_queryset per la massima efficienza.
    @admin.display(description='Fatturato Totale')
    def list_fatturato_totale(self, obj):
        return obj.total_fatturato
    list_fatturato_totale.admin_order_field = 'total_fatturato'

    @admin.display(description='Credito Residuo')
    def list_credito_residuo(self, obj):
        return obj.total_residuo
    list_credito_residuo.admin_order_field = 'total_residuo'