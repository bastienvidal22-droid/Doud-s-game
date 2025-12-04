import streamlit as st
import streamlit.components.v1 as components
import random
import requests
import time

st.set_page_config(page_title="Doud's Game", page_icon="💿", layout="centered")

# --- CSS INJECTION (Amélioration Esthétique) ---
st.markdown("""
<style>
/* NOUVEAU: FOND D'IMAGE */
/* Cible le conteneur principal de l'application pour le fond */
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1549490349-8643362247b5?fit=crop&w=1400&q=80"); 
    background-size: cover; 
    background-repeat: no-repeat; 
    background-attachment: fixed; 
}

/* Règle l'opacité du contenu principal pour que l'image de fond soit visible */
[data-testid="stHeader"] {
    background: rgba(0,0,0,0); /* Rend l'en-tête de Streamlit transparent */
}
.stApp {
    background: rgba(0,0,0,0.5); /* Optionnel: fonce légèrement le contenu */
}


/* 1. Customizing Containers */
.stAlert {
    border-radius: 12px;
    padding: 10px;
    font-size: 1.1em;
}

/* 2. Styling the Main Title */
h1 {
    text-align: center;
    color: #FF5733; /* Couleur thème */
    margin-bottom: 0.5rem;
    font-size: 2.5em;
    font-weight: 800;
}

/* 3. Main Container Styling (Espace pour l'icône CD) */
div.block-container {
    padding-top: 1.5rem; 
    padding-bottom: 2rem;
    max-width: 750px;
}

/* 4. Style for Registration Box */
.registration-box {
    background-color: #2A1E35; 
    padding: 20px; 
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
}

/* 5. Customizing the Success Messages */
.stSuccess {
    background-color: #0b2e1d !important; 
    border-left: 5px solid #28a745 !important;
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
            full_data = response.json().get("record", {})
            return [item for item in full_data.get("playlist_data", []) if item.get('setup') != 'temp']
        else:
            st.error(f"Erreur de lecture Cloud (Code: {response.status_code}).")
            return []
    except Exception as e:
        st.error(f"Erreur de connexion au Cloud: {e}")
        return []
    return []

def save_playlist(new_playlist):
    payload = {"playlist_data": new_playlist}
    response = requests.put(BASE_URL, json=payload, headers=HEADERS)
    
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
    st.session_session_state.current_index = 0
if 'my_last_add' not in st.session_state:
    st.session_state.my_last_add = None
if 'last_user_name' not in st.session_state:
    st.session_state.last_user_name = None
if 'registered_user_name' not in st.session_state:
    st.session_state.registered_user_name = None
if 'shuffled_playlist' not in st.session_state:
    st.session_state.shuffled_playlist = []

# --- SIDEBAR (CONTRÔLES ADMINISTRATEUR) ---
with st.sidebar:
    st.header("⚙️ Administrateur")
    password = st.text_input("Mot de passe Admin", type="password")
    is_host = (password == "0510") 
    
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
    save_playlist([]) 
else:
    playlist = playlist_brut
    current_count = len(playlist)
# -------------------------------------------------------------


# === PHASE 1 : AJOUT ===
if not st.session_state.game_started:
    
    # Boîte d'information centrale pour le compteur
    st.markdown(f"""
    <div style="text-align: center; background-color: #1E232A; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
        <p style="font-size: 1.2em; font-weight: bold; color: #FF5733; margin: 0;">
            Actuellement {current_count} titres dans la playlist
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- BLOC 1: ENREGISTREMENT DU NOM ---
    if st.session_state.registered_user_name is None:
        st.markdown("<div class='registration-box'>", unsafe_allow_html=True)
        st.markdown("### 1. Qui êtes-vous ?")
        
        with st.form("register_form"):
            user_name = st.text_input("Entrez votre prénom", key="reg_name_input")
            if st.form_submit_button("Confirmer mon identité"):
                if user_name:
                    st.session_state.registered_user_name = user_name
                    st.rerun()
                else:
                    st.warning("Veuillez entrer votre prénom.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # --- BLOC 2: SOUMISSION DES LIENS / LANCEMENT DU JEU ---
    else:
        user_name = st.session_state.registered_user_name
        
        st.markdown(f"### Bienvenue, **{user_name}** ! 👋")
        
        # Compteur individuel
        if user_name:
            my_count = len([t for t in playlist if t.get('user') == user_name])
            st.markdown(f"""
            <div style="text-align: center; background-color: #2A1E35; padding: 10px; border-radius: 8px; margin-bottom: 25px;">
                <p style="font-size: 1em; color: #ADD8E6; margin: 0;">
                    Vous avez ajouté **{my_count}** titre{'s' if my_count > 1 else ''} !
                </p>
            </div>
            """, unsafe_allow_html=True)


        # --- Formulaire d'ajout simplifié ---
        with st.form("ajout", clear_on_submit=True): 
            
            st.markdown("#### 2. Ajouter un lien YouTube :")
            link = st.text_input("Lien YouTube", key="link_input") 
            
            # Bouton Submission centralisé
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.form_submit_button("Rajouter à la Playlist 🚀", use_container_width=True):
                    vid = extract_video_id(link)
                    
                    if link and vid: 
                        entry = {"user": user_name, "id": vid, "link": link}
                        playlist.append(entry)
                        st.cache_data.clear()
                        save_playlist(playlist)
                        st.session_state.my_last_add = entry
                        st.session_state.last_user_name = user_name
                        st.success("Titre ajouté avec succès !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Veuillez entrer un lien YouTube valide.")


        # --- Affichage du dernier ajout ---
        if st.session_state.my_last_add:
            st.caption(f"✅ Dernier ajout : **{st.session_state.my_last_add['user']}** - {st.session_state.my_last_add['link']}")
            
            if st.button("Annuler mon dernier ajout"):
                full = load_playlist()
                last = st.session_state.my_last_add
                new_list = [x for x in full if not (x.get('id') == last['id'] and x.get('user') == last['user'])]
                st.cache_data.clear()
                save_playlist(new_list)
                st.session_state.my_last_add = None
                st.rerun()
                
        # --- Bouton de lancement ---
        if is_host and len(playlist) > 0:
            st.markdown("---")
            
            is_game_paused = (st.session_state.shuffled_playlist and st.session_state.current_index > 0)
            
            if is_game_paused:
                st.markdown("### Reprendre la Soirée")
                st.info(f"Une partie est en pause. Vous étiez à la piste **{st.session_state.current_index + 1}** sur **{len(st.session_state.shuffled_playlist)}**.")
                
                col_resume, col_restart = st.columns(2)
                
                with col_resume:
                    if st.button("▶️ REPRENDRE LA SOIRÉE", type="primary", use_container_width=True):
                        st.session_state.game_started = True
                        st.rerun()
                        
                with col_restart:
                    if st.button("🔄 RECOMMENCER DE 0", use_container_width=True):
                        st.session_state.current_index = 0
                        st.session_state.game_started = True
                        st.rerun()

            else:
                # Si la partie n'a jamais été commencée ou a été terminée
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    if st.button("🚀 LANCER LA SOIRÉE", type="primary", use_container_width=True):
                        st.session_state.shuffled_playlist = playlist.copy()
                        random.shuffle(st.session_state.shuffled_playlist)
                        st.session_state.game_started = True
                        st.session_state.current_index = 0
                        st.rerun()

# === PHASE 2 : JEU ===
else:
    if not is_host:
        st.warning("Regardez l'écran géant (Ordi de l'hôte) !")
    else:
        if 'shuffled_playlist' not in st.session_state:
             st.session_state.shuffled_playlist = playlist.copy()
             random.shuffle(st.session_state.shuffled_playlist)
             
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
                #rep {{ 
                    text-align: center; font-size: 2em; font-weight: bold; color: #4CAF50; 
                    margin-top: 15px; padding-bottom: 15px; 
                    opacity: 0; transition: opacity 1s; 
                }}
            </style>
            <div class="wrapper"><iframe id="vid" src="{embed_url}" allow="autoplay; encrypted-media"></iframe></div>
            <div style="text-align:center;">
                <button class="btn" onclick="document.getElementById('vid').style.filter='blur(0px)'">👁️ TITRE</button>
                <button class="btn" onclick="document.getElementById('rep').style.opacity='1'">👤 QUI ?</button>
            </div>
            <div id="rep" style="opacity: 0;">C'est {track['user']} !</div>
            """
            components.html(html_code, height=480)
            
            # --- Boutons Suivant et Revenir au menu ---
            col_back, col_next = st.columns([1, 2])
            
            with col_back:
                if st.button("⏪ REVENIR AU MENU", use_container_width=True):
                    st.session_state.game_started = False
                    st.rerun()

            with col_next:
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
