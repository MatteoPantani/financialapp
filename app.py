import streamlit as st
import requests

st.set_page_config(page_title="ISIN Tracker 2026", page_icon="📈")

st.title("🔍 ISIN Real-Time Info")

# Sezione API Key
API_KEY = st.text_input("Inserisci la tua API Key:", type="password")

def get_data_by_isin(isin):
    if not API_KEY:
        st.warning("Inserisci l'API Key per continuare.")
        return None

    # --- NUOVO ENDPOINT 2026 ---
    # Usiamo la ricerca universale che supporta ticker, nomi e ISIN
    search_url = f"https://financialmodelingprep.com/api/v3/search?query={isin}&limit=1&apikey={API_KEY}"
    
    try:
        search_response = requests.get(search_url).json()
        
        # Controllo se l'API restituisce un errore di sottoscrizione
        if isinstance(search_response, dict) and "Error Message" in search_response:
            st.error(f"Errore API: {search_response['Error Message']}")
            return None
            
        if not search_response:
            st.warning(f"Nessun risultato per l'ISIN: {isin}. Verifica che sia corretto.")
            return None
        
        # Recuperiamo il simbolo dal primo risultato della ricerca
        symbol = search_response[0].get('symbol')
        
        # Ora prendiamo i dati reali (Quote) usando il simbolo ottenuto
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={API_KEY}"
        quote_data = requests.get(quote_url).json()
        
        if quote_data:
            return quote_data[0]
            
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
    
    return None

# --- UI APP ---
isin_input = st.text_input("Inserisci Codice ISIN (es. US0378331005):").upper().strip()

if isin_input:
    with st.spinner('Ricerca in corso...'):
        data = get_data_by_isin(isin_input)
        
        if data:
            st.success(f"Titolo trovato: **{data.get('name')}**")
            
            # Visualizzazione dati principali
            c1, c2, c3 = st.columns(3)
            c1.metric("Prezzo", f"{data.get('price')} {data.get('currency', '')}")
            c2.metric("Variazione", f"{data.get('changesPercentage')}%")
            c3.metric("Scambio", data.get('exchangedisplayName', 'N/A'))
            
            # Dettagli aggiuntivi
            with st.expander("Dettagli Tecnici"):
                st.json(data)
