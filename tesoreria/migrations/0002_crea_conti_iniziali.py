from django.db import migrations
from decimal import Decimal

def crea_conti_iniziali(apps, schema_editor):
    ContoBancario = apps.get_model('tesoreria', 'ContoBancario')
    
    conti_iniziali = [
        {
            'nome': 'Banca Intesa - Conto Corrente',
            'tipo_conto': 'bancario',
            'intestatario': 'Il Tuo Nome',
            'iban': 'IT60X0542811101000000123456',
            'nome_banca': 'Banca Intesa',
            'saldo_attuale': Decimal('15000.00'),
            'attivo': True
        },
        {
            'nome': 'Unicredit - Conto Aziendale', 
            'tipo_conto': 'bancario',
            'intestatario': 'Il Tuo Nome',
            'iban': 'IT02R0200811773000012345678',
            'nome_banca': 'Unicredit',
            'saldo_attuale': Decimal('8000.00'),
            'attivo': True
        },
        {
            'nome': 'BNL - Conto Risparmio',
            'tipo_conto': 'bancario', 
            'intestatario': 'Il Tuo Nome',
            'iban': 'IT05S0103001600000012345679',
            'nome_banca': 'BNL',
            'saldo_attuale': Decimal('25000.00'),
            'attivo': True
        },
        {
            'nome': 'Cassa Office',
            'tipo_conto': 'cassa',
            'intestatario': 'Azienda',
            'iban': '',
            'nome_banca': '',
            'saldo_attuale': Decimal('500.00'),
            'attivo': True
        }
    ]
    
    for conto_data in conti_iniziali:
        ContoBancario.objects.create(**conto_data)

def elimina_conti_iniziali(apps, schema_editor):
    ContoBancario = apps.get_model('tesoreria', 'ContoBancario')
    ContoBancario.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('tesoreria', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(crea_conti_iniziali, elimina_conti_iniziali),
    ]