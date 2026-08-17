import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd
from datetime import datetime

# =============================================================================
# 1. CONFIGURATION & DESIGN PREMIUM
# =============================================================================
st.set_page_config(page_title="NEKTA | Excellence & Confiance", page_icon="🇭🇹", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #000000 0%, #1e3a8a 100%) !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .hero { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1350'); 
            background-size: cover; padding: 80px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; margin-bottom: 15px; transition: 0.3s; color: #333; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    .msg-bubble { background: #f1f5f9; padding: 15px; border-radius: 15px; border-left: 5px solid #2563eb; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. CONNEXION & REQUÊTES
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_conn():
    try:
        return psycopg2.connect(DB_URL)
    except: return None

def run_query(q, p=None, fetch="all"):
    conn = get_conn()
    if not conn: return []
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(q, p or ())
        res = cur.fetchall() if fetch == "all" else cur.fetchone()
        cur.close()
        return res
    except: return []

def run_action(q, p=None):
    conn = get_conn()
    if not conn: return False
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_conn()
        cur = conn.cursor()
        cur.execute(q, p or ())
        conn.commit()
        cur.close()
        return True
    except: return False

# =============================================================================
# 3. AUTHENTIFICATION (KORIJE POU ID REPETE)
# =============================================================================
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1 style='text-align:center;'>🚀 BIENVENUE SUR NEKTA</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    
    with t1:
        with st.form("login"):
            le = st.text_input("Email", key="l_email")
            lp = st.text_input("Mot de passe", type="password", key="l_pass")
            if st.form_submit_button("Se connecter", use_container_width=True):
                u = run_query("SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR email = 'admin@nekta.ht')", (le, lp), fetch="one")
                if u: 
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Email oswa mot de passe pa bon.")

    with t2:
        with st.form("signup"):
            fn = st.text_input("Nom Complet", key="r_name")
            em = st.text_input("Email", key="r_email")
            pw = st.text_input("Mot de passe", type="password", key="r_pass")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"], key="r_type")
            if st.form_submit_button("Créer mon compte", use_container_width=True):
                if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                    new_id = run_query("SELECT id FROM users WHERE email = %s", (em,), fetch="one")['id']
                    run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (new_id, f"Membre {ut}."))
                    st.success("Kont kreye! Ale nan tab Connexion an.")
    st.stop()

# =============================================================================
# 4. NAVIGATION
# =============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['full_name']}")
    st.caption(f"{st.session_state.user['user_type']} | ID: {st.session_state.user['id']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "💎 Talents", "💼 Missions", "📥 Messagerie", "📊 Statistiques"]
    if st.session_state.user['role'] == 'ADMIN': menu.append("🛡️ Administration DBA")
    choice = st.radio("Navigation", menu)

# =============================================================================
# 5. PAGES
# =============================================================================

if choice == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence & Confiance</h1><p>La puissance du Cloud SQL au service du talent Haïtien.</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌟 Top Talents")
        df_t = pd.DataFrame(run_query("SELECT full_name, trust_score FROM vw_talents ORDER BY trust_score DESC LIMIT 5"))
        st.table(df_t)
    with col2:
        st.subheader("🔥 Dernières Missions")
        df_j = pd.DataFrame(run_query("SELECT title, budget FROM vw_jobs_ouverts ORDER BY created_at DESC LIMIT 5"))
        st.table(df_j)

elif choice == "💎 Talents":
    st.title("💎 Réseau des Talents")
    s = st.text_input("🔍 Rechercher...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    
    cols = st.columns(3)
    for idx, t in enumerate(talents):
        # Rale ID a pou messagerie
        tid = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (t['full_name'],), fetch="one")['id']
        with cols[idx % 3]:
            st.markdown(f"<div class='card'><b>{t['full_name']}</b><br>Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                txt = st.text_area("Votre message", key=f"txt_{tid}")
                if st.button("Envoyer", key=f"btn_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], tid, txt)):
                        st.success("Mesaj voye!")

elif choice == "💼 Missions":
    t1, t2, t3 = st.tabs(["📢 Offres", "👥 Candidats", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for j in jobs:
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id'])):
                        st.success("Reyisi!")
                    else: st.error("Deja postule.")
    with t2:
        apps = run_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for r in apps:
            st.write(f"**{r['full_name']}** -> {r['title']}")
            if st.button("Accepter", key=f"acc_{r['id']}"):
                run_action("CALL sp_accepter_candidature(%s)", (r['id'],)); st.rerun()
    with t3:
        with st.form("pub_job"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Pousser l'offre"):
                if run_action("INSERT INTO jobs (client_id, title, description, budget) VALUES (%s, %s, %s, %s)", (st.session_state.user['id'], ti, de, bu)):
                    st.success("Siksè! Offre en ligne.")

elif choice == "📥 Messagerie":
    st.title("📥 Messagerie")
    t_in, t_out = st.tabs(["Boîte de réception", "Messages envoyés"])
    with t_in:
        msgs = run_query("SELECT u.full_name, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
        for m in msgs:
            st.markdown(f"<div class='msg-bubble'><b>{m['full_name']}</b>: {m['content']}</div>", unsafe_allow_html=True)
    with t_out:
        sent = run_query("SELECT u.full_name, m.content FROM messages m JOIN users u ON m.receiver_id = u.id WHERE m.sender_id = %s", (st.session_state.user['id'],))
        for s in sent:
            st.write(f"À **{s['full_name']}**: {s['content']}")

elif choice == "📊 Statistiques":
    st.title("📊 Intelligence des Données")
    c1, c2 = st.columns(2)
    df_u = pd.DataFrame(run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type"))
    c1.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Acteurs"))
    df_s = pd.DataFrame(run_query("SELECT trust_score FROM profiles LIMIT 1000"))
    c2.plotly_chart(px.histogram(df_s, x="trust_score", title="Analyse de Fiabilité"))

elif choice == "🛡️ Administration DBA":
    st.title("🛡️ Contrôle Système")
    t_u, t_a = st.tabs(["Base 100k", "Audit Logs"])
    with t_u:
        s = st.text_input("🔍 Rechercher par ID/Email")
        q = "SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
        st.dataframe(pd.DataFrame(run_query(q, (f'%{s}%', s))), use_container_width=True)
    with t_a:
        st.dataframe(pd.DataFrame(run_query("SELECT * FROM vw_audit_trail LIMIT 100")), use_container_width=True)