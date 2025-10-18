from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render
from django.db.models import Q
from django.http import HttpResponseRedirect
from .models import PianoDeiConti, RegistrazioneContabile, MovimentoContabile

@admin.register(PianoDeiConti)
class PianoDeiContiAdmin(admin.ModelAdmin):
    list_display = ['codice', 'descrizione', 'classe', 'natura', 'attivo', 'livello_display']
    list_filter = ['classe', 'natura', 'attivo']
    search_fields = ['codice', 'descrizione']
    
    # Paginazione
    list_per_page = 25
    show_full_result_count = True
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('sottoconto_di')
    
    def livello_display(self, obj):
        return obj.livello()
    livello_display.short_description = "Livello"
    
    # Azioni rapide
    actions = ['disattiva_conti', 'attiva_conti']
    
    def disattiva_conti(self, request, queryset):
        queryset.update(attivo=False)
        self.message_user(request, f"{queryset.count()} conti disattivati")
    disattiva_conti.short_description = "Disattiva conti selezionati"
    
    def attiva_conti(self, request, queryset):
        queryset.update(attivo=True)
        self.message_user(request, f"{queryset.count()} conti attivati")
    attiva_conti.short_description = "Attiva conti selezionati"
    
    # 👇 VISTE PERSONALIZZATE - CODICE CORRETTO
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('albero-conti/', self.admin_site.admin_view(self.vista_albero), name='albero_conti'),
            path('conti-patrimoniali/', self.admin_site.admin_view(self.vista_patrimoniali), name='conti_patrimoniali'),
            path('conti-economici/', self.admin_site.admin_view(self.vista_economici), name='conti_economici'),
        ]
        return custom_urls + urls
    
    def vista_albero(self, request):
        """Vista albero gerarchico"""
        conti_radice = PianoDeiConti.objects.filter(sottoconto_di__isnull=True).order_by('codice')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Albero del Piano dei Conti',
            'conti_radice': conti_radice,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/contabilita/albero_conti.html', context)
    
    def vista_patrimoniali(self, request):
        """Vista conti patrimoniali"""
        queryset = PianoDeiConti.objects.filter(classe='patrimoniale').order_by('codice')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Conti Patrimoniali',
            'queryset': queryset,
            'classe_filtro': 'patrimoniale',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/contabilita/conti_filtrati.html', context)
    
    def vista_economici(self, request):
        """Vista conti economici"""
        queryset = PianoDeiConti.objects.filter(classe='economico').order_by('codice')
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Conti Economici',
            'queryset': queryset,
            'classe_filtro': 'economico',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/contabilita/conti_filtrati.html', context)
    
    # 👇 METODO PER AGGIUNGERE I LINK NELLA PAGINA PRINCIPALE
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Aggiungi i link alle viste personalizzate
        extra_context['custom_links'] = [
            {
                'url': reverse('admin:albero_conti'),
                'label': '🌳 Vista Albero',
                'description': 'Visualizza la gerarchia completa dei conti'
            },
            {
                'url': reverse('admin:conti_patrimoniali'),
                'label': '💼 Conti Patrimoniali', 
                'description': 'Solo conti patrimoniali (Attivo/Passivo)'
            },
            {
                'url': reverse('admin:conti_economici'),
                'label': '📈 Conti Economici',
                'description': 'Solo conti economici (Costi/Ricavi)'
            },
        ]
        
        return super().changelist_view(request, extra_context=extra_context)