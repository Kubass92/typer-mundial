import streamlit as st
import pandas as pd
import requests

# --- 1. KONFIGURACJA (TUTAJ WKLEJ SWOJE LINKI) ---
# Pamiętaj: Link musi kończyć się na ?output=csv
SHEET_CSV_URL = "TU_WKLEJ_TWOJ_LINK_Z_GOOGLE_SHEETS_CSV" 
API_KEY = "2b5e744d084a4b278786968038753754"
API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

# --- 2. USTAWIENIA STRONY ---
st.set_page_config(page_title="Typer Mundial 2026", layout="wide")

# --- 3. LEGENDA W PANELU BOCZNYM ---
with st.sidebar:
    st.header("🏆 ZASADY PUNKTACJI")
    st.markdown("""
    ---
    🎯 **5 pkt** – **Super Trafienie**
    (Idealny wynik bramkowy)
    
    🏃 **2 pkt** – **Trafiony Awans**
    (Wskazanie kto przejdzie dalej)
    
    ✅ **1 pkt** – **Trafiony Zwycięzca**
    (Tylko kierunek: wygrana/remis)
    
    ---
    *Przykład: Typ 1:1 i awans Hiszpanii. Jeśli Hiszpania wygra w karnych po 1:1, dostajesz 7 pkt!*
    """)
    st.write("---")
    if st.button("🔄 Odśwież dane"):
        st.rerun()

# --- 4. FUNKCJE POBIERANIA ---
def pobierz_typy():
    try:
        # Dodajemy parametr, aby uniknąć buforowania danych przez Google
        url = f"{SHEET_CSV_URL}&cachebuster={pd.Timestamp.now().timestamp()}"
        df = pd.read_csv(url)
        return df
    except:
        return None

def pobierz_wyniki_api():
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(API_URL, headers=headers)
        return r.json().get('matches', [])
    except:
        return []

# --- 5. GŁÓWNA LOGIKA APLIKACJI ---
st.title("⚽ TYPER MUNDIAL 2026")

typy_df = pobierz_typy()
mecze_api = pobierz_wyniki_api()

if typy_df is None:
    st.error("❌ BŁĄD: Nie mogę odczytać Arkusza Google.")
    st.info("Upewnij się, że w Arkuszu kliknąłeś: Plik -> Udostępnij -> Opublikuj w internecie -> Format CSV.")
    st.stop()

if not mecze_api:
    st.warning("⚠️ Brak danych z API (lub przekroczono darmowy limit).")

# Mapowanie wyników z boisk
wyniki_dict = {}
for m in mecze_api:
    if m['status'] in ['FINISHED', 'IN_PLAY', 'TIMED']:
        home = m['homeTeam']['name']
        away = m['awayTeam']['name']
        # Pobieramy wyniki (jeśli mecz się nie zaczął, dajemy 0:0)
        h_score = m['score']['fullTime']['home'] if m['score']['fullTime']['home'] is not None else 0
        a_score = m['score']['fullTime']['away'] if m['score']['fullTime']['away'] is not None else 0
        
        # Kto awansował (ważne w fazie pucharowej)
        winner = None
        if m['score']['winner'] == 'HOME_TEAM': winner = home
        elif m['score']['winner'] == 'AWAY_TEAM': winner = away
        
        wyniki_dict[f"{home}-{away}"] = {
            "score": (h_score, a_score),
            "winner": winner,
            "status": m['status']
        }

# --- 6. OBLICZANIE RANKINGU ---
ranking = {}

for _, row in typy_df.iterrows():
    gracz = row['Gracz']
    mecz_id = row['Mecz'] # W arkuszu wpisuj np: Spain-Germany
    t_h = row['Typ_Gospodarz']
    t_a = row['Typ_Gosc']
    t_awans = row['Kto_Awans']

    if gracz not in ranking:
        ranking[gracz] = 0

    if mecz_id in wyniki_dict:
        real = wyniki_dict[mecz_id]
        r_h, r_a = real['score']
        
        # Punktacja
        if (t_h == r_h) and (t_a == r_a):
            ranking[gracz] += 5 # Super Trafienie
        elif (t_h - t_a) * (r_h - r_a) > 0 or (t_h == t_a and r_h == r_a):
            ranking[gracz] += 1 # Zwycięzca/Remis
            
        if str(t_awans).strip() == str(real['winner']).strip() and real['winner'] is not None:
            ranking[gracz] += 2 # Bonus Awans

# --- 7. WYŚWIETLANIE WYNIKÓW ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 RANKING")
    ranking_df = pd.DataFrame(list(ranking.items()), columns=['Uczestnik', 'Punkty'])
    ranking_df = ranking_df.sort_values(by='Punkty', ascending=False)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)

with col2:
    st.subheader("⚽ MECZE LIVE / WYNIKI")
    if wyniki_dict:
        for mecz, dane in wyniki_dict.items():
            st.write(f"**{mecz}** — `{dane['score'][0]}:{dane['score'][1]}`")
    else:
        st.write("Czekamy na pierwsze mecze...")