import streamlit as st
import requests
import pandas as pd

# Configurazione Pagina
st.set_page_config(page_title="ISIN Tracker", page_icon="📈", layout="centered")

st.title("🔍 ISIN Real-Time Info")
st.write("Inserisci un codice ISIN per ottenere i dati finanziari aggiornati.")

# --- CONFIGURAZIONE API ---
API_KEY = "czfxszRYE1pquPbskwRGVBprTvhdWCJW"  # Inserisci qui la tua chiave

def get_data_by_isin(isin):
    # 1. Cerchiamo il Ticker tramite ISIN
    search_url = f"https://financialmodelingprep.com/api/v3/search-isin?isin={isin}&apikey={API_KEY}"
    response = requests.get(search_url).json()
    
    if not response:
        return None
    
    symbol = response[0]['symbol']
    exchange = response[0]['exchangeShortName']
    
    # 2. Recuperiamo la quotazione giornaliera
    quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}"
    quote_data = requests.get(quote_url).json()
    
    if quote_data:
        data = quote_data[0]
        return {
            "Nome": data['name'],
            "Simbolo": data['symbol'],
            "Prezzo": f"{data['price']} {exchange}",
            "Variazione %": f"{data['changesPercentage']}%",
            "Volume": data['volume'],
            "Capitalizzazione": f"{data['marketCap']:,}"
        }
    return None

# --- INTERFACCIA UTENTE ---
isin_input = st.text_input("Inserisci Codice ISIN (es. US0378331005):", "").upper().strip()

if isin_input:
    with st.spinner('Recupero dati in corso...'):
        info = get_data_by_isin(isin_input)
        
        if info:
            st.success(f"Dati trovati per: **{info['Nome']}**")
            
            # Layout a colonne per Mobile/Desktop
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prezzo Attuale", info['Prezzo'])
                st.write(f"**Simbolo:** {info['Simbolo']}")
            with col2:
                st.metric("Variazione", info['Variazione %'])
                st.write(f"**Volume:** {info['Volume']}")
            
            st.divider()
            st.write(f"**Market Cap:** {info['Capitalizzazione']}")
        else:
            st.error("ISIN non trovato o API Key non valida.")

st.info("Nota: I dati vengono aggiornati una volta al giorno o all'apertura dell'app.")
