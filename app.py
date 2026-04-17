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
    st.error("Errore nei Secrets di Streamlit. Verifica SUPABASE_URL e SUPABASE_KEY.")
    st.stop()

# --- FUNZIONI DATABASE ---
def load_watchlist():
    try:
        response = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Errore nel caricamento: {e}")
        return []

def add_to_watchlist(symbol, name, price):
    try:
        data = {"symbol": str(symbol), "name": str(name), "price": float(price)}
        supabase.table("watchlist").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")
        return False

def delete_from_watchlist(item_id):
    try:
        supabase.table("watchlist").delete().eq("id", item_id).execute()
        return True
    except Exception as e:
        st.error(f"Errore nella cancellazione: {e}")
        return False

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Ricerca Titoli")
    search_type = st.radio("Cerca per:", ["Ticker", "ISIN"])
    query = st.text_input(f"Inserisci {search_type}", placeholder="Es: AAPL o US0378331005").strip()
    suffix = st.selectbox("Mercato", ["Nessuno (Auto)", ".MI", ".DE", ".L", ".PA"])
    search_btn = st.button("🔍 Cerca Titolo", type="primary")

# --- LOGICA DI RICERCA ---
if query and search_btn:
    # Costruzione query corretta
    full_query = query + (suffix if suffix != "Nessuno (Auto)" and search_type == "Ticker" else "")
    
    with st.spinner('Recupero dati in corso...'):
        ticker_obj = yf.Ticker(full_query)
        info = ticker_obj.info
        
        if 'symbol' in info:
            curr_price = info.get('currentPrice') or info.get('regularMarketPrice')
            name = info.get('longName') or info.get('shortName') or query
            
            # --- AREA RISULTATI ---
            st.header(f"{name} ({info.get('symbol')})")
            
            col_metrics, col_btn = st.columns([3, 1])
            
            with col_metrics:
                c1, c2, c3 = st.columns(3)
                c1.metric("Prezzo", f"{curr_price} {info.get('currency', '')}")
                c2.metric("Variazione %", f"{info.get('regularMarketChangePercent', 0):.2f}%")
                c3.metric("Borsa", info.get('exchange', 'N/A'))
            
            with col_btn:
                # Definiamo col_a correttamente all'interno dello scope dove serve
                if st.button("⭐ Salva nel Cloud"):
                    if add_to_watchlist(info['symbol'], name, curr_price):
                        st.toast("Salvato con successo!", icon="✅")
                        time.sleep(1)
                        st.rerun()

            # Grafico
            hist = ticker_obj.history(period="1mo")
            if not hist.empty:
                fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00cf8d'))])
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Titolo non trovato. Prova a cambiare mercato o inserire il Ticker diretto.")

st.divider()

# --- WATCHLIST ---
st.subheader("📁 La tua Watchlist (Supabase Cloud)")
cloud_data = load_watchlist()

if cloud_data:
    df_display = pd.DataFrame(cloud_data)
    for _, row in df_display.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"**{row['name']}**")
            col2.write(f"`{row['symbol']}`")
            col3.write(f"**{row['price']}**")
            if col4.button("Rimuovi", key=f"del_{row['id']}"):
                if delete_from_watchlist(row['id']):
                    st.rerun()
else:
    st.info("La tua watchlist è vuota. Cerca un titolo e clicca su 'Salva'.")
