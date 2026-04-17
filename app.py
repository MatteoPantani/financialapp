# --- FUNZIONI DATABASE AGGIORNATE ---
def add_to_watchlist(symbol, name, price):
    try:
        data = {
            "symbol": str(symbol), 
            "name": str(name), 
            "price": float(price)
        }
        # Tentativo di inserimento
        result = supabase.table("watchlist").insert(data).execute()
        
        # Verifichiamo se l'inserimento è andato a buon fine
        if len(result.data) > 0:
            st.toast(f"✅ {symbol} salvato correttamente!", icon="⭐")
            return True
        else:
            st.error("Errore: Il database non ha restituito dati dopo l'inserimento.")
            return False
    except Exception as e:
        st.error(f"❌ Errore durante il salvataggio: {str(e)}")
        return False

# --- NEL CORPO DELL'APP (Dove c'è il pulsante) ---
if col_a.button("⭐ Salva nel Cloud"):
    successo = add_to_watchlist(info['symbol'], info.get('shortName'), curr_price)
    if successo:
        # Importante: Aspetta un attimo prima di ricaricare per mostrare il toast
        import time
        time.sleep(1)
        st.rerun()
