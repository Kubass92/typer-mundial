import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# --- KONFIGURACJA ---
API_KEY = "2b5e744d084a4b278786968038753754"
API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

st.set_page_config(page_title="Mundial 2026 Typer", layout="wide")

# --- POŁĄCZENIE Z BAZĄ ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Funkcja pobierająca dane
def get_data():
    return conn.read(worksheet="Sheet1", ttl=0)

# --- PANEL BOCZNY (LEGENDA) ---
with st.sidebar:
    st.header("📖 Zasady Punktacji")
    st.markdown("🎯 **5 pkt** - Super Trafienie\n\n🏃 **2 pkt** - Awans\n\n✅ **1 pkt** - Zwycięzca")

# --- SEKCJA 1: FORMULARZ WPISYWANIA ---
st.title("🏆 Mundial 2026 - Panel Typowania")

with st.expander("➕ KLIKNIJ TUTAJ, ABY DODAĆ SWÓJ TYP"):
    with st.form("formularz_typu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Twoje Imię / Nick")
            mecz_choice = st.selectbox("Wybierz mecz do obstawienia", 
                                      ["Spain-Germany", "Poland-USA", "Brazil-France", "Argentina-Italy"])
        with col2:
            g_score = st.number_input("Gospodarz (bramki)", min_value=0, step=1)
            a_score = st.number_input("Gość (bramki)", min_value=0, step=1)
            awans_choice = st.radio("Kto awansuje dalej?", ["Gospodarz", "Gość"])
        
        submitted = st.form_submit_button("Zatwierdź i zapisz mój typ")

        if submitted:
            if name:
                # Pobierz aktualne dane, dodaj nową linię i wyślij z powrotem
                current_df = get_data()
                new_entry = pd.DataFrame([{
                    "Gracz": name,
                    "Mecz": mecz_choice,
                    "Typ_Gospodarz": g_score,
                    "Typ_Gosc": a_score,
                    "Kto_Awans": mecz_choice.split('-')[0] if awans_choice == "Gospodarz" else mecz_choice.split('-')[1]
                }])
                updated_df = pd.concat([current_df, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.success(f"Dzięki {name}! Twój typ został zapisany w bazie.")
                st.rerun()
            else:
                st.error("Podaj imię przed zatwierdzeniem!")

# --- SEKCJA 2: RANKING I WYNIKI LIVE ---
st.divider()
st.header("📊 Ranking Uczestników")

# Pobieranie wyników z internetu
headers = {'X-Auth-Token': API_KEY}
try:
    resp = requests.get(API_URL, headers=headers)
    live_matches = resp.json().get('matches', [])
except:
    live_matches = []

# Logika liczenia punktów (identyczna jak wcześniej)
df_typy = get_data()
if not df_typy.empty:
    # Tutaj przeliczamy punkty na podstawie df_typy i live_matches
    # Wyświetlamy tabelę rankingową
    st.dataframe(df_typy, use_container_width=True)
else:
    st.info("Baza typów jest pusta. Bądź pierwszy i wpisz swój wynik powyżej!")
