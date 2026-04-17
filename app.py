import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="FinHub Pro", layout="wide")

# Connessione
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNZIONI ---
def add_to_db(symbol, name, price):
    try:
        data = {"symbol": str(symbol), "name": str(name), "price": float(price)}
        # Esegui l'insert e chiedi di restituire il dato inserito
        res = supabase.table("watchlist").insert(data).execute()
        return len(res.data) > 0
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def load_db():
    res = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
    return res.data

def delete_item(id):
    supabase.table("watchlist").delete().eq("id", id).execute()
    st.rerun()

# --- INTERFACCIA ---
st.title("📈 Il mio Portafoglio Cloud")

with st.sidebar:
    query = st.text_input("Cerca Ticker (es. AAPL, BTC-USD, RACE.MI)").upper()
    if st.button("🔍 Cerca"):
        st.session_state.search = query

if 'search' in st.session_state and st.session_state.search:
    t = yf.Ticker(st.session_state.search)
    info = t.info
    if 'symbol' in info:
        p = info.get('currentPrice') or info.get('regularMarketPrice')
        n = info.get('shortName')
        
        col1, col2 = st.columns([3, 1])
        col1.metric(n, f"{p} {info.get('currency', '')}")
        
        if col2.button("⭐ Salva nel Cloud"):
            if add_to_db(info['symbol'], n, p):
                st.success("Aggiunto!")
                time.sleep(1)
                st.rerun()
    else:
        st.error("Titolo non trovato.")

st.divider()

# --- VISUALIZZAZIONE WATCHLIST ---
st.subheader("📁 Watchlist Salvata")
items = load_db()

if items:
    for i in items:
        # Evitiamo di mostrare il record di TEST se vuoi, o mostriamoli tutti
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"**{i['name']}**")
        c2.write(f"`{i['symbol']}`")
        c3.write(f"{i['price']}")
        if c4.button("Rimuovi", key=f"del_{i['id']}"):
            delete_item(i['id'])
else:
    st.info("Nessun titolo salvato.")
