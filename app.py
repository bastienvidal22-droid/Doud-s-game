import streamlit as st
import streamlit.components.v1 as components
import random
import requests
import time

# Configuration de base
st.set_page_config(page_title="Doud's Game", page_icon="💿", layout="centered")

# --- CSS INJECTION (Amélioration Esthétique) ---
st.markdown("""
<style>
/* 1. Global Styling */
body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* 2. Customizing Containers */
.stAlert {
    border-radius: 12px;
    padding: 10px;
    font-size: 1.1em;
}

/* 3. Main Container Styling (for the whole page) */
div.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 750px;
}

/* 4. Customizing the Success Messages */
.stSuccess {
    background-color: #0b2e1d !important; 
    border-left: 5px solid #28a745 !important;
}

/* 5. Styling the Main Title */
h1 {
    text-align: center;
    color: #FF5733; /* Couleur thème */
    margin-bottom: 0.5rem;
    font-size: 2.5em;
    font-weight: 800;
}

/* 6. Info Box for Song Count */
.stMarkdown p {
    color: #E8E8E8;
}

</style>
""", unsafe_allow_html=True)


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
@st.cache_data(ttl=5) 
def load_playlist():
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        if response.status_code == 200:
            full_list = response.json().get("record", [])
            return [item for item in full_list if item.get('setup') != 'temp']
        else:
            st.error(f"Erreur de lecture Cloud (Code: {response.status_code}).")
            return []
    except Exception as e:
        st.error(f"Erreur de connexion au Cloud: {e}")
        return []
    return []

def save_playlist(new_playlist):
    response = requests.put(BASE_URL, json=new_playlist, headers=HEADERS)
    if response.status_code not in [200, 201, 204]:
        st.error(f"❌ ÉCHEC DE SAUVEGARDE (Code: {response.status_code}).")
        st.warning("Vérifiez la Master Key sur JSONBin.")
        return False
    return True

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

# --- SIDEBAR (CONTRÔLES ADMINISTRATEUR) ---
with st.sidebar:
    st.header("⚙️ Administrateur")
    password = st.text_input("Mot de passe Admin", type="password")
    is_host = (password == "0510") # Mot de passe Admin
    
    if is_host:
        st.success("Vous êtes administrateur")
        
        if st.button("🗑️ Réinitialiser la playlist"):
            success = save_playlist([]) 
            
            if success:
                st.cache_data.clear() 
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()
            else:
                pass 

st.title("💿 Doud's Game") 

# -------------------------------------------------------------
# LOGIQUE DE COMPTAGE 
# -------------------------------------------------------------
playlist_brut = load_playlist()

if isinstance(playlist_brut, dict):
    playlist = []
    current_count = 0
    save_playlist([{"setup": "temp"}]) 
else:
    playlist = playlist_brut
    current_count = len(playlist)
# -------------------------------------------------------------


# === PHASE 1 : AJOUT (ESTHÉTIQUE & UX) ===
if not st.session_state.game_started:
    
    # Boîte d'information centrale pour le compteur
    st.markdown(f"""
    <div style="text-align: center; background-color: #1E232A; padding: 15px; border-radius: 10px; margin-bottom: 25px;">
        <p style="font-size: 1.2em; font-weight: bold; color: #4CAF50;">
            Playlist collaborative en ligne. Déjà {current_count} titres !
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    
    # --- Formulaire ---
    with st.form("ajout", clear_on_submit=True): 
        
        st.markdown("### Ajouter votre Top Chansons :")
        
        # Inputs alignés
        col_name, col_link = st.columns([1, 2])
        with col_name: name = st.text_input("Prénom", key="name_input")
        with col_link: link = st.text_input("Lien YouTube", key="link_input") 
        
        # Bouton Submission centralisé
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.form_submit_button("Rajouter à la Playlist 🚀", use_container_width=True):
                vid = extract_video_id(link)
                
                if name and link and vid: 
                    entry = {"user": name, "id": vid, "link": link} 
                    playlist.append(entry)
                    st.cache_data.clear()
                    save_playlist(playlist)
                    st.session_state.my_last_add = entry
                    st.success("Titre ajouté avec succès !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Veuillez vérifier le prénom et le lien YouTube.")


    # --- Affichage du dernier ajout ---
    if st.session_state.my_last_add:
        st.markdown(f"""
        <div style="background-color: #0b2e1d; padding: 10px; border-radius: 8px; margin-top: 20px;">
            <p style="color: #cccccc; font-size: 0.9em; margin: 0;">
                ✅ Dernier ajout par **{st.session_state.my_last_add['user']}** : 
                <span style="font-size: 0.8em;">{st.session_state.my_last_add['link']}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
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
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🚀 LANCER LA SOIRÉE", type="primary", use_container_width=True):
                st.session_state.shuffled_playlist = playlist.copy()
                random.shuffle(st.session_state.shuffled_playlist)
                st.session_state.game_started = True
                st.rerun()

# === PHASE 2 : JEU (AMÉLIORATION VISUELLE) ===
else:
    if not is_host:
        st.warning("Regardez l'écran géant (Ordi de l'hôte) !")
    else:
        if 'shuffled_playlist' not in st.session_state:
             st.session_state.shuffled_playlist = playlist.copy()
             random.shuffle(st.session_state.shuffled_playlist)
             
        if st.session_state.current_index < len(st.session_state.shuffled_playlist):
            track = st.session_state.shuffled_playlist[st.session_state.current_index]
            
            st.markdown(f"## 🎶 Piste {st.session_state.current_index + 1} / {len(st.session_state.shuffled_playlist)}")

            embed_url = f"https://www.youtube.com/embed/{track['id']}?autoplay=1&controls=1&showinfo=0&rel=0"
            user_name = track['user']

            # Code HTML/JS pour le No-Cut (Fluidité maximale)
            html_code = f"""
            <style>
                .wrapper {{ width: 100%; height: 350px; background: #000; border-radius: 15px; overflow: hidden; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
                iframe {{ width: 100%; height: 100%; border: 0; filter: blur(40px); transform: scale(1.1); transition: filter 0.8s; }}
                .btn-game {{ 
                    background: #FF5733; color: white; border: none; 
                    padding: 10px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; margin: 5px; 
                    box-shadow: 0 3px 5px rgba(0,0,0,0.3); transition: background 0.3s;
                }}
                .btn-game:hover {{ background: #CC4422; }}
                #rep {{ text-align: center; font-size: 2em; font-weight: bold; color: #4CAF50; margin-top: 15px; opacity: 0; transition: opacity 1s; }}
            </style>
            <div class="wrapper"><iframe id="vid" src="{embed_url}" allow="autoplay; encrypted-media"></iframe></div>
            
            <div style="text-align:center;">
                <button class="btn-game" onclick="document.getElementById('vid').style.filter='blur(0px)'">👁️ TITRE</button>
                <button class="btn-game" onclick="document.getElementById('rep').style.opacity='1'">👤 QUI ?</button>
            </div>
            <div id="rep">C'est {track['user']} !</div>
            """
            components.html(html_code, height=550)

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
