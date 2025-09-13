# -*- coding: utf-8 -*-
"""
Questo modulo definisce la classe `ViticultureSimulator`, responsabile della generazione
di dati ambientali, produttivi ed economici simulati per un vigneto.

La simulazione si basa su modelli stocastici e stagionali per creare serie storiche
realistiche di temperatura, precipitazioni, irradiazione solare e altre metriche
rilevanti per la viticoltura.
"""
import numpy as np
import pandas as pd

class ViticultureSimulator:
    """
    Simulatore per la generazione di dati vitivinicoli.
    
    Questa classe incapsula tutta la logica per creare un set di dati giornaliero
    che include variabili climatiche e metriche annuali di produzione ed economiche.
    """
    def __init__(self, start_date, end_date, total_hectares=600):
        """
        Inizializza il simulatore con i parametri di base.

        Args:
            start_date (str): Data di inizio della simulazione (formato 'YYYY-MM-DD').
            end_date (str): Data di fine della simulazione (formato 'YYYY-MM-DD').
            total_hectares (int): Numero totale di ettari del vigneto da simulare.
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        # Crea un range di date giornaliere che servirà da indice per i nostri dati.
        self.date_range = pd.date_range(self.start_date, self.end_date, freq='D')
        # Inizializza il DataFrame principale che conterrà tutti i dati.
        self.data = pd.DataFrame(index=self.date_range)
        self.total_hectares = total_hectares
        # Estrae gli anni unici dalla serie di date per iterare su di essi.
        self.years = self.data.index.year.unique()

    def generate_ambient_data(self):
        """
        Genera i dati climatici giornalieri (temperatura, pioggia, umidità, etc.).
        
        I dati vengono generati utilizzando modelli sinusoidali per la stagionalità
        e rumore casuale per simulare la variabilità giornaliera.
        """
        print("Generazione dei dati ambientali...")
        num_days = len(self.date_range)
        avg_annual_temp = 12.0  # Temperatura media annuale di base.
        
        # Converte l'indice dei giorni dell'anno in un array NumPy per calcoli efficienti.
        day_of_year = self.data.index.dayofyear.values
        
        # Simula l'effetto stagionale sulla temperatura usando una funzione seno.
        # Il picco è spostato per simulare l'estate.
        seasonal_temp_effect = 10 * np.sin(2 * np.pi * (day_of_year - 110) / 365) + 3
        
        # Per evitare picchi di temperatura irrealistici, generiamo un "rumore" casuale
        # e poi lo smussiamo con una media mobile su 7 giorni. Questo rende le variazioni più graduali.
        random_noise = np.random.normal(loc=0, scale=3, size=num_days)
        smoothed_noise = pd.Series(random_noise).rolling(window=7, center=True, min_periods=1).mean().values
        
        # La temperatura finale è la somma della media, dell'effetto stagionale e del rumore smussato.
        self.data['Temperature_C'] = avg_annual_temp + seasonal_temp_effect + smoothed_noise
        
        # Simula le precipitazioni con una probabilità stagionale (più piogge in primavera/estate).
        rain_prob_seasonal = 0.25 + 0.2 * np.sin(2 * np.pi * (day_of_year - 60) / 365)
        is_raining = np.random.rand(num_days) < rain_prob_seasonal
        # Se piove, la quantità di pioggia segue una distribuzione esponenziale. Altrimenti è 0.
        self.data['Precipitation_mm'] = np.where(is_raining, np.random.exponential(scale=7.0, size=num_days), 0)
        
        # Genera l'umidità da una distribuzione normale e la "clippa" tra 0 e 100.
        self.data['Humidity_percent'] = np.random.normal(loc=75, scale=12, size=num_days).clip(0, 100)
        
        # Simula l'irradiazione solare con una forte componente stagionale.
        seasonal_irradiance_effect = 150 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        self.data['Solar_Irradiance_W_m2'] = (180 + seasonal_irradiance_effect + np.random.normal(0, 40, num_days)).clip(20)

        # Aggiunge piccole interdipendenze fisiche tra le variabili:
        # - L'irradiazione solare aumenta leggermente la temperatura.
        # - L'aumento di temperatura riduce l'umidità relativa.
        self.data['Temperature_C'] += self.data['Solar_Irradiance_W_m2'] * 0.005
        self.data['Humidity_percent'] -= self.data['Temperature_C'] * 0.5
        self.data['Humidity_percent'] = self.data['Humidity_percent'].clip(0, 100)
        
        # Aggiunge una colonna con il numero di ettari, costante per ogni riga.
        self.data['Hectares_Simulated'] = self.total_hectares
        
        print("Generazione dei dati ambientali completata.")

    def calculate_annual_metrics(self):
        """
        Calcola le metriche di produzione ed economiche su base annuale.

        Questo metodo itera su ogni anno della simulazione, calcola le metriche
        aggregate (resa, qualità, costi, ricavi) e le assegna a tutti i giorni
        di quell'anno.
        """
        print("Calcolo dei dati di produzione ed economici annuali...")

        # Inizializza le colonne che conterranno i dati annuali.
        self.data['Yield_kg_ha'] = np.nan
        self.data['Grape_Sugar_Level'] = np.nan
        self.data['Production_Cost_EUR_ha'] = np.nan
        self.data['Selling_Price_EUR_kg'] = np.nan
        self.data['Revenue_EUR_ha'] = np.nan

        # Itera su ogni anno presente nel set di dati.
        for year in self.years:
            # Filtra i dati per l'anno corrente.
            yearly_data = self.data[self.data.index.year == year]

            # --- CALCOLO DELLA RESA ANNUALE PER ETTARO (Yield_kg_ha) ---
            # La resa finale dipende da una base casuale e da vari fattori climatici.
            base_yield = np.random.normal(loc=12000, scale=800)
            
            # Effetto dell'irradiazione solare: più sole, più resa.
            mean_solar_irradiance = yearly_data['Solar_Irradiance_W_m2'].mean()
            solar_effect_annual = (mean_solar_irradiance - 200) * 15 
            
            total_days = len(yearly_data)
            
            # Penalità per temperature estreme (troppo caldo o troppo freddo).
            extreme_temp_days_ratio = ((yearly_data['Temperature_C'] > 35) | (yearly_data['Temperature_C'] < 5)).sum() / total_days
            extreme_temp_penalty = extreme_temp_days_ratio * 4000
            
            # Penalità per rischio malattie (caldo, umido e piovoso).
            disease_risk_days_ratio = ((yearly_data['Temperature_C'] > 25) & (yearly_data['Humidity_percent'] > 80) & (yearly_data['Precipitation_mm'] > 0)).sum() / total_days
            disease_risk_penalty = disease_risk_days_ratio * 3500

            # Penalità per piogge torrenziali.
            extreme_precip_days_ratio = (yearly_data['Precipitation_mm'] > 20).sum() / total_days
            extreme_precip_penalty = extreme_precip_days_ratio * 3000
            
            # Calcolo della resa finale, con un cap minimo e massimo.
            final_yield = base_yield + solar_effect_annual - extreme_temp_penalty - disease_risk_penalty - extreme_precip_penalty
            final_yield = max(min(final_yield, 15000), 8000)

            # --- CALCOLO LIVELLO DI ZUCCHERO (Qualità) ---
            # Il livello di zucchero dipende principalmente da temperatura e sole.
            mean_temperature_c = yearly_data['Temperature_C'].mean()
            mean_solar_irradiance_w = yearly_data['Solar_Irradiance_W_m2'].mean()
            
            base_sugar = np.random.normal(loc=17, scale=0.5)
            final_sugar_level = base_sugar + (mean_solar_irradiance_w / 200) + (mean_temperature_c / 20)
            final_sugar_level = max(min(final_sugar_level, 19.5), 15)

            # --- CALCOLO DEI COSTI E RICAVI PER ETTARO ---
            base_cost_per_ha = np.random.normal(loc=10000, scale=1000)
            final_production_cost_per_ha = max(base_cost_per_ha, 8000)
            
            # Il prezzo di vendita è influenzato dalla qualità (livello di zucchero).
            base_price = np.random.normal(loc=4.0, scale=0.8)
            quality_effect = (final_sugar_level - 17.5) * 0.5
            final_selling_price_per_kg = max(min(base_price + quality_effect, 6.0), 3.5)
            
            # Il ricavo è dato dalla resa moltiplicata per il prezzo, meno i costi.
            revenue_per_ha = (final_yield * final_selling_price_per_kg) - final_production_cost_per_ha
            
            # Assegna i valori annuali calcolati a tutte le righe dell'anno corrente.
            self.data.loc[self.data.index.year == year, 'Yield_kg_ha'] = final_yield
            self.data.loc[self.data.index.year == year, 'Grape_Sugar_Level'] = final_sugar_level
            self.data.loc[self.data.index.year == year, 'Production_Cost_EUR_ha'] = final_production_cost_per_ha
            self.data.loc[self.data.index.year == year, 'Selling_Price_EUR_kg'] = final_selling_price_per_kg
            self.data.loc[self.data.index.year == year, 'Revenue_EUR_ha'] = revenue_per_ha
        
        print("Calcolo dei dati di produzione ed economici completato.")

    def run_simulation(self):
        """
        Esegue l'intera pipeline di simulazione.
        
        Returns:
            pd.DataFrame: Il DataFrame completo con tutti i dati simulati.
        """
        self.generate_ambient_data()
        self.calculate_annual_metrics()
        
        return self.data