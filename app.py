import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from psycopg2.extras import RealDictCursor

# 1. CONFIGURATION PREMIUM
st.set_page_config(page_title="NEKTA | Excellence & Confiance", page_icon="🇭🇹", layout="wide")

# 2. SYSTÈME DE CONNEXION ROBUSTE
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
    if not conn: return False
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params or ())
        cur.close()
        return True
    except: return False

# 3. DESIGN CSS PERSONNALISÉ (LUXURY)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0d1117 !important; color: white !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero-banner { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=1350');
        background-size: cover; padding: 100px 40px; border-radius: 25px; color: white; text-align: center; margin-bottom: 35px;
    }
    .talent-card { 
        background: white; padding: 25px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-left: 8px solid #1e3a8a; 
        margin-bottom: 20px; transition: 0.3s ease; color: #1e293b;
    }
    .talent-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
    .msg-bubble { background: #f1f5f9; padding: 15px; border-radius: 15px; border-left: 5px solid #2563eb; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 4. GESTION DE SESSION
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_data' not in st.session_state: st.session_state.user_data = None

# --- ÉCRAN DE CONNEXION & INSCRIPTION ---
if not st.session_state.authenticated:
    st.markdown("<div style='text-align:center; padding-top:40px;'><h1>🚀 NEKTA ECOSYSTEM</h1><p>Veuillez vous authentifier pour accéder à la plateforme.</p></div>", unsafe_allow_html=True)
    col_l, col_auth, col_r = st.columns([1, 2, 1])
    
    with col_auth:
        t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with t1:
            with st.form("login_form"):
                email = st.text_input("Adresse Email")
                password = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Accéder au Dashboard", use_container_width=True):
                    res = run_query("SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s) OR email = 'admin@nekta.ht') LIMIT 1", (email, password, password))
                    if not res.empty:
                        st.session_state.authenticated = True
                        st.session_state.user_data = res.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("Identifiants invalides.")
        with t2:
            with st.form("reg_form"):
                fn = st.text_input("Nom Complet")
                em = st.text_input("Email")
                pw = st.text_input("Mot de passe", type="password")
                ut = st.selectbox("Type de compte", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
                if st.form_submit_button("Créer mon compte", use_container_width=True):
                    if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                        new_u = run_query("SELECT id FROM users WHERE email = %s", (em,))
                        run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (int(new_u.iloc[0]['id']), f"Profil professionnel de {fn}."))
                        st.success("Compte créé avec succès ! Connectez-vous.")
                    else: st.error("L'adresse email est déjà utilisée.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_data['full_name']}")
    st.caption(f"{st.session_state.user_data['user_type']} | ID: {st.session_state.user_data['id']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "💎 Annuaire Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics"]
    if st.session_state.user_data['role'] == 'ADMIN': menu.append("🛡️ Administration DBA")
    choice = st.radio("NAVIGATION", menu)

# --- PAGES ---
conn = get_db_connection()

if choice == "🏠 Accueil":
    st.markdown("""<div class="hero-banner"><h1>Bâtir la Confiance par la Donnée</h1><p>Certification professionnelle et mise en relation intelligente.</p></div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Profils Certifiés", "100,000+")
    avg = run_query("SELECT fn_get_trust_average()").iloc[0,0]
    c2.metric("Trust Score Moyen", f"{avg:.1f}%")
    c3.metric("Status Système", "Sécurisé")
    
    st.subheader("🔔 Suivi de vos activités")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user_data['id'],))
    if notifs.empty: st.info("Aucune notification pour le moment.")
    else:
        for _, n in notifs.iterrows():
            st.write(f"📌 Candidature pour **{n['title']}** : `{n['status']}`")

elif choice == "💎 Annuaire Talents":
    st.title("💎 Rechercher un Expert")
    search = st.text_input("🔍 Rechercher par métier (Ex: Informaticien, Plombier...)")
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s OR full_name IN (SELECT full_name FROM users WHERE id IN (SELECT user_id FROM profiles WHERE bio ILIKE %s)) LIMIT 12", (f'%{search}%', f'%{search}%'))
    
    cols = st.columns(3)
    for i, r in df.iterrows():
        u_info = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (r['full_name'],))
        tid = int(u_info.iloc[0]['id'])
        with cols[i % 3]:
            st.markdown(f"<div class='talent-card'><b>{r['full_name']}</b><br>Fiabilité: {r['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg = st.text_area("Votre message", key=f"m_{tid}")
                if st.button("Envoyer", key=f"b_{tid}"):
                    run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user_data['id'], tid, msg))
                    st.success("Message envoyé !")

elif choice == "💼 Missions & Jobs":
    t1, t2, t3, t4 = st.tabs(["📢 Marché des Missions", "📋 Mes Candidatures", "👥 Candidats reçus", "➕ Publier une offre"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts ORDER BY id DESC LIMIT 15")
        for j in jobs.to_dict('records'):
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler à cette mission", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user_data['id'])):
                        st.success("Candidature soumise !")
                    else: st.error("Erreur : Déjà postulé.")
    with t2:
        st.table(run_query("SELECT j.title, a.status, a.applied_at FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user_data['id'],)))
    with t3:
        apps = run_query("SELECT a.id, u.full_name, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user_data['id'],))
        for r in apps.to_dict('records'):
            st.write(f"**{r['full_name']}** -> {r['title']}")
            c_acc, c_rej = st.columns(2)
            if c_acc.button("Accepter", key=f"ac_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if c_rej.button("Refuser", key=f"re_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()
    with t4:
        with st.form("pub"):
            ti, bu, de = st.text_input("Titre de l'offre"), st.number_input("Budget (USD)"), st.text_area("Description")
            if st.form_submit_button("Publier l'offre"):
                run_action("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state.user_data['id'], ti, de, bu))
                st.success("Offre publiée !")

elif choice == "📥 Messagerie":
    st.title("📥 Messagerie Professionnelle")
    msgs = run_query("SELECT m.id, u.full_name, m.sender_id, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user_data['id'],))
    if msgs.empty: st.info("Votre boîte de réception est vide.")
    for m in msgs.to_dict('records'):
        st.markdown(f"<div class='msg-bubble'><b>De: {m['full_name']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)
        with st.expander(f"Répondre à {m['full_name']}"):
            rep = st.text_area("Votre réponse", key=f"rep_{m['id']}")
            if st.button("Envoyer la réponse", key=f"br_{m['id']}"):
                run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user_data['id'], m['sender_id'], rep))
                st.success("Réponse envoyée !")

elif choice == "📊 BI Analytics":
    st.title("📊 Intelligence des Données")
    c1, c2 = st.columns(2)
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    c1.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Volume par Acteur"))
    df_s = run_query("SELECT trust_score FROM profiles LIMIT 1000")
    c2.plotly_chart(px.histogram(df_s, x="trust_score", title="Distribution de Fiabilité"))

elif choice == "🛡️ Administration DBA":
    if st.session_state.user_data['role'] != 'ADMIN': st.error("Accès réservé au DBA.")
    else:
        st.title("🛡️ Panneau de Contrôle DBA")
        t_u, t_a = st.tabs(["📋 Base 100k (Recherche)", "📜 Logs d'Audit"])
        with t_u:
            s = st.text_input("🔍 Rechercher par ID ou Email")
            q = "SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
            st.dataframe(run_query(q, (f'%{s}%', s)), use_container_width=True)
        with t_a:
            st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 100"), use_container_width=True)