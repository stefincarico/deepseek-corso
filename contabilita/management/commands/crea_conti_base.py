from django.core.management.base import BaseCommand
from contabilita.models import PianoDeiConti
from decimal import Decimal

class Command(BaseCommand):
    help = 'Popola il database con un piano dei conti completo per il gestionale'
    
    def handle(self, *args, **options):
        """
        Script per creare un piano dei conti completo per una piccola/media impresa
        """
        self.stdout.write('🎯 Inizio creazione piano dei conti...')
        
        # Dizionario per tenere traccia dei conti creati
        conti_creati = {}
        
        # DEFINIZIONE COMPLETA DEL PIANO DEI CONTI
        conti_da_creare = [
            # ==================== CONTI PATRIMONIALI ====================
            
            # ATTIVO (DARE)
            {'codice': '1', 'descrizione': 'ATTIVO', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': None},
            
            # ATTIVO CIRCOLANTE
            {'codice': '1.1', 'descrizione': 'ATTIVO CIRCOLANTE', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1'},
            {'codice': '1.1.01', 'descrizione': 'CASSA', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.1'},
            {'codice': '1.1.02', 'descrizione': 'BANCHE E POSTE', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.1'},
            {'codice': '1.1.03', 'descrizione': 'CREDITI VERSO CLIENTI', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.1'},
            {'codice': '1.1.04', 'descrizione': 'RIMANENZE DI MAGAZZINO', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.1'},
            {'codice': '1.1.05', 'descrizione': 'RATEI ATTIVI', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.1'},
            
            # ATTIVO IMMOBILIZZATO
            {'codice': '1.2', 'descrizione': 'ATTIVO IMMOBILIZZATO', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1'},
            {'codice': '1.2.01', 'descrizione': 'IMMOBILI', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            {'codice': '1.2.02', 'descrizione': 'AUTOMEZZI', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            {'codice': '1.2.03', 'descrizione': 'ATTREZZATURE', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            {'codice': '1.2.04', 'descrizione': 'ARREDAMENTO', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            {'codice': '1.2.05', 'descrizione': 'IMPIANTI', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            {'codice': '1.2.06', 'descrizione': 'FONDO AMMORTAMENTO', 'classe': 'patrimoniale', 'natura': 'dare', 'sottoconto_di': '1.2'},
            
            # PASSIVO (AVERE)
            {'codice': '2', 'descrizione': 'PASSIVO', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': None},
            
            # PASSIVO CORRENTE
            {'codice': '2.1', 'descrizione': 'PASSIVO CORRENTE', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2'},
            {'codice': '2.1.01', 'descrizione': 'DEBITI VERSO FORNITORI', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.1'},
            {'codice': '2.1.02', 'descrizione': 'DEBITI TRIBUTARI', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.1'},
            {'codice': '2.1.03', 'descrizione': 'DEBITI VERSO BANCHE', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.1'},
            {'codice': '2.1.04', 'descrizione': 'RATEI PASSIVI', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.1'},
            
            # PATRIMONIO NETTO
            {'codice': '2.2', 'descrizione': 'PATRIMONIO NETTO', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2'},
            {'codice': '2.2.01', 'descrizione': 'CAPITALE SOCIALE', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.2'},
            {'codice': '2.2.02', 'descrizione': 'UTILE PERDITA ESERCIZIO', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.2'},
            {'codice': '2.2.03', 'descrizione': 'RISERVE', 'classe': 'patrimoniale', 'natura': 'avere', 'sottoconto_di': '2.2'},
            
            # ==================== CONTI ECONOMICI ====================
            
            # COSTI (DARE)
            {'codice': '3', 'descrizione': 'COSTI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': None},
            
            # ACQUISTI
            {'codice': '3.1', 'descrizione': 'ACQUISTI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3'},
            {'codice': '3.1.01', 'descrizione': 'ACQUISTI MERCI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.1'},
            {'codice': '3.1.02', 'descrizione': 'ACQUISTI MATERIE PRIME', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.1'},
            {'codice': '3.1.03', 'descrizione': 'ACQUISTI MATERIALE CONSUMO', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.1'},
            
            # SERVIZI
            {'codice': '3.2', 'descrizione': 'SERVIZI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3'},
            {'codice': '3.2.01', 'descrizione': 'SERVIZI ENERGETICI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.02', 'descrizione': 'AFFITTI E LOCAZIONI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.03', 'descrizione': 'MANUTENZIONI E RIPARAZIONI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.04', 'descrizione': 'SERVIZI TELEFONICI E INTERNET', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.05', 'descrizione': 'SERVIZI PROFESSIONALI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.06', 'descrizione': 'PUBBLICITÀ E MARKETING', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.07', 'descrizione': 'SPESE POSTALI E BANCARIE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.08', 'descrizione': 'ASSICURAZIONI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            {'codice': '3.2.09', 'descrizione': 'SPESE VARIE E IMPREVISTI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.2'},
            
            # PERSONALE
            {'codice': '3.3', 'descrizione': 'PERSONALE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3'},
            {'codice': '3.3.01', 'descrizione': 'STIPENDI E SALARI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.3'},
            {'codice': '3.3.02', 'descrizione': 'CONTRIBUTI PREVIDENZIALI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.3'},
            {'codice': '3.3.03', 'descrizione': 'TRATTAMENTO DI FINE RAPPORTO', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.3'},
            {'codice': '3.3.04', 'descrizione': 'PREMI E INCENTIVI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.3'},
            
            # TRIBUTI
            {'codice': '3.4', 'descrizione': 'TRIBUTI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3'},
            {'codice': '3.4.01', 'descrizione': 'IMPOSTE DIRETTE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.4'},
            {'codice': '3.4.02', 'descrizione': 'IMPOSTE INDIRETTE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.4'},
            {'codice': '3.4.03', 'descrizione': 'ADDIZIONALI E ACCISE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.4'},
            
            # AMMORTAMENTI
            {'codice': '3.5', 'descrizione': 'AMMORTAMENTI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3'},
            {'codice': '3.5.01', 'descrizione': 'AMMORTAMENTO IMMOBILI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.5'},
            {'codice': '3.5.02', 'descrizione': 'AMMORTAMENTO AUTOMEZZI', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.5'},
            {'codice': '3.5.03', 'descrizione': 'AMMORTAMENTO ATTREZZATURE', 'classe': 'economico', 'natura': 'dare', 'sottoconto_di': '3.5'},
            
            # RICAVI (AVERE)
            {'codice': '4', 'descrizione': 'RICAVI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': None},
            
            # RICAVI VENDITE
            {'codice': '4.1', 'descrizione': 'RICAVI VENDITE', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4'},
            {'codice': '4.1.01', 'descrizione': 'RICAVI VENDITE PRODOTTI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4.1'},
            {'codice': '4.1.02', 'descrizione': 'RICAVI VENDITE SERVIZI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4.1'},
            {'codice': '4.1.03', 'descrizione': 'RICAVI ACCESSORI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4.1'},
            
            # RICAVI FINANZIARI
            {'codice': '4.2', 'descrizione': 'RICAVI FINANZIARI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4'},
            {'codice': '4.2.01', 'descrizione': 'INTERESSI ATTIVI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4.2'},
            {'codice': '4.2.02', 'descrizione': 'PROVENTI DIVERSI', 'classe': 'economico', 'natura': 'avere', 'sottoconto_di': '4.2'},
            
            # ==================== CONTI D'ORDINE ====================
            {'codice': '5', 'descrizione': 'CONT D\'ORDINE', 'classe': 'ordine', 'natura': 'dare', 'sottoconto_di': None},
            {'codice': '5.1', 'descrizione': 'GARANZIE RICEVUTE', 'classe': 'ordine', 'natura': 'dare', 'sottoconto_di': '5'},
            {'codice': '5.2', 'descrizione': 'GARANZIE CONCESSE', 'classe': 'ordine', 'natura': 'dare', 'sottoconto_di': '5'},
        ]
        
        # FASE 1: Crea tutti i conti senza riferimenti
        self.stdout.write('📋 Creazione conti base...')
        for conto_data in conti_da_creare:
            codice = conto_data['codice']
            descrizione = conto_data['descrizione']
            classe = conto_data['classe']
            natura = conto_data['natura']
            
            # Crea il conto senza riferimento al padre
            conto, created = PianoDeiConti.objects.get_or_create(
                codice=codice,
                defaults={
                    'descrizione': descrizione,
                    'classe': classe,
                    'natura': natura,
                    'sottoconto_di': None,  # Temporaneamente null
                }
            )
            
            if created:
                self.stdout.write(f'   ✅ Creato: {codice} - {descrizione}')
            else:
                self.stdout.write(f'   ⚠️  Già esistente: {codice} - {descrizione}')
            
            conti_creati[codice] = conto
        
        # FASE 2: Aggiorna i riferimenti gerarchici
        self.stdout.write('🔗 Collegamento gerarchia conti...')
        for conto_data in conti_da_creare:
            codice = conto_data['codice']
            padre_codice = conto_data['sottoconto_di']
            
            if padre_codice:  # Se ha un padre
                conto = conti_creati[codice]
                padre = conti_creati[padre_codice]
                
                # Aggiorna il riferimento
                if conto.sottoconto_di != padre:
                    conto.sottoconto_di = padre
                    conto.save()
                    self.stdout.write(f'   🔗 Collegato: {codice} → {padre_codice}')
        
        # STATISTICHE FINALI
        totale_conti = PianoDeiConti.objects.count()
        conti_patrimoniali = PianoDeiConti.objects.filter(classe='patrimoniale').count()
        conti_economici = PianoDeiConti.objects.filter(classe='economico').count()
        conti_ordine = PianoDeiConti.objects.filter(classe='ordine').count()
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 PIANO DEI CONTI COMPLETATO!'))
        self.stdout.write(f'   📊 Totale conti creati: {totale_conti}')
        self.stdout.write(f'   💼 Conti patrimoniali: {conti_patrimoniali}')
        self.stdout.write(f'   📈 Conti economici: {conti_economici}')
        self.stdout.write(f'   📋 Conti d\'ordine: {conti_ordine}')
        self.stdout.write('')
        self.stdout.write('🚀 Ora puoi iniziare a registrare le prime operazioni in prima nota!')