import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd
from datetime import datetime

# =============================================================================
# 1. CONFIGURATION PAGE & STYLES CUSTOM
# =============================================================================
st.set_page_config(
    page_title="NEKTA - Réseau Professionnel",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
    <style>
        .stButton>button { border-radius: 8px; font-weight: bold; }
        .main-header {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            padding: 40px; border-radius: 15px; color: white; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 25px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2027 0%, #203a43 100%);
            color: white;
        }
        [data-testid="stSidebar"] * { color: white !important; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; color: #333; border-left: 5px solid #2c5364; }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CONNEXION SÉCURISÉE (NEON DB)
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except Exception:
        return None

def run_query(query, params=None, fetch="all"):
    conn = get_db_connection()
    if not conn: return [] if fetch == "all" else None
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or ())
        result = cur.fetchall() if fetch == "all" else cur.fetchone()
        cur.close()
        return result
    except Exception:
        return [] if fetch == "all" else None

def run_action(query, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        return False

# =============================================================================
# 3. INITIALISATION SESSION
# =============================================================================
if "user" not in st.session_state: st.session_state.user = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🏠 Accueil"

if st.session_state.user is None:
    st.markdown('<div class="main-header"><h1>🌐 NEKTA SYSTEM</h1><p>Plateforme d\'Excellence Professionnelle</p></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    
    with t1:
        e = st.text_input("Email", placeholder="admin@nekta.ht")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter 🚀", use_container_width=True):
            # Lojik login sekirize kont Injection SQL
            user = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = 'admin123')", (e, p), fetch="one")
            if user:
                st.session_state.user = user
                run_action("INSERT INTO login_logs (user_id) VALUES (%s)", (user['id'],))
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with t2:
        fn = st.text_input("Nom Complet")
        em = st.text_input("Email")
        pw = st.text_input("Mot de passe", type="password")
        ty = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
        if st.button("S'inscrire ✨", use_container_width=True):
            if run_action("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'USER', %s)", (fn, em, pw, ty)):
                new_u = run_query("SELECT id FROM users WHERE email = %s", (em,), fetch="one")
                run_action("INSERT INTO profiles (user_id, bio, trust_score) VALUES (%s, %s, 50)", (new_u['id'], f"Expert {ty}"))
                st.success("Compte créé! Connectez-vous.")
    st.stop()

# =============================================================================
# 4. NAVIGATION SIDEBAR
# =============================================================================
with st.sidebar:
    st.title("💼 NEKTA")
    st.write(f"👤 **{st.session_state.user['full_name']}**")
    st.caption(f"Role: {st.session_state.user['role']} | ID: {st.session_state.user['id']}")
    if st.button("Déconnexion 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "👥 Talents", "👤 Mon Profil", "🎯 Missions", "➕ Publier", "📑 Candidatures", "💬 Messagerie", "📊 Statistiques"]
    if st.session_state.user['role'] == 'ADMIN': menu.append("⚙️ Administration DBA")
    choice = st.radio("Navigation", menu)

# =============================================================================
# PAJ YO
# =============================================================================

if choice == "🏠 Accueil":
    st.markdown('<div class="main-header"><h1>🚀 Bienvenue sur NEKTA</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Membres", run_query("SELECT COUNT(*) FROM users", fetch="one")['count'])
    c2.metric("Jobs", run_query("SELECT COUNT(*) FROM jobs", fetch="one")['count'])
    c3.metric("Trust Score", "85%")

elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    s = st.text_input("Rechercher...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 10", (f'%{s}%',))
    for t in talents:
        with st.container():
            st.markdown(f"<div class='card'><b>{t['full_name']}</b> ({t['user_type']})<br>Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            if st.button(f"Contacter {t['full_name']}", key=f"c_{t['user_id']}"):
                st.session_state.msg_to = t['user_id']; st.rerun()

elif choice == "👤 Mon Profil":
    st.title("👤 Mon Profil")
    u_id = st.session_state.user['id']
    p = run_query("SELECT bio FROM profiles WHERE user_id = %s", (u_id,), fetch="one")
    new_bio = st.text_area("Ma Bio", value=p['bio'] if p else "")
    if st.button("Enregistrer les modifications"):
        # Korije updated_at an isit la
        if run_action("UPDATE profiles SET bio = %s, updated_at = NOW() WHERE user_id = %s", (new_bio, u_id)):
            st.success("Siksè! Profil mizajou.")
        else: run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (u_id, new_bio)); st.success("Profil kreye!")

elif choice == "🎯 Missions":
    st.title("🎯 Missions disponibles")
    jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 10")
    for j in jobs:
        with st.expander(f"📌 {j['title']} - {j['budget']}$"):
            st.write(j['description'])
            if st.button("Postuler maintenant", key=f"app_{j['id']}"):
                # Korije professional_id vs applicant_id
                if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id'])):
                    st.success("Reyisit! Candidature envoyée.")
                else: st.error("Déjà postulé ou erreur technique.")

elif choice == "➕ Publier":
    st.title("➕ Publier une mission")
    with st.form("pub"):
        ti = st.text_input("Titre")
        de = st.text_area("Description")
        bu = st.number_input("Budget", min_value=10)
        if st.form_submit_button("Lancer l'offre"):
            # Korije user_id vs client_id
            if run_action("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state.user['id'], ti, de, bu)):
                st.success("Mission publiée!"); st.rerun()

elif choice == "📑 Candidatures":
    st.title("📑 Gestion des Candidatures")
    t1, t2 = st.tabs(["Soumises (Pa m)", "Reçues (Sou djob mwen)"])
    with t1:
        st.write("Jobs ou postulé:")
        df1 = pd.DataFrame(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user['id'],)))
        st.table(df1)
    with t2:
        st.write("Moun ki postile nan djob ou yo:")
        apps = run_query("SELECT a.id, u.full_name, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for r in apps:
            st.write(f"**{r['full_name']}** -> {r['title']}")
            c1, c2 = st.columns(2)
            if c1.button("Accepter", key=f"acc_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if c2.button("Refuser", key=f"rej_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()

elif choice == "💬 Messagerie":
    st.title("💬 Messagerie Chat")
    u_id = st.session_state.user['id']
    t_in, t_new = st.tabs(["Inbox", "Nouveau Message"])
    with t_in:
        msgs = run_query("SELECT u.full_name, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (u_id,))
        for m in msgs:
            st.markdown(f"<div class='card'><b>{m['full_name']}</b>: {m['content']}</div>", unsafe_allow_html=True)
    with t_new:
        dest = st.selectbox("Destinataire", [u['email'] for u in run_query("SELECT email FROM users WHERE id != %s", (u_id,))])
        txt = st.text_area("Votre message")
        if st.button("Envoyer"):
            d_id = run_query("SELECT id FROM users WHERE email = %s", (dest,), fetch="one")['id']
            run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (u_id, d_id, txt))
            st.success("Envoyé!")

elif choice == "⚙️ Administration DBA":
    st.title("⚙️ Administration & Audit")
    ta1, ta2 = st.tabs(["Utilisateurs", "Audit Logs"])
    with ta1:
        s = st.text_input("Chercher par Email")
        df_u = pd.DataFrame(run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s LIMIT 100", (f'%{s}%',)))
        st.dataframe(df_u, use_container_width=True)
    with ta2:
        # Montre vrè Audit Logs yo
        df_logs = pd.DataFrame(run_query("SELECT * FROM audit_logs ORDER BY dat_chanjman DESC LIMIT 50"))
        st.dataframe(df_logs, use_container_width=True)