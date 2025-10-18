# Gestionale Contabile

Questo è un software gestionale sviluppato in Django per la gestione della contabilità, fatturazione e tesoreria.

## Installazione e Avvio

Queste istruzioni ti guideranno nella configurazione del progetto sul tuo computer locale per lo sviluppo e il testing.

### Prerequisiti

Assicurati di avere installato Python (versione 3.10 o superiore) sul tuo sistema.

### Passaggi di Configurazione

1.  **Clona il Repository**
    ```bash
    git clone <URL_DEL_TUO_REPOSITORY>
    cd gestionale-contabile # o il nome della cartella del progetto
    ```

2.  **Crea e Attiva un Ambiente Virtuale**
    È una best practice usare un ambiente virtuale per isolare le dipendenze del progetto.
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3.  **Installa le Dipendenze**
    Il file `requirements.txt` contiene tutte le librerie Python necessarie.
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: se non hai un file `requirements.txt`, puoi crearlo con `pip freeze > requirements.txt`)*

4.  **Applica le Migrazioni del Database**
    Questo comando crea la struttura del database (le tabelle) e popola i dati iniziali (come i conti di tesoreria).
    ```bash
    python manage.py migrate
    ```

5.  **Crea un Superutente**
    Per accedere all'area di amministrazione di Django, devi creare un utente amministratore.
    ```bash
    python manage.py createsuperuser
    ```
    Segui le istruzioni per inserire username, email e password.

6.  **Avvia il Server di Sviluppo**
    ```bash
    python manage.py runserver
    ```

7.  **Accedi all'Applicazione**
    Apri il tuo browser e vai ai seguenti indirizzi:
    *   **Dashboard Principale**: `http://127.0.0.1:8000/`
    *   **Area di Amministrazione**: `http://127.0.0.1:8000/admin/` (accedi con le credenziali del superutente appena creato).

## Logica delle Migrazioni Dati

All'interno del progetto, alcune migrazioni sono state create non per modificare la struttura del database, ma per popolarlo con dati iniziali essenziali.

### Creazione Conti Iniziali (`tesoreria/migrations/0002_crea_conti_iniziali.py`)

Questa migrazione ha lo scopo di **popolare il database con un set di conti di tesoreria predefiniti** al primo avvio dell'applicazione.

#### Scopo del Processo

1.  **Inizializzazione (Seeding)**: Al momento dell'installazione, il sistema crea automaticamente alcuni conti (es: "Banca Intesa", "Cassa Office") per evitare all'utente di doverli inserire manualmente. Questa operazione viene eseguita una sola volta.

2.  **Logica del `saldo_attuale`**: Il valore assegnato al campo `saldo_attuale` in questa migrazione non è il risultato di un calcolo. Rappresenta il **saldo di apertura** o **saldo iniziale** del conto. È un valore statico che definisce la liquidità disponibile su quel conto nel momento in cui il gestionale viene configurato per la prima volta.

3.  **Aggiornamento Dinamico**: Una volta che i conti iniziali sono stati creati, il loro `saldo_attuale` diventa un valore **dinamico**. Viene automaticamente aumentato o diminuito ogni volta che viene registrato un `Incasso` o una `Spesa`. Questa logica di aggiornamento automatico è gestita dai segnali Django definiti nel file `tesoreria/signals.py`, che intercettano la creazione o la cancellazione di un movimento e chiamano il metodo `aggiorna_saldo` sul `ContoBancario` corrispondente.

In sintesi, la migrazione `0002_crea_conti_iniziali.py` imposta il punto di partenza per la tesoreria, dopodiché la gestione dei saldi diventa completamente automatica e basata sui movimenti registrati.
