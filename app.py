import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- SETUP ---
st.set_page_config(page_title="FinHub Portfolio", layout="wide")

# Connessione Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNZIONI DB ---
def add_to_portfolio(symbol, name, price_now, pmc, shares):
    try:
        data = {
            "symbol": str(symbol),
            "name": str(name),
            "price": float(price_now), # Ultimo prezzo conosciuto
            "pmc": float(pmc),
            "shares": float(shares)
        }
        res = supabase.table("watchlist").insert(data).execute()
        return len(res.data) > 0
    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")
        return False

def load_portfolio():
    res = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
    return res.data

def delete_asset(id):
    supabase.table("watchlist").delete().eq("id", id).execute()
    st.rerun()

# --- INTERFACCIA DI INSERIMENTO ---
st.title("💼 Gestione Portfolio")

with st.expander("➕ Aggiungi una nuova posizione"):
    col_search, col_data = st.columns([1, 2])
    
    with col_search:
        ticker_input = st.text_input("Ticker/ISIN", placeholder="es. AAPL o SWDA.MI").upper()
        search_btn = st.button("Verifica Titolo")

    if ticker_input and search_btn:
        t = yf.Ticker(ticker_input)
        info = t.info
        if 'symbol' in info:
            st.session_state.temp_asset = info
            st.success(f"Trovato: {info.get('shortName')}")
        else:
            st.error("Titolo non trovato.")

    if 'temp_asset' in st.session_state:
        asset = st.session_state.temp_asset
        st.write("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            qta = st.number_input("Quantità posseduta", min_value=0.0, step=0.1)
        with c2:
            pmc_input = st.number_input("Prezzo Medio Carico (PMC)", min_value=0.0, step=0.01)
        with c3:
            st.write(f"Prezzo Attuale: **{asset.get('currentPrice') or asset.get('regularMarketPrice')}**")
            if st.button("💾 Salva Posizione", type="primary"):
                current_p = asset.get('currentPrice') or asset.get('regularMarketPrice')
                if add_to_portfolio(asset['symbol'], asset.get('shortName'), current_p, pmc_input, qta):
                    st.success("Asset aggiunto al portfolio!")
                    del st.session_state.temp_asset
                    time.sleep(1)
                    st.rerun()

st.divider()

# --- TABELLA PORTFOLIO ---
st.subheader("📊 Le tue Posizioni")
data = load_portfolio()

if data:
    # Creiamo una lista per il DataFrame così da fare calcoli massivi
    rows = []
    total_market_value = 0
    total_invested = 0

    for item in data:
        # Recupero prezzo aggiornato (per semplicità in questa fase usiamo l'ultimo salvato o una nuova chiamata)
        # Nota: in un'app reale qui faremmo una chiamata batch a yfinance
        current_price = item['price'] 
        invested = item['shares'] * item['pmc']
        market_value = item['shares'] * current_price
        pl_percent = ((current_price - item['pmc']) / item['pmc'] * 100) if item['pmc'] > 0 else 0
        pl_abs = market_value - invested
        
        rows.append({
            "ID": item['id'],
            "Titolo": item['name'],
            "Ticker": item['symbol'],
            "Q.tà": item['shares'],
            "PMC": f"{item['pmc']:.2f}",
            "Prezzo Att.": f"{current_price:.2f}",
            "Investito": f"{invested:.2f} €",
            "Valore Att.": f"{market_value:.2f} €",
            "P&L %": f"{pl_percent:+.2f}%",
            "P&L Ass.": f"{pl_abs:+.2f} €"
        })
        
        total_market_value += market_value
        total_invested += invested

    # Visualizzazione Riepilogo in alto
    m1, m2, m3 = st.columns(3)
    m1.metric("Totale Investito", f"{total_invested:.2f} €")
    m2.metric("Valore Attuale", f"{total_market_value:.2f} €", f"{(total_market_value - total_invested):.2f} €")
    perf_tot = ((total_market_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
    m3.metric("Performance Totale", f"{perf_tot:.2f}%")

    # Tabella con i dati
    df_portfolio = pd.DataFrame(rows)
    st.table(df_portfolio.drop(columns=["ID"])) # Nascondiamo l'ID uuid
    
    # Tasti rimozione
    with st.expander("⚙️ Gestisci / Rimuovi posizioni"):
        for item in data:
            if st.button(f"Rimuovi {item['symbol']}", key=item['id']):
                delete_asset(item['id'])

else:
    st.info("Il portfolio è vuoto. Aggiungi il tuo primo titolo sopra.")
