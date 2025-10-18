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

    _(Nota: se non hai un file `requirements.txt`, puoi crearlo con `pip freeze > requirements.txt`)_

4.  **Applica le Migrazioni del Database**
    Questo comando è cruciale. Esegue le seguenti operazioni:


    python manage.py makemigrations 
    python manage.py migrate
    copia il file 0002_popola_piano_dei_conti.py da _cartella_di_servizio a contabilita/migrations/
    python manage.py makemigrations --empty contabilita --name popola_piano_dei_conti

    - Crea l'intera struttura del database (tabelle e relazioni).
    - **Popola automaticamente il Piano dei Conti** con una struttura standard.
    - **Crea i conti di tesoreria predefiniti** (es. "Banca Intesa", "Cassa Office"), ma con saldo a zero.



5.  **Crea un Superutente**
    Per accedere all'area di amministrazione di Django, devi creare un utente amministratore.

    ```bash
    python manage.py createsuperuser
    ```

    Segui le istruzioni per inserire username, email e password.

6.  **Configurazione Iniziale (Azione Manuale)**

    - Accedi all'area di amministrazione (`/admin/`).
    - Vai alla sezione "Conti Bancari".
    - Modifica i conti pre-creati ("Banca Intesa", "Cassa Office", ecc.) e, nel campo **"Conto Contabile Associato"**, collega ciascuno al rispettivo conto del `PianoDeiConti` (es: `1.1.02 - BANCHE E POSTE` o `1.1.01 - CASSA`).
    - **Inserimento Saldi di Apertura**: Per inserire i saldi iniziali dei conti, dei crediti clienti o dei debiti fornitori, sarà necessario creare delle registrazioni in partita doppia tramite una futura vista di "Prima Nota". Ad esempio, per un saldo bancario di 10.000€, la scrittura sarà: `DARE: 1.1.02 - BANCHE E POSTE` e `AVERE: 2.2.04 - BILANCIO DI APERTURA`.

7.  **Avvia il Server di Sviluppo**

    ```bash
    python manage.py runserver
    ```

8.  **Accedi all'Applicazione**
    Apri il tuo browser e vai ai seguenti indirizzi:
    - **Dashboard Principale**: `http://127.0.0.1:8000/`
    - **Area di Amministrazione**: `http://127.0.0.1:8000/admin/` (accedi con le credenziali del superutente appena creato).

## Architettura Contabile e Logica dei Saldi

Il progetto è stato oggetto di un importante refactoring per passare da un sistema di tracciamento saldi "extra-contabile" a un sistema basato sui principi della **partita doppia**.

### Calcolo Dinamico dei Saldi

Il campo `saldo_attuale` è stato rimosso dal modello `ContoBancario`. Ora, il saldo di qualsiasi conto di tesoreria non è più un valore memorizzato, ma una **proprietà calcolata dinamicamente**.

Il sistema interroga in tempo reale tutti i `MovimentoContabile` associati al conto contabile collegato (es. `1.1.02 - BANCHE E POSTE`) e ne calcola il saldo come `Totale DARE - Totale AVERE`.

### Contabilizzazione Automatica

Ogni operazione di tesoreria (`Incasso` o `Spesa`) genera automaticamente una `RegistrazioneContabile` in partita doppia. Ad esempio, un incasso da un cliente genera la seguente scrittura:

- **DARE**: Cassa/Banca (aumenta la liquidità)
- **AVERE**: Crediti v/Clienti (diminuisce il credito)

Questo approccio garantisce che ogni operazione sia tracciata, che il bilancio sia sempre quadrato e che i saldi siano sempre corretti e verificabili.
