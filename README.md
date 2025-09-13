# Simulatore Vitivinicolo e Dashboard di Analisi

Questo progetto simula dati ambientali, produttivi ed economici per un vigneto e li visualizza attraverso una dashboard interattiva.

## Struttura del Progetto

-   `main.py`: Punto di ingresso per avviare la simulazione.
-   `simulatore_dati.py`: Contiene la logica di simulazione per la generazione dei dati.
-   `dashboard.py`: Contiene il codice per la dashboard web interattiva.
-   `simulated_vineyard_data.csv`: File di output generato dal simulatore e utilizzato dalla dashboard (non versionato).
-   `requirements.txt`: Elenco delle dipendenze Python.

## Prerequisiti

-   Python 3.8 o superiore

## Installazione

1.  Clona il repository o scarica i file in una cartella locale.
2.  Crea e attiva un ambiente virtuale (consigliato):
    ```bash
    python -m venv venv
    # Su Windows
    .\venv\Scripts\activate
    # Su macOS/Linux
    source venv/bin/activate
    ```
3.  Installa tutte le dipendenze necessarie:
    ```bash
    pip install -r requirements.txt
    ```

## Utilizzo

Per utilizzare l'applicazione, segui questi due passaggi:

1.  **Esegui il simulatore** per generare il file di dati:
    ```bash
    python main.py
    ```
    Questo creerà il file `simulated_vineyard_data.csv` nella stessa cartella.

2.  **Avvia la dashboard** per visualizzare i dati:
    ```bash
    python dashboard.py
    ```
    Apri il browser e vai all'indirizzo `http://127.0.0.1:8050/` per vedere la dashboard.
