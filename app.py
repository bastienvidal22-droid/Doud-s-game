import streamlit as st
import streamlit.components.v1 as components
import random
import requests
import time

st.set_page_config(page_title="Blind Test Cloud", page_icon="☁️", layout="centered")

# --- RECUPERATION DES SECRETS (Configuration Cloud) ---
try:
    BIN_ID = st.secrets["BIN_ID"]
    API_KEY = st.secrets["API_KEY"]
except:
    st.error("Erreur : Les secrets (BIN_ID et API_KEY) ne sont pas configurés sur Streamlit Cloud.")
    st.stop()

BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

# --- FONCTIONS CLOUD ---
def load_playlist():
    # Charge les données depuis JSONBin
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get("record", [])
    except:
        return []
    return []

def save_playlist(new_playlist):
    # Enregistre la playlist sur le cloud
    requests.put(BASE_URL, json=new_playlist, headers=HEADERS)

def extract_video_id(url):
    if not url: return None
    if "shorts/" in url: return url.split("shorts/")[1].split("?")[0]
    elif "youtu.be/" in url: return url.split("youtu.be/")[1].split("?")[0]
    elif "v=" in url: return url.split("v=")[1].split("&")[0]
    return None

# --- STATE ---
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'my_last_add' not in st.session_state:
    st.session_state.my_last_add = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("☁️ Zone Hôte")
    password = st.text_input("Mot de passe Admin", type="password")
    is_host = (password == "1234") # <--- Change ton mot de passe ici si tu veux
    
    if is_host:
        st.success("Connecté en tant que DJ !")
        if st.button("🗑️ RAZ Playlist (Urgence)"):
            save_playlist([])
            st.session_state.game_started = False
            st.rerun()

st.title("☁️ Blind Test Party")

# -------------------------------------------------------------
# NOUVELLE LOGIQUE DE COMPTAGE ICI (Correction du bug "1 titre")
# -------------------------------------------------------------
playlist_brut = load_playlist()

# Si ce n'est pas une liste (c'est le dict {"test": "ok"}), on corrige
if isinstance(playlist_brut, dict):
    playlist = []
    current_count = 0
    # On force la RAZ du Bin aussi pour que la prochaine lecture soit propre
    save_playlist([]) 
else:
    playlist = playlist_brut
    current_count = len(playlist)
# -------------------------------------------------------------


# === PHASE 1 : AJOUT ===
if not st.session_state.game_started:
    # Le st.info utilise maintenant le nouveau 'current_count'
    st.info(f"Playlist collaborative en ligne. Déjà {current_count} titres !") 
    
    with st.form("ajout"):
        c1, c2 = st.columns([1, 2])
        with c1: name = st.text_input("Prénom")
        with c2: link = st.text_input("Lien YouTube")
        
        if st.form_submit_button("Envoyer au Cloud 🚀"):
            if name and link and (vid := extract_video_id(link)):
                entry = {"user": name, "id": vid}
                
                # On utilise la variable 'playlist' nettoyée par la nouvelle logique
                playlist.append(entry)
                
                save_playlist(playlist)
                st.session_state.my_last_add = entry
                st.success("Sauvegardé !")
                time.sleep(1)
                st.rerun()

    if st.session_state.my_last_add:
        st.caption(f"Ton dernier ajout : {st.session_state.my_last_add['user']}")
        if st.button("Annuler mon dernier ajout"):
            full = load_playlist()
            last = st.session_state.my_last_add
            new_list = [x for x in full if not (x.get('id') == last['id'] and x.get('user') == last['user'])]
            save_playlist(new_list)
            st.session_state.my_last_add = None
            st.rerun()

    # Le bouton de lancement utilise len(playlist) qui est maintenant nettoyé
    if is_host and len(playlist) > 0:
        st.markdown("---")
        if st.button("🚀 LANCER LA SOIRÉE", type="primary"):
            st.session_state.shuffled_playlist = playlist.copy()
            random.shuffle(st.session_state.shuffled_playlist)
            st.session_state.game_started = True
            st.rerun()
            
    if st.button("🔄 Actualiser"):
        st.rerun()

# === PHASE 2 : JEU ===
else:
    if not is_host:
        st.warning("Regardez l'écran géant (Ordi de l'hôte) !")
    else:
        if st.session_state.current_index < len(st.session_state.shuffled_playlist):
            track = st.session_state.shuffled_playlist[st.session_state.current_index]
            st.metric("Piste", f"{st.session_state.current_index + 1} / {len(st.session_state.shuffled_playlist)}")

            embed_url = f"https://www.youtube.com/embed/{track['id']}?autoplay=1&controls=1&showinfo=0&rel=0"
            user_name = track['user']

            html_code = f"""
            <style>
                .wrapper {{ width: 100%; height: 350px; background: #000; border-radius: 15px; overflow: hidden; margin-bottom: 15px; }}
                iframe {{ width: 100%; height: 100%; border: 0; filter: blur(40px); transform: scale(1.1); transition
