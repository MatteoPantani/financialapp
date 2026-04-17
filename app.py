import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- 1. CONFIGURAZIONE & CONNESSIONE ---
st.set_page_config(page_title="FinHub Portfolio Pro", layout="wide")

# Caricamento credenziali dai Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Errore nei Secrets di Streamlit. Verifica SUPABASE_URL e SUPABASE_KEY.")
    st.stop()

# Inizializzazione sessione utente
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
    except Exception:
        st.error("Email o password errati.")

def sign_up(email, password):
    try:
        supabase.auth.sign_up({"email": email, "password": password})
        st.info("Registrazione inviata. Se non riesci ad accedere subito, controlla se è richiesta la conferma via email.")
    except Exception as e:
        st.error(f"Errore: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- 3. FUNZIONI DATABASE ---
def load_portfolio():
    # La RLS su Supabase garantisce che l'utente veda solo i suoi dati
    res = supabase.table("watchlist").select("*").execute()
    return res.data

def add_to_portfolio(symbol, name, price, pmc, shares, asset_type):
    # CONTROLLO DUPLICATI: verifica se il ticker esiste già per questo utente
    existing = supabase.table("watchlist").select("*").eq("symbol", symbol).eq("user_id", st.session_state.user.id).execute()
    if existing.data:
        st.warning(f"⚠️ Il titolo {symbol} è già presente. Modificalo nella sezione apposita sotto.")
        return False
    
    data = {
        "symbol": symbol,
        "name": name,
        "price": float(price),
        "pmc": float(pmc),
        "shares": int(shares), # Forza unità intere
        "asset_type": asset_type,
        "user_id": st.session_state.user.id
    }
    supabase.table("watchlist").insert(data).execute()
    return True

def update_asset(id, new_pmc, new_shares):
    supabase.table("watchlist").update({
        "pmc": float(new_pmc), 
        "shares": int(new_shares)
    }).eq("id", id).execute()
    st.success("Dati aggiornati correttamente!")
    time.sleep(1)
    st.rerun()

def delete_asset(id):
    supabase.table("watchlist").delete().eq("id", id).execute()
    st.rerun()

# --- 4. LOGICA DI NAVIGAZIONE ---

# SCHERMATA LOGIN (Se l'utente non è loggato)
if st.session_state.user is None:
    st.title("🔐 FinHub Portfolio Login")
    col_auth, _ = st.columns([1, 1])
    with col_auth:
        tab1, tab2 = st.tabs(["Accedi", "Registrati"])
        with tab1:
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("Entra", type="primary", use_container_width=True):
                login(e, p)
        with tab2:
            e_r = st.text_input("Nuova Email")
            p_r = st.text_input("Nuova Password", type="password")
            if st.button("Crea Account", use_container_width=True):
                sign_up(e_r, p_r)
    st.stop() # Interrompe l'esecuzione qui per i non loggati

# --- AREA RISERVATA ---
st.sidebar.title(f"👤 {st.session_state.user.email.split('@')[0]}")
if st.sidebar.button("Logout"):
    logout()

st.title("💼 Il Tuo Portfolio Management")

# --- SEZIONE: AGGIUNTA TITOLI ---
with st.expander("🔍 Cerca e Aggiungi Titolo", expanded=True):
    ticker_input = st.text_input("Inserisci Ticker (es. AAPL, RACE.MI, SWDA.MI)").upper()
    
    if ticker_input:
        t = yf.Ticker(ticker_input)
        try:
            info = t.info
            if 'symbol' in info:
                name = info.get('longName') or info.get('shortName')
                curr_p = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                mkt_cap = info.get('marketCap', 0)
                open_p = info.get('open', 0)
                prev_close = info.get('previousClose', 0)

                st.markdown(f"### {name} ({info['symbol']})")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Prezzo Attuale", f"{curr_p} {info.get('currency', '')}")
                c2.metric("Cap. Mercato", f"{mkt_cap:,}")
                c3.metric("Apertura", f"{open_p}")
                c4.metric("Chiusura Prec.", f"{prev_close}")

                st.write("---")
                col_q, col_p, col_t, col_b = st.columns([1, 1, 1, 1])
                with col_q:
                    qta = st.number_input("Quantità (Interi)", min_value=1, step=1)
                with col_p:
                    pmc = st.number_input("Prezzo Medio Carico (PMC)", min_value=0.01, step=0.01)
                with col_t:
                    a_type = st.selectbox("Asset Type", ["Stock", "ETF", "Bond", "Crypto", "Commodity"])
                with col_b:
                    st.write("") # Spazio estetico
                    if st.button("💾 Salva Posizione", type="primary"):
                        if add_to_portfolio(info['symbol'], name, curr_p, pmc, qta, a_type):
                            st.success("Asset salvato!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.error("Ticker non trovato su Yahoo Finance.")
        except Exception:
            st.error("Errore nel recupero dati. Riprova tra poco.")

st.divider()

# --- SEZIONE: VISUALIZZAZIONE & RIEPILOGO ---
data = load_portfolio()

if data:
    df = pd.DataFrame(data)
    
    # Calcoli finanziari
    df['Investito'] = df['shares'] * df['pmc']
    df['Valore_Attuale'] = df['shares'] * df['price']
    df['P&L_Ass'] = df['Valore_Attuale'] - df['Investito']
    
    # Dashboard Metrics
    m1, m2, m3 = st.columns(3)
    tot_inv = df['Investito'].sum()
    tot_val = df['Valore_Attuale'].sum()
    tot_pl = tot_val - tot_inv
    m1.metric("Totale Investito", f"{tot_inv:,.2f} €")
    m2.metric("Valore Portafoglio", f"{tot_val:,.2f} €", f"{tot_pl:+.2f} €")
    perf = (tot_pl / tot_inv * 100) if tot_inv > 0 else 0
    m3.metric("Performance Totale", f"{perf:+.2f}%")

    st.subheader("📊 Dettaglio Posizioni")
    # Tabella formattata
    view_df = df[['asset_type', 'symbol', 'name', 'shares', 'pmc', 'price', 'P&L_Ass']].copy()
    view_df.columns = ['Tipo', 'Ticker', 'Nome', 'Quantità', 'PMC', 'Prezzo Att.', 'P&L (€)']
    st.dataframe(view_df, use_container_width=True, hide_index=True)

    # --- SEZIONE: MODIFICA & ELIMINA ---
    st.subheader("⚙️ Gestione Asset")
    with st.expander("Modifica o Rimuovi un Titolo esistente"):
        ticker_to_edit = st.selectbox("Seleziona titolo", df['symbol'].unique())
        if ticker_to_edit:
            row = df[df['symbol'] == ticker_to_edit].iloc[0]
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                new_q = st.number_input("Aggiorna Quantità", value=int(row['shares']), step=1)
            with col_e2:
                new_p = st.number_input("Aggiorna PMC", value=float(row['pmc']), step=0.01)
            with col_e3:
                st.write("Azioni")
                c_up, c_del = st.columns(2)
                if c_up.button("💾 Aggiorna", key="up_btn"):
                    update_asset(row['id'], new_p, new_q)
                if c_del.button("🗑️ Elimina", key="del_btn", type="secondary"):
                    delete_asset(row['id'])
else:
    st.info("Portfolio vuoto. Usa la barra di ricerca sopra per aggiungere il tuo primo investimento.")
