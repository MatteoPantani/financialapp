import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="FinHub Auth Portfolio", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- GESTIONE SESSIONE ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- FUNZIONI AUTH ---
def sign_up(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        st.success("Registrazione effettuata! Ora puoi accedere.")
    except Exception as e:
        st.error(f"Errore registrazione: {e}")

def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.rerun()
    except Exception as e:
        st.error("Email o password errati.")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# --- INTERFACCIA AUTH ---
if st.session_state.user is None:
    st.title("🔐 Benvenuto in FinHub")
    tab1, tab2 = st.tabs(["Login", "Registrazione"])
    
    with tab1:
        email_log = st.text_input("Email", key="log_email")
        pass_log = st.text_input("Password", type="password", key="log_pass")
        if st.button("Accedi"):
            login(email_log, pass_log)
            
    with tab2:
        email_reg = st.text_input("Email", key="reg_email")
        pass_reg = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Registrati"):
            sign_up(email_reg, pass_reg)
    st.stop() # Blocca l'app qui se non loggato

# --- SE SIAMO QUI, L'UTENTE È LOGGATO ---
st.sidebar.write(f"Logged as: {st.session_state.user.email}")
if st.sidebar.button("Esci"):
    logout()

# --- FUNZIONI DB AGGIORNATE (Senza user_id manuale, Supabase lo prende dall'auth) ---
def add_to_db(symbol, name, price, pmc, shares):
    try:
        data = {
            "symbol": symbol,
            "name": name,
            "price": price,
            "pmc": pmc,
            "shares": shares,
            "user_id": st.session_state.user.id  # Colleghiamo l'utente
        }
        supabase.table("watchlist").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def load_db():
    # Grazie alla RLS, questa query restituirà solo i dati dell'utente loggato
    res = supabase.table("watchlist").select("*").execute()
    return res.data

# --- APP PORTFOLIO (Stessa logica di prima) ---
st.title(f"💼 Portfolio di {st.session_state.user.email.split('@')[0]}")

# ... (Qui inserisci la parte di ricerca yfinance e la tabella che abbiamo scritto nel messaggio precedente)
# Ricordati solo di usare add_to_db() e load_db() aggiornate!

data = load_db()
if data:
    df = pd.DataFrame(data)
    st.dataframe(df[["symbol", "name", "shares", "pmc", "price"]])
else:
    st.info("Il tuo portfolio personale è vuoto.")
