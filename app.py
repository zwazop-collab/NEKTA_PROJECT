import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from psycopg2.extras import RealDictCursor

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="NEKTA | Excellence & Confiance", page_icon="🇭🇹", layout="wide")

# 2. CONNEXION SÉCURISÉE (NEON)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except Exception as e:
        return None

def run_query(query, params=None):
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        return pd.read_sql(query, conn, params=params)
    except: return pd.DataFrame()

def run_action(query, params=None):
    conn = get_db_connection()
    if not conn or conn.closed: st.cache_resource.clear(); conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        return True
    except: return False

# 3. DESIGN CSS (Luxurious & High-End)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .hero { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1454165833767-027ff81968d2?q=80&w=1350');
        background-size: cover; padding: 80px 40px; border-radius: 25px; color: white; text-align: center; margin-bottom: 25px;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; margin-bottom: 15px; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 4. INITIALISATION DES VARIABLES DE SESSION
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'user' not in st.session_state: st.session_state['user'] = None

# --- ÉCRAN DE CONNEXION ---
if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    with t1:
        with st.form("l"):
            e, p = st.text_input("Email"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                sql = "SELECT id, full_name, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                res = run_query(sql, (e, p, p))
                if not res.empty:
                    st.session_state.auth = True
                    st.session_state.user = res.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    with t2:
        with st.form("r"):
            fn, em, pw = st.text_input("Nom Complet"), st.text_input("Email"), st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                    st.success("Compte créé ! Connectez-vous.")
    st.stop()

# --- SI KONEKTE : NAVIGATION ---
with st.sidebar:
    # Sekirite : nou tcheke si 'user' la ekziste anvan nou afiche l
    if st.session_state.user:
        st.markdown(f"### 👤 {st.session_state.user['full_name']}")
        st.caption(f"{st.session_state.user['user_type']} | ID: {st.session_state.user['id']}")
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = st.radio("WORKSPACE", ["🏠 Accueil", "💎 Talents", "💼 Missions", "📥 Messagerie", "📊 BI Analytics", "🛡️ Administration"])

conn = get_db_connection()

if menu == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence et Confiance</h1><p>Algorithmes certifiés et traçabilité SQL.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    # Fonksyon métier SQL
    avg = run_query("SELECT fn_get_trust_average()").iloc[0,0]
    c1.metric("Confiance Globale", f"{avg:.1f}%")
    msg_count = run_query("SELECT fn_total_messages(%s)", (st.session_state.user['id'],)).iloc[0,0]
    c2.metric("Messages Reçus", msg_count)
    c3.metric("Status SGBD", "Connecté")

elif menu == "💎 Talents":
    st.title("💎 Réseau des Talents")
    search = st.text_input("🔍 Rechercher...")
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{search}%',))
    cols = st.columns(3)
    for i, r in df.iterrows():
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br>Score: {r['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Écrire / ⭐ Noter"):
                # Nou rale vrè ID moun nan pou aksyon yo
                target = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (r['full_name'],)).iloc[0,0]
                msg = st.text_area("Message", key=f"m_{target}")
                if st.button("Venvoyer", key=f"b_{target}"):
                    run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], target, msg))
                    st.success("Envoyé !")

elif menu == "💼 Missions":
    t1, t2, t3 = st.tabs(["📢 Offres", "👥 Candidats reçus", "➕ Publier"])
    with t1:
        st.dataframe(run_query("SELECT * FROM vw_jobs_ouverts LIMIT 50"), use_container_width=True)
        jid = st.number_input("ID du job pour postuler", min_value=1)
        if st.button("Postuler maintenant"):
            if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (int(jid), st.session_state.user['id'])):
                st.success("Postulé !")
            else: st.error("Déjà postulé ou erreur.")
    with t2:
        apps = run_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for _, r in apps.iterrows():
            st.write(f"**{r['full_name']}** -> {r['title']}")
            if st.button(f"Accepter {r['full_name']}", key=r['id']):
                run_action("CALL sp_accepter_candidature(%s)", (int(r['id']),)); st.rerun()
    with t3:
        with st.form("new_j"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Publier"):
                run_action("INSERT INTO jobs (client_id, title, budget, description) VALUES (%s, %s, %s, %s)", (st.session_state.user['id'], ti, bu, de))
                st.success("Publiée !")

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT u.full_name as de, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
    if msgs.empty: st.info("Aucun message.")
    for _, m in msgs.iterrows():
        st.markdown(f"<div class='card'><b>De: {m['de']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)

elif menu == "📊 BI Analytics":
    st.title("📊 Intelligence des Données")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.6))

elif menu == "🛡️ Administration":
    if st.session_state.user['role'] != 'ADMIN': st.error("Accès réservé.")
    else:
        st.title("🛡️ Contrôle DBA")
        search = st.text_input("🔍 Recherche rapide par ID ou Email")
        df_adm = run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100", (f'%{search}%', search))
        st.dataframe(df_adm, use_container_width=True)
        st.write("### 📜 Audit Logs (Trigger SQL)")
        st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 50"), use_container_width=True)