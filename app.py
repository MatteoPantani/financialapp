import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="FinHub Portfolio Pro", layout="wide")
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

if "user" not in st.session_state:
    st.session_state.user = None

# --- FUNZIONI AUTH (Semplificate per brevità) ---
def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- FUNZIONI DATABASE ---
def load_portfolio():
    res = supabase.table("watchlist").select("*").execute()
    return res.data

def add_to_portfolio(symbol, name, price, pmc, shares, asset_type):
    # CONTROLLO DUPLICATI
    existing = supabase.table("watchlist").select("*").eq("symbol", symbol).eq("user_id", st.session_state.user.id).execute()
    if existing.data:
        st.error(f"Errore: Il titolo {symbol} è già presente nel tuo portfolio. Usa la sezione 'Modifica' per cambiare quantità o PMC.")
        return False
    
    data = {
        "symbol": symbol, "name": name, "price": float(price),
        "pmc": float(pmc), "shares": int(shares), # Solo unità intere
        "asset_type": asset_type, "user_id": st.session_state.user.id
    }
    supabase.table("watchlist").insert(data).execute()
    return True

def update_asset(id, new_pmc, new_shares):
    supabase.table("watchlist").update({"pmc": new_pmc, "shares": int(new_shares)}).eq("id", id).execute()
    st.success("Dati aggiornati!")
    time.sleep(1)
    st.rerun()

def delete_asset(id):
    supabase.table("watchlist").delete().eq("id", id).execute()
    st.rerun()

# --- INTERFACCIA ---
if st.session_state.user is None:
    # (Inserire qui il blocco login già creato precedentemente)
    st.warning("Effettua il login per continuare")
    st.stop()

st.sidebar.title(f"👤 {st.session_state.user.email.split('@')[0]}")
if st.sidebar.button("Logout"): logout()

st.title("💼 Gestione Avanzata Portfolio")

# --- SEZIONE 1: RICERCA E AGGIUNTA ---
with st.expander("🔍 Cerca e Aggiungi Titolo", expanded=True):
    ticker_input = st.text_input("Inserisci Ticker (es. AAPL, SWDA.MI, BTC-USD)").upper()
    
    if ticker_input:
        t = yf.Ticker(ticker_input)
        info = t.info
        if 'symbol' in info:
            # Info Extra richieste
            name = info.get('longName', 'N/A')
            market_cap = info.get('marketCap', 0)
            open_p = info.get('open', 0)
            prev_close = info.get('previousClose', 0)
            curr_p = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            asset_type_yf = info.get('quoteType', 'N/A') # Es: EQUITY, ETF, etc.

            st.markdown(f"### {name}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Prezzo Attuale", f"{curr_p} {info.get('currency', '')}")
            c2.metric("Cap. Mercato", f"{market_cap:,}")
            c3.metric("Apertura", f"{open_p}")
            c4.metric("Chiusura Prec.", f"{prev_close}")

            st.write("---")
            col_q, col_p, col_t, col_b = st.columns([1, 1, 1, 1])
            with col_q:
                qta = st.number_input("Quantità (solo Interi)", min_value=1, step=1) # Vincolo unità intere
            with col_p:
                pmc = st.number_input("Prezzo Medio Carico", min_value=0.01)
            with col_t:
                a_type = st.selectbox("Tipologia Asset", ["Stock", "ETF", "Bond", "Crypto", "Commodity"])
            with col_b:
                st.write(" ")
                if st.button("💾 Salva nel Cloud", type="primary"):
                    if add_to_portfolio(info['symbol'], name, curr_p, pmc, qta, a_type):
                        st.success("Asset aggiunto!")
                        time.sleep(1)
                        st.rerun()
        else:
            st.error("Titolo non trovato.")

st.divider()

# --- SEZIONE 2: PORTFOLIO E MODIFICA ---
data = load_portfolio()
if data:
    df = pd.DataFrame(data)
    
    # Dashboard Riepilogativa (come prima)
    df['total_cost'] = df['shares'] * df['pmc']
    df['total_value'] = df['shares'] * df['price']
    
    st.subheader("📊 Il Tuo Patrimonio")
    st.dataframe(df[['asset_type', 'symbol', 'name', 'shares', 'pmc', 'price']], use_container_width=True)

    # SEZIONE MODIFICA
    st.subheader("⚙️ Modifica o Rimuovi Posizioni")
    selected_ticker = st.selectbox("Seleziona un titolo da modificare", df['symbol'].tolist())
    
    if selected_ticker:
        row = df[df['symbol'] == selected_ticker].iloc[0]
        col_edit1, col_edit2, col_edit3 = st.columns(3)
        
        with col_edit1:
            new_q = st.number_input("Nuova Quantità", value=int(row['shares']), step=1)
        with col_edit2:
            new_p = st.number_input("Nuovo PMC", value=float(row['pmc']), step=0.01)
        with col_edit3:
            st.write("Azioni")
            c_up, c_del = st.columns(2)
            if c_up.button("Aggiorna", use_container_width=True):
                update_asset(row['id'], new_p, new_q)
            if c_del.button("Elimina", type="secondary", use_container_width=True):
                delete_asset(row['id'])
else:
    st.info("Portfolio vuoto.")
