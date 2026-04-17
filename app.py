import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="FinHub Pro 2026", page_icon="💎", layout="wide")

# --- CONNESSIONE SUPABASE ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Configurazione Secrets mancante o errata. Verifica SUPABASE_URL e SUPABASE_KEY.")
    st.stop()

# --- FUNZIONI DATABASE ---
def load_watchlist():
    try:
        # Recupera i dati ordinati per i più recenti
        response = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Errore caricamento watchlist: {e}")
        return []

def add_to_watchlist(symbol, name, price):
    st.write("--- LOG DI SALVATAGGIO ---")
    data_to_send = {
        "symbol": str(symbol),
        "name": str(name) if name else "N/A",
        "price": float(price) if price else 0.0
    }
    st.json(data_to_send)
    
    try:
        res = supabase.table("watchlist").insert(data_to_send).execute()
        
        if not res.data:
            st.error("⚠️ Supabase ha ricevuto il comando ma NON ha scritto i dati.")
            st.info("Esegui 'ALTER TABLE watchlist DISABLE ROW LEVEL SECURITY;' nell'SQL Editor di Supabase.")
            st.write("Dettaglio tecnico:", res)
            return False
        
        st.success("✅ Salvato nel cloud con successo!")
        return True
    except Exception as e:
        st.error(f"❌ Errore critico database: {e}")
        return False

def delete_from_watchlist(item_id):
    try:
        supabase.table("watchlist").delete().eq("id", item_id).execute()
        return True
    except Exception as e:
        st.error(f"Errore cancellazione: {e}")
        return False

# --- INTERFACCIA SIDEBAR ---
with st.sidebar:
    st.title("⚙️ FinHub Control")
    search_type = st.radio("Cerca per:", ["Ticker", "ISIN"])
    query = st.text_input(f"Inserisci {search_type}", placeholder="Es: AAPL o US0378331005").strip()
    suffix = st.selectbox("Mercato (solo per Ticker)", ["Nessuno (Auto)", ".MI", ".DE", ".L", ".PA"])
    search_btn = st.button("🔍 Cerca", type="primary")
    
    if st.button("🗑️ Svuota Sessione"):
        st.rerun()

# --- LOGICA DI RICERCA ---
if query and search_btn:
    # Costruiamo il ticker corretto
    full_query = query + (suffix if suffix != "Nessuno (Auto)" and search_type == "Ticker" else "")
    
    with st.spinner('Interrogazione mercati...'):
        t_obj = yf.Ticker(full_query)
        info = t_obj.info
        
        if 'symbol' in info:
            curr_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            long_name = info.get('longName') or info.get('shortName') or query
            
            # --- DISPLAY DATI ---
            st.header(f"{long_name} ({info.get('symbol')})")
            
            c_met, c_sav = st.columns([3, 1])
            
            with c_met:
                m1, m2, m3 = st.columns(3)
                m1.metric("Prezzo", f"{curr_price} {info.get('currency', '')}")
                m2.metric("Variazione %", f"{info.get('regularMarketChangePercent', 0):.2f}%")
                m3.metric("Borsa", info.get('exchange', 'N/A'))
            
            with c_sav:
                if st.button("⭐ SALVA NEL CLOUD"):
                    if add_to_watchlist(info['symbol'], long_name, curr_price):
                        time.sleep(1.5)
                        st.rerun()

            # Grafico mensile
            hist = t_obj.history(period="1mo")
            if not hist.empty:
                fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00cf8d', width=3))])
                fig.update_layout(title="Andamento Ultimi 30 Giorni", height=350, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Titolo non trovato. Prova a specificare il mercato o usa il Ticker diretto.")

st.divider()

# --- WATCHLIST (DA SUPABASE) ---
st.subheader("📁 Watchlist Cloud")
cloud_items = load_watchlist()

if cloud_items:
    # Mostriamo la watchlist in una tabella pulita o in card
    for item in cloud_items:
        with st.expander(f"📌 {item['name']} ({item['symbol']}) - {item['price']}"):
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"Aggiunto il: {item['created_at']}")
            if col_b.button("Elimina", key=f"btn_{item['id']}"):
                if delete_from_watchlist(item['id']):
                    st.rerun()
else:
    st.info("La tua watchlist su Supabase è vuota. Cerca un titolo e clicca su 'Salva'.")
