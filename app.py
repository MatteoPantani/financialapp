import streamlit as st
import requests

st.set_page_config(page_title="ISIN Tracker", page_icon="📈")

st.title("🔍 ISIN Real-Time Info")

# --- CONFIGURAZIONE API ---
# CONSIGLIO: Se usi Streamlit Cloud, inserisci la chiave in "Secrets"
API_KEY = st.text_input("Inserisci la tua API Key di Financial Modeling Prep:", type="password")

def get_data_by_isin(isin):
    if not API_KEY:
        st.warning("Per favore, inserisci l'API Key.")
        return None

    # 1. Ricerca tramite ISIN
    search_url = f"https://financialmodelingprep.com/api/v3/search-isin?isin={isin}&apikey={API_KEY}"
    
    try:
        response = requests.get(search_url).json()
        
        # Gestione errori API (es. chiave scaduta o errata)
        if isinstance(response, dict) and "Error Message" in response:
            st.error(f"Errore API: {response['Error Message']}")
            return None
            
        if not response or len(response) == 0:
            st.warning(f"Nessun titolo trovato per l'ISIN: {isin}")
            return None
        
        # Se arriviamo qui, abbiamo trovato il simbolo
        symbol = response[0].get('symbol')
        exchange = response[0].get('exchangeShortName')
        
        # 2. Recupero quotazione
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}"
        quote_data = requests.get(quote_url).json()
        
        if quote_data and len(quote_data) > 0:
            return quote_data[0]
            
    except Exception as e:
        st.error(f"Si è verificato un errore tecnico: {e}")
    
    return None

# --- INTERFACCIA ---
isin_input = st.text_input("Inserisci Codice ISIN (es. US0378331005):").upper().strip()

if isin_input:
    data = get_data_by_isin(isin_input)
    if data:
        st.success(f"Dati per {data.get('name')}")
        col1, col2 = st.columns(2)
        col1.metric("Prezzo", f"{data.get('price')} {data.get('symbol')}")
        col2.metric("Variazione %", f"{data.get('changesPercentage')}%")
        
        with st.expander("Vedi dettagli completi"):
            st.write(data)
