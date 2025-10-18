from django.contrib import admin
from .models import ContoBancario, Incasso, Spesa
from django.utils.html import format_html
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

@admin.register(Incasso)
class IncassoAdmin(admin.ModelAdmin):
    list_display = [
        'scadenza_display',
        'conto_bancario',
        'data_incasso',
        'importo_incassato',
        'metodo_pagamento',
        'residuo_scadenza_display',
        'percentuale_incassata_display'
    ]
    
    list_filter = ['metodo_pagamento', 'data_incasso', 'conto_bancario']
    search_fields = ['scadenza__fattura__numero', 'scadenza__fattura__cliente__ragione_sociale']
    
    # Campi calcolati per la visualizzazione
    def scadenza_display(self, obj):
        return f"{obj.scadenza.fattura.numero} - €{obj.scadenza.importo}"
    scadenza_display.short_description = "Scadenza"
    
    def residuo_scadenza_display(self, obj):
        residuo = obj.scadenza.importo_residuo()
        if residuo == 0:
            return "✅ Saldata"
        elif residuo == obj.scadenza.importo:
            return f"€{residuo}"
        else:
            return f"€{residuo} (parziale)"
    residuo_scadenza_display.short_description = "Residuo"
    
    def percentuale_incassata_display(self, obj):
        percentuale = obj.scadenza.percentuale_incassata()
        return f"{percentuale:.1f}%"
    percentuale_incassata_display.short_description = "% Incassato"
    
    # Filtro per mostrare solo scadenze non completamente pagate
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "scadenza":
            from fatture.models import ScadenzaFattura
            # Annotiamo il queryset per calcolare il totale già incassato per ogni scadenza
            # Usiamo Coalesce per gestire le scadenze senza incassi (Sum restituirebbe None)
            scadenze_aperte = ScadenzaFattura.objects.annotate(
                totale_incassato=Coalesce(Sum('incassi__importo_incassato'), Decimal('0.00'), output_field=DecimalField())
            ).filter(
                importo__gt=F('totale_incassato')
            )
            
            kwargs["queryset"] = scadenze_aperte
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Spesa)
class SpesaAdmin(admin.ModelAdmin):
    list_display = ['scadenza', 'conto_bancario', 'data_pagamento', 'importo_pagato']
    list_filter = ['data_pagamento', 'conto_bancario']
    search_fields = ['scadenza__fattura_acquisto__numero', 'scadenza__fattura_acquisto__fornitore__ragione_sociale']