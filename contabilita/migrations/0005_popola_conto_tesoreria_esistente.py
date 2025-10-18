# /Users/angelolubrano/Documents/12.Python/deepseek-corso/contabilita/migrations/0003_popola_conto_tesoreria_esistente.py
# (Il nome del file potrebbe essere leggermente diverso, es. 0002, 0004, etc.)

from django.db import migrations

def popola_conto_tesoreria(apps, schema_editor):
    """
    Scorre tutti i movimenti contabili esistenti e, se sono legati a un conto
    di tesoreria (es. BANCHE), cerca il ContoBancario corrispondente e
    popola il nuovo campo 'conto_tesoreria'.
    """
    MovimentoContabile = apps.get_model('contabilita', 'MovimentoContabile')
    ContoBancario = apps.get_model('tesoreria', 'ContoBancario')
    Incasso = apps.get_model('tesoreria', 'Incasso')
    Spesa = apps.get_model('tesoreria', 'Spesa')

    # Itera su tutti i movimenti che non hanno ancora il campo popolato
    for mov in MovimentoContabile.objects.filter(conto_tesoreria__isnull=True):
        # Cerca l'incasso o la spesa che ha generato questa registrazione
        try:
            # Prova a trovare un incasso
            incasso = Incasso.objects.get(scadenza__fattura__numero=mov.registrazione.riferimento.replace('Incasso fattura ', ''))
            mov.conto_tesoreria = incasso.conto_bancario
            mov.save(update_fields=['conto_tesoreria'])
        except (Incasso.DoesNotExist, Incasso.MultipleObjectsReturned):
            try:
                # Prova a trovare una spesa
                spesa = Spesa.objects.get(scadenza__fattura_acquisto__numero=mov.registrazione.riferimento.replace('Pagamento fattura fornitore ', ''))
                mov.conto_tesoreria = spesa.conto_bancario
                mov.save(update_fields=['conto_tesoreria'])
            except (Spesa.DoesNotExist, Spesa.MultipleObjectsReturned):
                # Se non trova una corrispondenza, lascia il campo vuoto
                pass

class Migration(migrations.Migration):

    dependencies = [
        ('contabilita', '0004_movimentocontabile_conto_tesoreria'), # Assicurati che il nome di questa dipendenza sia corretto
        ('tesoreria', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(popola_conto_tesoreria),
    ]
