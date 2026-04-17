import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="ISIN Finder Free", page_icon="💰")

st.title("📈 ISIN Financial Tracker")
st.write("Recupero dati tramite Yahoo Finance (Senza API Key)")

# --- LOGICA DI RECUPERO ---
def get_data(isin):
    try:
        # yfinance può cercare direttamente per ISIN in molti casi
        ticker = yf.Ticker(isin)
        info = ticker.info
        
        # Se non trova nulla con l'ISIN, il dizionario 'info' sarà quasi vuoto
        if 'regularMarketPrice' not in info and 'currentPrice' not in info:
            return None
            
        return info
    except Exception as e:
        return str(e)

# --- INTERFACCIA ---
isin_input = st.text_input("Inserisci ISIN (es. US0378331005 o IT0005218380):").strip()

if isin_input:
    with st.spinner('Ricerca nel database globale...'):
        data = get_data(isin_input)
        
        if isinstance(data, dict):
            nome = data.get('longName', 'N/A')
            prezzo = data.get('currentPrice') or data.get('regularMarketPrice')
            valuta = data.get('currency', 'USD')
            var = data.get('regularMarketChangePercent', 0)
            
            st.success(f"Trovato: **{nome}**")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Prezzo", f"{prezzo} {valuta}")
            col2.metric("Variazione", f"{var:.2f}%")
            col3.metric("Settore", data.get('sector', 'N/A'))
            
            with st.expander("Vedi tutti i dati disponibili"):
                st.write(data)
        else:
            st.error("ISIN non trovato. Nota: Alcuni ISIN europei potrebbero richiedere il Ticker specifico (es. RACE.MI invece dell'ISIN).")

st.info("Consiglio: Se l'ISIN non viene trovato, prova a cercare il Ticker corrispondente su Yahoo Finance.")
