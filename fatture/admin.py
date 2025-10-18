from django.contrib import admin
from .models import Fattura, ScadenzaFattura

class ScadenzaFatturaInline(admin.TabularInline):
    model = ScadenzaFattura
    extra = 1

@admin.register(Fattura)
class FatturaAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'cliente',  # 👈 AGGIUNTO CLIENTE
        'data_emissione', 
        'importo_totale', 
        'totale_complessivo',
        'stato',
    ]
    
    list_filter = ['stato', 'data_emissione', 'cliente']  # 👈 AGGIUNTO CLIENTE
    search_fields = ['numero', 'descrizione', 'cliente__ragione_sociale']  # 👈 AGGIUNTO RICERCA CLIENTE
    
    inlines = [ScadenzaFatturaInline]
    readonly_fields = ['totale_complessivo', 'totale_scadenze']

@admin.register(ScadenzaFattura)
class ScadenzaFatturaAdmin(admin.ModelAdmin):
    list_display = [
        'fattura',
        'data_scadenza', 
        'importo',
        'stato',
        'data_pagamento',
        'is_scaduta'
    ]
    
    list_filter = ['stato', 'data_scadenza']
    search_fields = ['fattura__numero', 'fattura__cliente__ragione_sociale']  # 👈 RICERCA PER CLIENTE