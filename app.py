import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configurazione stile moderno
st.set_page_config(page_title="FinHub 2026", page_icon="💎", layout="wide")

# Inizializzazione memoria (Watchlist)
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# --- CSS Personalizzato per un look moderno ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Ricerca e Filtri) ---
with st.sidebar:
    st.title("⚙️ Controllo")
    search_type = st.radio("Cerca per:", ["Ticker", "ISIN"])
    query = st.text_input(f"Inserisci {search_type}", placeholder="Es: AAPL o US0378331005").strip()
    
    suffix = st.selectbox("Seleziona Borsa (opzionale)", 
                          ["Nessuno (Auto)", ".MI (Milano)", ".DE (Francoforte)", ".L (Londra)", ".PA (Parigi)"],
                          index=0)
    
    col_search, col_reset = st.columns(2)
    search_btn = col_search.button("🔍 Cerca", type="primary")
    if col_reset.button("🗑️ Reset App"):
        st.session_state.watchlist = []
        st.rerun()

# --- LOGICA DI RECUPERO ---
def fetch_data(q, s_type, s_suffix):
    clean_query = q
    if s_suffix != "Nessuno (Auto)":
        # Se l'utente cerca per Ticker aggiungiamo il suffisso della borsa
        if s_type == "Ticker" and "." not in q:
            clean_query = f"{q}{s_suffix}"
    
    ticker = yf.Ticker(clean_query)
    return ticker

# --- MAIN INTERFACE ---
if query and search_btn:
    ticker_obj = fetch_data(query, search_type, suffix)
    info = ticker_obj.info
    
    if 'symbol' in info:
        # Layout Intestazione
        col_title, col_action = st.columns([3, 1])
        with col_title:
            st.header(f"{info.get('longName', query)} ({info.get('symbol')})")
            st.caption(f"Settore: {info.get('sector', 'N/A')} | Valuta: {info.get('currency')}")
        
        with col_action:
            if st.button("⭐ Salva in Watchlist"):
                if info['symbol'] not in [x['symbol'] for x in st.session_state.watchlist]:
                    st.session_state.watchlist.append({
                        "symbol": info['symbol'],
                        "name": info.get('shortName'),
                        "price": info.get('currentPrice') or info.get('regularMarketPrice')
                    })
                    st.toast("Aggiunto ai preferiti!")

        # Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice')
        prev_close = info.get('previousClose')
        change = ((curr_price - prev_close) / prev_close) * 100 if prev_close else 0
        
        c1.metric("Prezzo", f"{curr_price} {info.get('currency')}")
        c2.metric("Variazione %", f"{change:.2f}%")
        c3.metric("Min/Max Day", f"{info.get('dayLow')} - {info.get('dayHigh')}")
        c4.metric("Volume", f"{info.get('regularMarketVolume', 0):,}")

        # Grafico Semplice (Ultimi 30 giorni)
        hist = ticker_obj.history(period="1mo")
        if not hist.empty:
            fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist['Close'], line=dict(color='#00cf8d', width=3))])
            fig.update_layout(title="Andamento ultimo mese", margin=dict(l=20, r=20, t=40, b=20), height=300)
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Dati non trovati. Se è un titolo europeo, prova a selezionare la borsa corretta (es. .MI per Milano).")

st.divider()

# --- WATCHLIST SEZIONE (Dati salvati) ---
st.subheader("📁 La tua Watchlist")
if st.session_state.watchlist:
    df_watch = pd.DataFrame(st.session_state.watchlist)
    
    # Visualizzazione con possibilità di eliminare
    for i, item in enumerate(st.session_state.watchlist):
        cols = st.columns([3, 1, 1])
        cols[0].write(f"**{item['name']}** ({item['symbol']})")
        cols[1].write(f"{item['price']}")
        if cols[2].button("Rimuovi", key=f"del_{i}"):
            st.session_state.watchlist.pop(i)
            st.rerun()
else:
    st.info("La tua watchlist è vuota. Cerca un titolo e clicca su 'Salva' per vederlo qui.")
