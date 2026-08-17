import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd
from datetime import datetime

# 1. CONFIGURATION & DESIGN
st.set_page_config(page_title="NEKTA | Excellence & Confiance", page_icon="🇭🇹", layout="wide")

DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except Exception as e:
        return None

def run_query(query, params=None, fetch="all"):
    conn = get_db_connection()
    if not conn: return [] if fetch == "all" else None
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch == "all": return cur.fetchall()
            return cur.fetchone()
    except: return [] if fetch == "all" else None

def run_action(query, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        return True
    except: return False

# --- STYLE CSS ---
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #000000 0%, #1e3a8a 100%) !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        .hero { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=1350'); 
                background-size: cover; padding: 80px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; }
        .card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3a8a; margin-bottom: 15px; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
if "auth_user" not in st.session_state: st.session_state.auth_user = None

if st.session_state.auth_user is None:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    
    with t1:
        with st.form("form_login"):
            email_log = st.text_input("Adresse Email", key="log_email")
            pass_log = st.text_input("Mot de passe", type="password", key="log_pass")
            if st.form_submit_button("Se connecter 🚀", use_container_width=True):
                # Chèk modpas pwofesyonèl (sipòte crypt() ak md5())
                u = run_query("SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s))", (email_log, pass_log, pass_log), fetch="one")
                if u:
                    st.session_state.auth_user = u
                    st.rerun()
                else: st.error("Email ou mot de passe incorrect.")

    with t2:
        with st.form("form_signup"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type de compte", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire ✨", use_container_width=True):
                # Inscription pwofesyonèl nan de tab yo
                success = run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut))
                if success:
                    new_u = run_query("SELECT id FROM users WHERE email = %s", (em,), fetch="one")
                    run_action("INSERT INTO profiles (user_id, bio, trust_score) VALUES (%s, %s, 50)", (new_u['id'], f"Profil professionnel de {fn}"))
                    st.success("🎉 Compte créé ! Veuillez vous connecter dans l'onglet Connexion.")
                else: st.error("L'email est déjà utilisé.")
    st.stop()

# --- NAVIGATION ---
user = st.session_state.auth_user
with st.sidebar:
    st.markdown(f"### 👤 {user['full_name']}")
    st.caption(f"{user['user_type']} | ID: {user['id']}")
    if st.button("Déconnexion 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "👥 Talents", "👤 Mon Profil", "💼 Missions", "📑 Candidatures", "💬 Messagerie", "📊 Statistiques"]
    if user['role'] == 'ADMIN': menu.append("⚙️ Administration DBA")
    choice = st.radio("Navigation", menu)

# --- PAGES ---
if choice == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence & Confiance</h1><p>Plateforme de mise en relation intelligente.</p></div>', unsafe_allow_html=True)
    st.subheader("🔔 Suivi de vos activités")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (user['id'],))
    if not notifs: st.info("Aucune activité récente.")
    else:
        for n in notifs:
            color = "green" if n['status'] == 'ACCEPTED' else "red" if n['status'] == 'REJECTED' else "orange"
            st.markdown(f"• Mission **{n['title']}** : <b style='color:{color}'>{n['status']}</b>", unsafe_allow_html=True)

elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    s = st.text_input("Rechercher un profil...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    cols = st.columns(3)
    for idx, t in enumerate(talents):
        tid = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (t['full_name'],), fetch="one")['id']
        with cols[idx % 3]:
            st.markdown(f"<div class='card'><b>{t['full_name']}</b><br>Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg = st.text_area("Message", key=f"m_{tid}")
                if st.button("Envoyer", key=f"b_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (user['id'], tid, msg)):
                        st.success("Envoyé !")

elif choice == "💼 Missions":
    t1, t2 = st.tabs(["📢 Offres Ouvertes", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for j in jobs:
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], user['id'])):
                        st.success("Candidature envoyée !")
                    else: st.error("Déjà postulé.")
    with t2:
        with st.form("pj"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Pousser l'offre"):
                if run_action("INSERT INTO jobs (client_id, title, budget, description) VALUES (%s, %s, %s, %s)", (user['id'], ti, bu, de)):
                    st.success("Mission publiée !"); st.rerun()

elif choice == "📑 Candidatures":
    t1, t2 = st.tabs(["Mes Candidatures", "Candidats reçus"])
    with t1:
        st.table(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (user['id'],)))
    with t2:
        reçus = run_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (user['id'],))
        for r in reçus:
            st.write(f"**{r['full_name']}** -> {r['title']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Accepter", key=f"acc_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if c2.button("Refuser", key=f"ref_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()

elif choice == "💬 Messagerie":
    st.title("💬 Boîte de réception")
    msgs = run_query("SELECT u.full_name, m.content, m.sender_id, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (user['id'],))
    for m in msgs:
        st.markdown(f"<div class='card'><b>De: {m['full_name']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)
        with st.expander("Répondre"):
            rep = st.text_area("Réponse", key=f"r_{m['sender_id']}_{m['sent_at']}")
            if st.button("Envoyer la réponse", key=f"br_{m['sender_id']}"):
                run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (user['id'], m['sender_id'], rep))
                st.success("Réponse envoyée !")

elif choice == "📊 Statistiques":
    st.title("📊 Intelligence des Données")
    df_u = pd.DataFrame(run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type"))
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Volume par Acteur"))

elif choice == "⚙️ Administration DBA":
    st.title("⚙️ Administration & Audit")
    ta1, ta2 = st.tabs(["Liste 100k", "Audit Logs"])
    with ta1:
        s = st.text_input("Chercher par Email")
        res = run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s LIMIT 100", (f'%{s}%',))
        st.dataframe(pd.DataFrame(res), use_container_width=True)
    with ta2:
        logs = run_query("SELECT * FROM vw_audit_trail LIMIT 100")
        st.dataframe(pd.DataFrame(logs), use_container_width=True)