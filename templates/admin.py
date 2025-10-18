from django.contrib import admin
from .models import Fornitore

@admin.register(Fornitore)
class FornitoreAdmin(admin.ModelAdmin):
    list_display = ['ragione_sociale', 'partita_iva', 'citta', 'stato']
    list_filter = ['stato', 'citta']
    search_fields = ['ragione_sociale', 'partita_iva', 'codice_fiscale']
    readonly_fields = ['debito_residuo']
