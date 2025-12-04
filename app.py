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

# --- FONCTIONS CLOUD (AVEC GESTION DU CACHE) ---
# On utilise st.cache_data pour éviter de surcharger l'API de JSONBin à chaque interaction
@st.cache_data(ttl=5) # Met les données en cache pour 5 secondes max
def load_playlist():
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

# --- SIDEBAR (MODIFIÉE POUR UN RESET TOTAL) ---
with st.sidebar:
    st.header("☁️ Zone Hôte")
    password = st.text_input("Mot de passe Admin", type="password")
    is_host = (password == "1234") 
    
    if is_host:
        st.success("Connecté en tant que DJ !")
        
        # LOGIQUE DE RESET AMÉLIORÉE (VIDAGE DU CACHE)
        if st.button("🗑️ RAZ Playlist (Urgence)"):
            save_playlist([]) 
            
            # Vider le cache de la fonction load_playlist()
            st.cache_data.clear() 
            
            # Vider TOUTES les variables de session et redémarrer
            for key in st.session_state.keys():
                del st.session_state[key]
                
            st.rerun()

st.title("☁️ Blind Test Party")

# -------------------------------------------------------------
# LOGIQUE DE COMPTAGE (Correction du bug "1 titre")
# -------------------------------------------------------------
playlist_brut = load_playlist()

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
    st.info(f"Playlist collaborative en ligne. Déjà {current_count} titres !") 
    
    # On utilise clear_on_submit=True
    with st.form("ajout", clear_on_submit=True): 
        c1, c2 = st.columns([1, 2])
        
        # Le prénom n'est plus pré-rempli pour des raisons de session
        with c1: name = st.text_input("Prénom", key="name_input")
        
        # Le lien sera effacé automatiquement
        with c2: link = st.text_input("Lien YouTube", key="link_input") 
        
        if st.form_submit_button("Rajouter à la Playlist 🚀"):
            if name and link and (vid := extract_video_id(link)):
                
                # On sauvegarde le nom ET le lien pour l'affichage de confirmation
                entry = {"user": name, "id": vid, "link": link} 
                playlist.append(entry)
                
                # Vider le cache avant l'écriture pour garantir une lecture fraîche au prochain load
                st.cache_data.clear()
                
                save_playlist(playlist)
                st.session_state.my_last_add = entry
                st.success("Sauvegardé !")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Remplissez les deux champs avec un lien YouTube valide.")

    if st.session_state.my_last_add:
        st.caption(f"Ton dernier ajout par {st.session_state.my_last_add['user']} : **{st.session_state.my_last_add['link']}**")
        
        if st.button("Annuler mon dernier ajout"):
            full = load_playlist()
            last = st.session_state.my_last_add
            new_list = [x for x in full if not (x.get('id') == last['id'] and x.get('user') == last['user'])]
            
            st.cache_data.clear()
            save_playlist(new_list)
            st.session_state.my_last_add = None
            st.rerun()

    if is_host and len(playlist) > 0:
        st.markdown("---")
        if st.button("🚀 LANCER LA SOIRÉE", type="primary"):
            st.session_state.shuffled_playlist = playlist.copy()
            random.shuffle(st.session_state.shuffled_playlist)
            st.session_state.game_started = True
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

            # Code HTML/JS pour le No-Cut (Fluidité maximale)
            html_code = f"""
            <style>
                .wrapper {{ width: 100%; height: 350px; background: #000; border-radius: 15px; overflow: hidden; margin-bottom: 15px; }}
                iframe {{ width: 100%; height: 100%; border: 0; filter: blur(40px); transform: scale(1.1); transition: filter 0.8s; }}
                .btn {{ background: #333; color: white; border: 1px solid #555; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; }}
                .btn:hover {{ background: #444; }}
                #rep {{ opacity: 0; color: #4CAF50; font-size: 20px; font-weight: bold; text-align: center; transition: opacity 1s; margin-top: 10px; }}
            </style>
            <div class="wrapper"><iframe id="vid" src="{embed_url}" allow="autoplay; encrypted-media"></iframe></div>
            <div style="text-align:center;">
                <button class="btn" onclick="document.getElementById('vid').style.filter='blur(0px)'">👁️ TITRE</button>
                <button class="btn" onclick="document.getElementById('rep').style.opacity='1'">👤 QUI ?</button>
            </div>
            <div id="rep">C'est {track['user']} !</div>
            """
            components.html(html_code, height=500)

            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("⏭️ SUIVANT", type="primary", use_container_width=True):
                    st.session_state.current_index += 1
                    st.rerun()
        else:
            st.balloons()
            st.success("Playlist terminée !")
            if st.button("Recommencer"):
                st.session_state.game_started = False
                st.session_state.current_index = 0
                st.rerun()
