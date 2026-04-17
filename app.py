import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client

# --- CONNESSIONE SUPABASE ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="FinHub Pro", page_icon="💎", layout="wide")

# --- FUNZIONI DATABASE ---
def load_watchlist():
    # Legge i dati dal database
    response = supabase.table("watchlist").select("*").execute()
    return response.data

def add_to_watchlist(symbol, name, price):
    # Inserisce un nuovo titolo
    data = {"symbol": symbol, "name": name, "price": price}
    supabase.table("watchlist").insert(data).execute()

def delete_from_watchlist(item_id):
    # Elimina un titolo tramite ID
    supabase.table("watchlist").delete().eq("id", item_id).execute()

# --- SIDEBAR E RICERCA ---
with st.sidebar:
    st.title("⚙️ Controllo")
    search_type = st.radio("Cerca per:", ["Ticker", "ISIN"])
    query = st.text_input(f"Inserisci {search_type}").strip()
    suffix = st.selectbox("Borsa", ["Nessuno (Auto)", ".MI", ".DE", ".L", ".PA"])
    search_btn = st.button("🔍 Cerca", type="primary")

# --- LOGICA PRINCIPALE ---
if query and search_btn:
    full_query = query + (suffix if suffix != "Nessuno (Auto)" and search_type == "Ticker" else "")
    ticker_obj = yf.Ticker(full_query)
    info = ticker_obj.info
    
    if 'symbol' in info:
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        col_t, col_a = st.columns([3, 1])
        col_t.header(f"{info.get('longName')} ({info.get('symbol')})")
        
        if col_a.button("⭐ Salva nel Cloud"):
            add_to_watchlist(info['symbol'], info.get('shortName'), curr_price)
            st.success("Salvato su Supabase!")
            st.rerun()

        # Grafico e Metric Cards (come prima)...
        st.metric("Prezzo", f"{curr_price} {info.get('currency')}")
        # [Grafico Plotly qui]
    else:
        st.error("Titolo non trovato.")

st.divider()

# --- VISUALIZZAZIONE WATCHLIST DAL CLOUD ---
st.subheader("📁 La tua Watchlist su Supabase")
data_cloud = load_watchlist()

if data_cloud:
    df = pd.DataFrame(data_cloud)
    for index, row in df.iterrows():
        cols = st.columns([2, 2, 1, 1])
        cols[0].write(f"**{row['name']}**")
        cols[1].write(f"`{row['symbol']}`")
        cols[2].write(f"{row['price']}")
        if cols[3].button("Elimina", key=f"del_{row['id']}"):
            delete_from_watchlist(row['id'])
            st.rerun()
else:
    st.info("Nessun dato nel cloud. Cerca e salva un titolo.")
