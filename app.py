import streamlit as st
import streamlit.components.v1 as components
import random
import requests
import time

st.set_page_config(page_title="Doud's Game", page_icon="💿", layout="centered")

# --- CSS INJECTION (Amélioration Esthétique) ---
st.markdown("""
<style>
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
    response = requests.put
