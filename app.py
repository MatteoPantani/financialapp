import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- SETUP PAGINA ---
st.set_page_config(page_title="FinHub Debugger", layout="wide")
st.title("🕵️ Diagnostica Connessione Supabase")

# --- 1. TEST CONNESSIONE SECRETS ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    st.sidebar.success("✅ Secrets caricati")
except Exception as e:
    st.sidebar.error(f"❌ Errore Secrets: {e}")
    st.stop()

# --- 2. FUNZIONE DI SALVATAGGIO "PARLANTE" ---
def add_to_watchlist_debug(symbol, name, price):
    st.write("### 🛠️ Log Operazione di Salvataggio")
    
    # Prepariamo l'oggetto
    payload = {
        "symbol": str(symbol),
        "name": str(name) if name else "N/A",
        "price": float(price) if price else 0.0
    }
    
    st.write("**1. Dati inviati al database:**")
    st.json(payload)
    
    try:
        st.write("**2. Chiamata API in corso...**")
        # Tentativo di inserimento
        res = supabase.table("watchlist").insert(payload).execute()
        
        st.write("**3. Risposta integrale dal server:**")
        st.write(res)
        
        # Verifica se l'inserimento è andato a buon fine
        if hasattr(res, 'data') and len(res.data) > 0:
            st.success("🎉 SUCCESSO! Riga creata su Supabase.")
            return True
        else:
            st.error("❌ IL SERVER HA RISPOSTO MA NON HA SCRITTO.")
            st.warning("Se 'data' è vuoto ([]) e non vedi errori, significa che la RLS su Supabase sta ancora bloccando l'accesso.")
            return False
            
    except Exception as e:
        st.error(f"⚠️ ERRORE CRITICO DURANTE L'INSERT:")
        st.code(str(e)) # Mostra l'errore tecnico per esteso
        return False

# --- 3. RICERCA E TEST ---
with st.sidebar:
    query = st.text_input("Inserisci Ticker per il test (es. AAPL)").upper()
    search_btn = st.button("Cerca")

if query and search_btn:
    t = yf.Ticker(query)
    info = t.info
    if 'symbol' in info:
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice')
        st.subheader(f"Titolo: {info.get('shortName')}")
        st.metric("Prezzo", f"{curr_price}")
        
        if st.button("🚀 TENTA SALVATAGGIO"):
            success = add_to_watchlist_debug(info['symbol'], info.get('shortName'), curr_price)
            if success:
                st.balloons()
                time.sleep(2)
                st.rerun()
    else:
        st.error("Titolo non trovato.")

st.divider()

# --- 4. TEST DI LETTURA ---
st.subheader("📋 Stato Tabella (SELECT)")
try:
    test_read = supabase.table("watchlist").select("*").limit(1).execute()
    st.write("Test di lettura riuscito. Dati presenti:")
    st.write(test_read.data)
except Exception as e:
    st.error(f"Errore durante la lettura: {e}")
