from django.contrib import admin
from .models import FatturaAcquisto, ScadenzaFatturaAcquisto

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