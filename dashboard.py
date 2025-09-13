# -*- coding: utf-8 -*-
"""
Questo script crea un dashboard interattivo utilizzando Dash e Plotly per visualizzare
i dati simulati di un vigneto. Il dashboard mostra metriche climatiche, di produzione
ed economiche, sia a livello di panoramica globale per annata, sia con un dettaglio
giornaliero per una singola annata selezionabile.
"""
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import datetime
import sys

# --- 1. CARICAMENTO E PREPARAZIONE DEI DATI ---

# Tenta di caricare i dati dal file CSV generato dal simulatore.
try:
    file_path = 'simulated_vineyard_data.csv'
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    # Recupera la data dell'ultima modifica del file per mostrarla nel dashboard.
    file_modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
except FileNotFoundError:
    # Se il file non viene trovato, stampa un messaggio di errore e termina l'esecuzione.
    print("Errore: Il file 'simulated_vineyard_data.csv' non è stato trovato.")
    print("Assicurati di aver eseguito lo script del simulatore per generare il file.")
    sys.exit(1)
except Exception as e:
    print(f"Errore imprevisto durante il caricamento del file '{file_path}': {e}")
    sys.exit(1)

# --- CONTROLLI FORMALI SUI DATI CARICATI ---

# 1. Controlla se il DataFrame è vuoto
if df.empty:
    print(f"Errore: Il file '{file_path}' è vuoto.")
    sys.exit(1)

# 2. Controlla la presenza delle colonne necessarie per il funzionamento del dashboard
required_columns = [
    'Temperature_C', 'Precipitation_mm', 'Humidity_percent', 
    'Solar_Irradiance_W_m2', 'Hectares_Simulated', 'Yield_kg_ha', 
    'Grape_Sugar_Level', 'Production_Cost_EUR_ha', 'Selling_Price_EUR_kg', 
    'Revenue_EUR_ha'
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    print(f"Errore: Le seguenti colonne obbligatorie mancano nel file '{file_path}': {', '.join(missing_columns)}")
    print("Rigenerare il file CSV eseguendo lo script del simulatore.")
    sys.exit(1)

print("Controlli formali sul file CSV superati. Dati caricati correttamente.")


# Estrae la lista degli anni unici presenti nei dati per popolare il dropdown.
available_years = sorted(df.index.year.unique())

# Recupera il numero di ettari simulati (prende il valore dalla prima riga).
# Se la colonna non esiste, usa un valore di default (600).
hectares_simulated = df['Hectares_Simulated'].iloc[0] if 'Hectares_Simulated' in df.columns else 600

# Aggrega i dati giornalieri in metriche annuali per la visualizzazione globale.
# 'groupby(df.index.year)' raggruppa i dati per anno solare.
df_annual = df.groupby(df.index.year).agg(
    # Per le metriche annuali (es. resa), che sono costanti per tutto l'anno,
    # usiamo 'first' per prendere il primo valore disponibile.
    Yield_kg_ha=('Yield_kg_ha', 'first'),
    Grape_Sugar_Level=('Grape_Sugar_Level', 'first'),
    Revenue_EUR_ha=('Revenue_EUR_ha', 'first'),
    Production_Cost_EUR_ha=('Production_Cost_EUR_ha', 'first'),
    Selling_Price_EUR_kg=('Selling_Price_EUR_kg', 'first'),
    # Per le metriche climatiche, calcoliamo medie o somme.
    Temperature_C_avg=('Temperature_C', 'mean'),
    Precipitation_mm_sum=('Precipitation_mm', 'sum'),
    Solar_Irradiance_W_m2_avg=('Solar_Irradiance_W_m2', 'mean'),
    Humidity_percent_avg=('Humidity_percent', 'mean'),
    # Le funzioni lambda vengono usate per calcoli personalizzati, come contare i giorni
    # che soddisfano determinate condizioni (es. temperature sopra i 35°C).
    Extreme_Heat_Days=('Temperature_C', lambda x: (x > 35).sum()),
    Frost_Days=('Temperature_C', lambda x: (x < 5).sum()),
    Extreme_Rain_Days=('Precipitation_mm', lambda x: (x > 20).sum()),
    Disease_Risk_Days=('Humidity_percent', lambda x: ((x > 80) & (df.loc[x.index, 'Temperature_C'] > 25)).sum())
).reset_index() # Converte l'indice (l'anno) in una colonna.

df_annual = df_annual.rename(columns={'index': 'Year'})

# Aggiunge una colonna 'Annata' con il formato "YYYY/YYYY+1" per una migliore leggibilità.
df_annual['Annata'] = df_annual['Year'].astype(str) + '/' + (df_annual['Year'] + 1).astype(str)

# Calcola i ricavi e i costi totali moltiplicando i valori per ettaro per il numero di ettari.
df_annual['Total_Revenue_EUR'] = df_annual['Revenue_EUR_ha'] * hectares_simulated
df_annual['Total_Cost_EUR'] = df_annual['Production_Cost_EUR_ha'] * hectares_simulated

# Esclude l'ultimo anno dai dati aggregati per evitare di mostrare dati parziali
# nei grafici della panoramica globale.
df_annual = df_annual.iloc[:-1]

# --- 2. INIZIALIZZAZIONE DELL'APPLICAZIONE DASH ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
# Imposta un tema scuro per i grafici per coerenza visiva.
plotly_template = 'plotly_dark'

# --- 3. CREAZIONE DEI GRAFICI GLOBALI ---
# Questi grafici vengono creati una sola volta all'avvio dell'app, poiché i loro dati non cambiano.

# Grafici a linea per le metriche chiave di produzione, ricavo e qualità.
fig_yield = px.line(df_annual, x='Annata', y='Yield_kg_ha', title="Andamento della Resa per Annata", markers=True, template=plotly_template, labels={'Yield_kg_ha': 'Resa (kg/ha)', 'Annata': 'Annata'})
fig_revenue = px.line(df_annual, x='Annata', y='Total_Revenue_EUR', title="Andamento dei Ricavi per Annata", markers=True, template=plotly_template, labels={'Total_Revenue_EUR': 'Ricavo (€)', 'Annata': 'Annata'})
fig_revenue.update_yaxes(tickprefix="€ ", tickformat=".2s") # Formatta l'asse Y per i ricavi (es. "€ 1.2M").
fig_quality = px.line(df_annual, x='Annata', y='Grape_Sugar_Level', title="Andamento della Qualità dell'Uva per Annata", markers=True, template=plotly_template, labels={'Grape_Sugar_Level': 'Livello Zucchero (°)', 'Annata': 'Annata'})

# Grafico a barre raggruppate per visualizzare gli eventi climatici estremi per ogni annata.
fig_extreme = go.Figure()
fig_extreme.add_trace(go.Bar(x=df_annual['Annata'], y=df_annual['Extreme_Heat_Days'], name='Caldo Estremo', marker_color='#dc3545'))
fig_extreme.add_trace(go.Bar(x=df_annual['Annata'], y=df_annual['Frost_Days'], name='Gelo', marker_color='#17a2b8'))
fig_extreme.add_trace(go.Bar(x=df_annual['Annata'], y=df_annual['Extreme_Rain_Days'], name='Pioggia Torrenziale', marker_color='#007bff'))
fig_extreme.add_trace(go.Bar(x=df_annual['Annata'], y=df_annual['Disease_Risk_Days'], name='Rischio Malattie', marker_color='#ffc107'))
fig_extreme.update_layout(barmode='group', title="Eventi Climatici Estremi per Annata", template=plotly_template, yaxis_title="Numero Giorni", xaxis_title="Annata")

# Grafici a dispersione (scatter plot) per analizzare le correlazioni tra variabili.
# La linea di tendenza ('trendline="ols"') aiuta a visualizzare la relazione.
fig_scatter_precip_yield = px.scatter(df_annual, x='Precipitation_mm_sum', y='Yield_kg_ha', trendline="ols",
                                      title="Precipitazioni Totali vs. Resa",
                                      labels={'Precipitation_mm_sum': 'Precipitazioni Totali (mm)', 'Yield_kg_ha': 'Resa (kg/ha)'},
                                      template=plotly_template)

fig_scatter_temp_sugar = px.scatter(df_annual, x='Temperature_C_avg', y='Grape_Sugar_Level', trendline="ols",
                                    title="Temperatura Media vs. Livello di Zucchero",
                                    labels={'Temperature_C_avg': 'Temperatura Media (°C)', 'Grape_Sugar_Level': 'Livello Zucchero (°)'},
                                    template=plotly_template)

fig_scatter_solar_yield = px.scatter(df_annual, x='Solar_Irradiance_W_m2_avg', y='Yield_kg_ha', trendline="ols",
                                    title="Irradiazione Solare Media vs. Resa",
                                    labels={'Solar_Irradiance_W_m2_avg': 'Irradiazione Media (W/m²)', 'Yield_kg_ha': 'Resa (kg/ha)'},
                                    template=plotly_template)

fig_scatter_disease_yield = px.scatter(df_annual, x='Disease_Risk_Days', y='Yield_kg_ha', trendline="ols",
                                    title="Giorni a Rischio Malattie vs. Resa",
                                    labels={'Disease_Risk_Days': 'Giorni a Rischio Malattie', 'Yield_kg_ha': 'Resa (kg/ha)'},
                                    template=plotly_template)

fig_scatter_solar_sugar = px.scatter(df_annual, x='Solar_Irradiance_W_m2_avg', y='Grape_Sugar_Level', trendline="ols",
                                     title="Irradiazione Solare Media vs. Livello di Zucchero",
                                     labels={'Solar_Irradiance_W_m2_avg': 'Irradiazione Media (W/m²)', 'Grape_Sugar_Level': 'Livello Zucchero (°)'},
                                     template=plotly_template)

fig_scatter_temp_yield = px.scatter(df_annual, x='Temperature_C_avg', y='Yield_kg_ha', trendline="ols",
                                    title="Temperatura Media vs. Resa",
                                    labels={'Temperature_C_avg': 'Temperatura Media (°C)', 'Yield_kg_ha': 'Resa (kg/ha)'},
                                    template=plotly_template)


# --- 4. DEFINIZIONE DEL LAYOUT DEL DASHBOARD ---
# Il layout descrive la struttura della pagina web, organizzata in righe (Row) e colonne (Col).
app.layout = dbc.Container([
    # Riga di intestazione con titolo e informazioni contestuali.
    dbc.Row([
        dbc.Col(html.P(f"Ettari in Simulazione: {hectares_simulated} ha", className="text-left text-muted my-4"), width=4, align="start"),
        dbc.Col(html.H1("Dashboard Cantine Ferrari 🍇", className="text-center my-4 display-4 text-primary"), width=4),
        dbc.Col(html.P(f"Dati aggiornati al: {file_modified_time.strftime('%d/%m/%Y %H:%M')}", className="text-right text-muted my-4"), width=4, align="start"),
    ]),
    dbc.Row(dbc.Col(html.P("Benvenuto nel simulatore di dati ambientali. Esplora le metriche chiave per la gestione della produzione vitivinicola.", className="text-center lead"), width=12)),
    dbc.Row(dbc.Col(html.Hr(), width=12)),
    
    # --- SEZIONE VISUALIZZAZIONE GLOBALE ---
    dbc.Row(dbc.Col(html.H2("Panoramica Globale per Annata", className="text-center my-4 text-secondary"), width=12)),

    # Riga con i tre grafici a linea principali.
    dbc.Row([
        dbc.Col(dcc.Graph(id='kpi-yield-line', figure=fig_yield), lg=4, md=12),
        dbc.Col(dcc.Graph(id='kpi-revenue-line', figure=fig_revenue), lg=4, md=12),
        dbc.Col(dcc.Graph(id='kpi-quality-line', figure=fig_quality), lg=4, md=12),
    ], className="my-4"),

    # Riga con il grafico degli eventi estremi.
    dbc.Row(dbc.Col(html.H4("Analisi degli Eventi Climatici Estremi", className="text-center"), width=12), className="mt-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(id='kpi-extreme-events', figure=fig_extreme), width=12),
    ], className="my-4"),

    # Righe con i grafici di correlazione, organizzati in card per una migliore estetica.
    dbc.Row(dbc.Col(html.H4("Correlazioni tra Variabili Climatiche e Produzione", className="text-center mt-3 mb-2"), width=12), className="mt-4"),
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Precipitazioni Totali vs. Resa"), dcc.Graph(id='scatter-precip-yield', figure=fig_scatter_precip_yield)], body=True), lg=6, md=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Temperatura Media vs. Livello di Zucchero"), dcc.Graph(id='scatter-temp-sugar', figure=fig_scatter_temp_sugar)], body=True), lg=6, md=12),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Irradiazione Solare vs. Resa"), dcc.Graph(id='scatter-solar-yield', figure=fig_scatter_solar_yield)], body=True), lg=6, md=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni a Rischio Malattie vs. Resa"), dcc.Graph(id='scatter-disease-yield', figure=fig_scatter_disease_yield)], body=True), lg=6, md=12),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Irradiazione Solare vs. Livello di Zucchero"), dcc.Graph(id='scatter-solar-sugar', figure=fig_scatter_solar_sugar)], body=True), lg=6, md=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Temperatura Media vs. Resa"), dcc.Graph(id='scatter-temp-yield', figure=fig_scatter_temp_yield)], body=True), lg=6, md=12),
    ], className="mb-4"),

    dbc.Row(dbc.Col(html.Hr(), width=12)),

    # --- SEZIONE VISUALIZZAZIONE DETTAGLIATA ---
    dbc.Row(dbc.Col(html.H2("Dettaglio Giornaliero per Annata", className="text-center my-4 text-secondary"), width=12)),

    # Riga con il dropdown per selezionare l'annata da analizzare.
    dbc.Row([
        dbc.Col(html.P("Seleziona l'annata da analizzare:", className="text-center"), width=12),
        dbc.Col(dcc.Dropdown(
            id='year-dropdown',
            # Le opzioni del dropdown escludono l'ultimo anno disponibile (available_years[:-1]).
            options=[{'label': str(year) + "/" + str(year + 1), 'value': year} for year in available_years[:-1]],
            value=available_years[0], # Valore di default alla prima annata.
            clearable=False,
            className="mb-4",
            searchable=False
        ), width=6, className="mx-auto")
    ], className="mb-4"),
    
    # Righe con le "card" dei KPI (Key Performance Indicators) per l'annata selezionata.
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Resa Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-yield', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="primary", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Ricavo Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-revenue', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="success", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Costo Produzione Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-cost', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="info", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Qualità Uva Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-quality', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="warning", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
    ], className="my-4"),

    # KPI dettagliati sugli eventi climatici.
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni di Caldo Estremo (> 35°C)", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-extreme-heat-days', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="danger", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni di Gelo (< 5°C)", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-frost-days', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="info", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni di Pioggia Torrenziale (> 20mm)", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-extreme-rain-days', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="primary", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni a Rischio Malattie", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-disease-days', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="warning", inverse=True, className="text-center m-2 shadow"), lg=3, md=6, sm=12),
    ], className="my-4"),

    # KPI aggiuntivi per precipitazioni e umidità.
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Precipitazioni Totali Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-precip', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="info", inverse=True, className="text-center m-2 shadow"), lg=6, md=6, sm=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Umidità Media Annata", className="text-center"),
                         dbc.CardBody(html.H4(id='kpi-yearly-humidity', className="text-center text-dark"), style={"backgroundColor": "#f8f9fa"})],
                         color="secondary", inverse=True, className="text-center m-2 shadow"), lg=6, md=6, sm=12),
    ], className="my-4 justify-content-center"),

    # Riga per il grafico climatico dettagliato.
    dbc.Row([
        dbc.Col(dcc.Graph(id='detailed-climate-graph'), width=12),
    ], className="mb-4"),
    
    # Riga per i grafici di analisi delle precipitazioni.
    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardHeader("Distribuzione della Pioggia"),
                         dcc.Graph(id='detailed-precip-hist')], body=True), lg=6, md=12),
        dbc.Col(dbc.Card([dbc.CardHeader("Giorni di Pioggia e Giorni Secchi"),
                         dcc.Graph(id='detailed-rainy-dry-days')], body=True), lg=6, md=12),
    ], className="mb-4"),

], fluid=True) # 'fluid=True' permette al container di occupare tutta la larghezza.

# --- 5. DEFINIZIONE DEI CALLBACK ---
# I callback sono funzioni che vengono eseguite automaticamente quando un input (es. un dropdown) cambia.
# Questo permette di aggiornare dinamicamente gli output (es. grafici, testi).

@app.callback(
    # Lista degli Output: ogni elemento da aggiornare nel layout.
    Output('kpi-yearly-yield', 'children'),
    Output('kpi-yearly-revenue', 'children'),
    Output('kpi-yearly-cost', 'children'),
    Output('kpi-yearly-quality', 'children'),
    Output('kpi-extreme-heat-days', 'children'),
    Output('kpi-frost-days', 'children'),
    Output('kpi-extreme-rain-days', 'children'),
    Output('kpi-disease-days', 'children'),
    Output('kpi-yearly-precip', 'children'),
    Output('kpi-yearly-humidity', 'children'),
    Output('detailed-climate-graph', 'figure'),
    Output('detailed-precip-hist', 'figure'),
    Output('detailed-rainy-dry-days', 'figure'),
    # Input: il valore selezionato nel dropdown 'year-dropdown'.
    Input('year-dropdown', 'value')
)
def update_detailed_view(selected_year):
    """
    Aggiorna la sezione di dettaglio del dashboard in base all'annata selezionata.
    
    Args:
        selected_year (int): L'anno di inizio dell'annata selezionata dall'utente.

    Returns:
        tuple: Una tupla contenente i nuovi valori per tutti gli Output definiti nel callback.
    """
    if selected_year is None:
        # Se nessun anno è selezionato, restituisce valori vuoti per evitare errori.
        return ("N.D.",) * 10 + ({}, {}, {})
    
    # Definisce il periodo dell'annata: da agosto dell'anno selezionato a settembre dell'anno successivo.
    start_date = f'{selected_year}-08-01'
    end_date = f'{selected_year + 1}-09-30'
    # Filtra il DataFrame principale per ottenere solo i dati dell'annata di interesse.
    df_yearly = df[(df.index >= start_date) & (df.index <= end_date)]
    
    # Se il DataFrame filtrato è vuoto, restituisce messaggi di "Nessun dato".
    if df_yearly.empty:
        return ("Nessun dato",) * 10 + ({}, {}, {})

    # Calcola i valori per i KPI utilizzando i dati filtrati.
    yearly_yield = df_yearly['Yield_kg_ha'].iloc[0]
    yearly_revenue_per_ha = df_yearly['Revenue_EUR_ha'].iloc[0]
    yearly_cost_per_ha = df_yearly['Production_Cost_EUR_ha'].iloc[0]
    yearly_quality = df_yearly['Grape_Sugar_Level'].iloc[0]
    hectares = df_yearly['Hectares_Simulated'].iloc[0]
    
    total_revenue = yearly_revenue_per_ha * hectares
    total_cost = yearly_cost_per_ha * hectares

    extreme_heat_days = (df_yearly['Temperature_C'] > 35).sum()
    frost_days = (df_yearly['Temperature_C'] < 5).sum()
    extreme_rain_days = (df_yearly['Precipitation_mm'] > 20).sum()
    disease_risk_days = ((df_yearly['Temperature_C'] > 25) & (df_yearly['Humidity_percent'] > 80)).sum()
    
    total_precip = df_yearly['Precipitation_mm'].sum()
    avg_humidity = df_yearly['Humidity_percent'].mean()

    # Crea l'etichetta dell'annata per i titoli dei grafici.
    annata_label = f"{selected_year}/{selected_year + 1}"

    # Crea il grafico dettagliato del clima per l'annata.
    # 'make_subplots' con 'secondary_y' permette di avere due assi Y (uno per temp/irrad, uno per precip).
    fig_detailed_climate = make_subplots(specs=[[{"secondary_y": True}]])
    fig_detailed_climate.add_trace(go.Scatter(x=df_yearly.index, y=df_yearly['Temperature_C'], name='Temperatura (°C)', mode='lines'), secondary_y=False)
    fig_detailed_climate.add_trace(go.Scatter(x=df_yearly.index, y=df_yearly['Solar_Irradiance_W_m2'], name='Irradiazione Solare (W/m²)', mode='lines'), secondary_y=False)
    fig_detailed_climate.add_trace(go.Bar(x=df_yearly.index, y=df_yearly['Precipitation_mm'], name='Precipitazioni (mm)'), secondary_y=True)
    fig_detailed_climate.update_layout(title=f"Andamento Climatico Giornaliero - Annata {annata_label}", template=plotly_template, hovermode="x unified")
    fig_detailed_climate.update_yaxes(title_text="Temperatura (°C) / Irradiazione (W/m²)", secondary_y=False)
    fig_detailed_climate.update_yaxes(title_text="Precipitazioni (mm)", secondary_y=True)

    # Crea l'istogramma della distribuzione delle precipitazioni.
    fig_detailed_precip_hist = px.histogram(df_yearly, x='Precipitation_mm', nbins=50,
                                   title=f"Distribuzione Precipitazioni - Annata {annata_label}",
                                   labels={'Precipitation_mm': 'Precipitazioni (mm)', 'count': 'Frequenza'},
                                   template=plotly_template, marginal='box')
    
    # Crea il grafico a torta per il rapporto tra giorni piovosi e secchi.
    rainy_days_count = (df_yearly['Precipitation_mm'] > 0).sum()
    dry_days_count = (df_yearly['Precipitation_mm'] == 0).sum()
    fig_detailed_rainy_dry = px.pie(names=['Giorni di Pioggia', 'Giorni Secchi'], values=[rainy_days_count, dry_days_count],
                           title=f"Rapporto Giorni Piovosi/Secchi - Annata {annata_label}",
                           template=plotly_template, hole=0.3)
                           
    # Restituisce tutti i valori calcolati e i grafici creati.
    # L'ordine deve corrispondere esattamente a quello degli Output nel decoratore.
    return (
        f"🍇 {yearly_yield:.2f} kg/ha",
        f"€ {total_revenue / 1_000_000:.2f} milioni",
        f"€ {total_cost / 1_000_000:.2f} milioni",
        f"{yearly_quality:.2f}°",
        f"{extreme_heat_days} giorni",
        f"{frost_days} giorni",
        f"{extreme_rain_days} giorni",
        f"{disease_risk_days} giorni",
        f"💧 {total_precip:.2f} mm",
        f"💨 {avg_humidity:.2f} %",
        fig_detailed_climate,
        fig_detailed_precip_hist,
        fig_detailed_rainy_dry
    )

# --- 6. AVVIO DELL'APPLICAZIONE ---
# Il blocco 'if __name__ == "__main__"' assicura che il server di sviluppo
# venga avviato solo quando lo script è eseguito direttamente.
if __name__ == '__main__':
    app.run(debug=True)