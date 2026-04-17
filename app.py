import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- 1. CONFIGURAZIONE & CONNESSIONE ---
st.set_page_config(page_title="FinHub Portfolio Pro", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Inizializzazione sessione
if "user" not in st.session_state:
    st.session_state.user = None

# --- 2. FUNZIONI AUTH ---
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.success("Accesso eseguito!")
        time.sleep(1)
        st.rerun()
    except:
        st.error("Credenziali non valide.")

def sign_up(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.info("Controlla la mail per confermare (se abilitato) o prova a loggarti.")
    except Exception as e:
        st.error(f"Errore: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- 3. FUNZIONI DATABASE ---
def load_portfolio():
    # La RLS di Supabase filtrerà automaticamente per user_id
    res = supabase.table("watchlist").select("*").execute()
    return res.data

def add_to_portfolio(symbol, name, price, pmc, shares):
    data = {
        "symbol": symbol,
        "name": name,
        "price": float(price),
        "pmc": float(pmc),
        "shares": float(shares),
        "user_id": st.session_state.user.id
    }
    supabase.table("watchlist").insert(data).execute()

def delete_asset(id):
    supabase.table("watchlist").delete().eq("id", id).execute()
    st.rerun()

# --- 4. LOGICA DI NAVIGAZIONE ---

# CASO A: UTENTE NON LOGGATO
if st.session_state.user is None:
    st.title("🔐 FinHub Login")
    tab1, tab2 = st.tabs(["Accedi", "Registrati"])
    with tab1:
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Entra"):
            login(e, p)
    with tab2:
        e_r = st.text_input("Nuova Email")
        p_r = st.text_input("Nuova Password", type="password")
        if st.button("Crea Account"):
            sign_up(e_r, p_r)
    st.stop()

# CASO B: UTENTE LOGGATO
st.sidebar.title(f"👤 {st.session_state.user.email.split('@')[0]}")
if st.sidebar.button("Logout"):
    logout()

st.title("💼 Il Tuo Portfolio Management")

# --- SEZIONE 1: RICERCA E AGGIUNTA ---
with st.expander("🔍 Cerca e Aggiungi Titolo", expanded=True):
    col_s, col_q, col_p = st.columns([2, 1, 1])
    
    with col_s:
        ticker_input = st.text_input("Inserisci Ticker (es. AAPL, RACE.MI, BTC-USD)").upper()
    
    if ticker_input:
        t = yf.Ticker(ticker_input)
        try:
            info = t.info
            if 'symbol' in info:
                price_now = info.get('currentPrice') or info.get('regularMarketPrice')
                name = info.get('shortName')
                st.write(f"**Titolo trovato:** {name} | **Prezzo attuale:** {price_now} {info.get('currency', '')}")
                
                with col_q:
                    qta = st.number_input("Quantità", min_value=0.01, step=0.1)
                with col_p:
                    pmc = st.number_input("PMC (Prezzo d'acquisto)", min_value=0.01, step=0.01)
                
                if st.button("➕ Aggiungi al Portfolio", type="primary"):
                    add_to_portfolio(info['symbol'], name, price_now, pmc, qta)
                    st.success(f"{info['symbol']} aggiunto!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Ticker non trovato.")
        except:
            st.error("Errore nel recupero dati da Yahoo Finance.")

st.divider()

# --- SEZIONE 2: VISUALIZZAZIONE DATI ---
data = load_portfolio()

if data:
    df = pd.DataFrame(data)
    
    # Calcoli per il riepilogo
    df['invested'] = df['shares'] * df['pmc']
    df['current_value'] = df['shares'] * df['price']
    df['p_l_abs'] = df['current_value'] - df['invested']
    
    tot_inv = df['invested'].sum()
    tot_val = df['current_value'].sum()
    tot_pl = tot_val - tot_inv
    tot_perc = (tot_pl / tot_inv * 100) if tot_inv > 0 else 0

    # Dashboard Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Totale Investito", f"{tot_inv:.2f} €")
    m2.metric("Valore Attuale", f"{tot_val:.2f} €", f"{tot_pl:+.2f} €")
    m3.metric("Performance", f"{tot_perc:+.2f}%")

    # Tabella pulita
    st.subheader("📊 Dettaglio Posizioni")
    display_df = df[['symbol', 'name', 'shares', 'pmc', 'price', 'p_l_abs']].copy()
    display_df.columns = ['Ticker', 'Nome', 'Quantità', 'PMC', 'Prezzo Att.', 'P&L (€)']
    st.dataframe(display_df, use_container_width=True)

    # Rimozione
    with st.expander("🗑️ Elimina Posizioni"):
        for _, row in df.iterrows():
            if st.button(f"Elimina {row['symbol']}", key=row['id']):
                delete_asset(row['id'])
else:
    st.info("Il tuo portfolio è vuoto. Inizia cercando un titolo qui sopra.")
