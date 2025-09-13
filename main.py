# -*- coding: utf-8 -*-
"""
Questo script è il punto di ingresso principale per l'esecuzione del simulatore di dati vitivinicoli.

Funzionamento:
1. Importa la classe `ViticultureSimulator`.
2. Imposta i parametri di configurazione della simulazione (date, ettari).
3. Crea un'istanza del simulatore.
4. Esegue la simulazione per generare i dati.
5. Salva i dati generati in un file CSV (`simulated_vineyard_data.csv`), che verrà poi
   utilizzato dal dashboard per la visualizzazione.
"""
from simulatore_dati import ViticultureSimulator

def main():
    """
    Funzione principale che orchestra l'esecuzione della simulazione.
    
    Definisce i parametri, avvia il simulatore e salva i risultati.
    """
    # --- PARAMETRI DI CONFIGURAZIONE DELLA SIMULAZIONE ---
    # Definisce l'intervallo temporale per cui generare i dati.
    start_date = '2015-08-01'
    end_date = '2025-09-30'
    
    # Definisce il numero totale di ettari del vigneto da simulare.
    hectares_to_simulate = 600
    
    print(f"Avvio della simulazione per {hectares_to_simulate} ettari dal {start_date} al {end_date}...")
    
    # --- ESECUZIONE DELLA SIMULAZIONE ---
    # 1. Crea un'istanza della classe del simulatore, passando i parametri di configurazione.
    simulator = ViticultureSimulator(start_date=start_date, end_date=end_date, total_hectares=hectares_to_simulate)
    
    # 2. Esegue il metodo principale che genera tutti i dati (climatici, produttivi, economici).
    simulation_data = simulator.run_simulation()
    
    # --- OUTPUT E SALVATAGGIO ---
    # Stampa le prime righe del DataFrame per un controllo rapido.
    print("\nAnteprima dei dati simulati (head):")
    print(simulation_data.head())
    
    # Stampa statistiche descrittive per verificare la coerenza dei dati generati.
    print("\nStatistiche descrittive dei dati (describe):")
    print(simulation_data.describe())
    
    # Salva il DataFrame completo in un file CSV.
    # Questo file sarà la fonte dati per il dashboard.
    file_name = 'simulated_vineyard_data.csv'
    simulation_data.to_csv(file_name)
    print(f"\nDati salvati correttamente nel file: {file_name}")

# Questo costrutto standard in Python assicura che la funzione `main()`
# venga eseguita solo quando lo script viene lanciato direttamente
# (e non quando viene importato come modulo in un altro script).
if __name__ == "__main__":
    main()