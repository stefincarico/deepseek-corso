from django.contrib import admin
from .models import FatturaAcquisto, ScadenzaFatturaAcquisto
from django.utils.html import format_html

class ScadenzaFatturaAcquistoInline(admin.TabularInline):
    model = ScadenzaFatturaAcquisto
    extra = 1

@admin.register(FatturaAcquisto)
class FatturaAcquistoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'fornitore', 'data_documento', 'totale_complessivo', 'stato']
    list_filter = ['stato', 'fornitore']
    search_fields = ['numero', 'fornitore__ragione_sociale']
    inlines = [ScadenzaFatturaAcquistoInline]
    readonly_fields = ['importo_pagato', 'importo_residuo']

@admin.register(ScadenzaFatturaAcquisto)
class ScadenzaFatturaAcquistoAdmin(admin.ModelAdmin):
    list_display = [
        'fattura_acquisto', 
        'fornitore_display', 
        'data_scadenza', 
        'importo', 
        'importo_residuo_display', 
        'stato_display'
    ]
    list_filter = ['stato', 'data_scadenza']
    search_fields = ['fattura_acquisto__numero', 'fattura_acquisto__fornitore__ragione_sociale']
    readonly_fields = ['importo_pagato', 'importo_residuo']

    def fornitore_display(self, obj):
        return obj.fattura_acquisto.fornitore
    fornitore_display.short_description = 'Fornitore'
    fornitore_display.admin_order_field = 'fattura_acquisto__fornitore'

    def importo_residuo_display(self, obj):
        return f"€ {obj.importo_residuo()}"
    importo_residuo_display.short_description = 'Residuo'

    def stato_display(self, obj):
        if obj.is_scaduta():
            return format_html('<span style="color: red; font-weight: bold;">SCADUTA</span>')
        return obj.get_stato_display()
    stato_display.short_description = 'Stato'
