import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- SETUP PAGINA ---
st.set_page_config(page_title="FinHub Debug Mode", layout="wide")
st.title("🛠️ Debugging Supabase Connection")

# --- 1. TEST CONNESSIONE SECRETS ---
st.subheader("1. Verifica Credenziali")
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    st.success(f"Connessione al client stabilita con URL: {url[:20]}...")
except Exception as e:
    st.error(f"Errore critico nei Secrets: {e}")
    st.stop()

# --- 2. FUNZIONE DI SALVATAGGIO CON LOG ---
def debug_add_to_watchlist(symbol, name, price):
    st.write("---")
    st.info(f"Tentativo di salvataggio per: {symbol}")
    
    # Preparazione dati
    data_to_send = {
        "symbol": str(symbol),
        "name": str(name),
        "price": float(price)
    }
    st.json(data_to_send) # Mostra esattamente cosa stiamo inviando
    
    try:
        # Esecuzione chiamata
        st.write("Inviando richiesta a Supabase...")
        response = supabase.table("watchlist").insert(data_to_send).execute()
        
        # Analisi risposta
        st.write("Risposta ricevuta dal server:")
        st.write(response)
        
        if hasattr(response, 'data') and len(response.data) > 0:
            st.success("✅ Riga creata correttamente nel database!")
            return True
        else:
            st.warning("⚠️ Il server ha risposto ma 'data' è vuoto. Controlla le regole RLS su Supabase.")
            return False
            
    except Exception as e:
        st.error(f"❌ Errore durante l'esecuzione dell'INSERT: {str(e)}")
        return False

# --- 3. LOGICA DI RICERCA ---
with st.sidebar:
    st.header("Ricerca")
    query = st.text_input("Inserisci Ticker (es. AAPL)").upper()
    btn = st.button("Cerca")

if query and btn:
    t = yf.Ticker(query)
    info = t.info
    if 'symbol' in info:
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice')
        st.metric("Titolo trovato", info.get('symbol'), curr_price)
        
        # IL PULSANTE DI TEST
        if st.button("🚀 TEST: SALVA ORA"):
            success = debug_add_to_watchlist(info['symbol'], info.get('shortName', 'N/A'), curr_price)
            if success:
                st.balloons()
                time.sleep(2)
                st.rerun()
    else:
        st.error("Titolo non trovato su Yahoo Finance.")

st.divider()

# --- 4. VERIFICA LETTURA ---
st.subheader("2. Stato attuale del Database")
try:
    check_db = supabase.table("watchlist").select("*").limit(5).execute()
    if check_db.data:
        st.write("Dati trovati nel cloud:")
        st.table(check_db.data)
    else:
        st.info("Il database risponde ma la tabella è vuota.")
except Exception as e:
    st.error(f"Impossibile leggere dalla tabella 'watchlist': {e}")
