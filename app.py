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
        .card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3a8a; margin-bottom: 15px; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CONNEXION SÉCURISÉE (NEON DB)
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
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
    except Exception:
        return False

# =============================================================================
# 3. AUTHENTIFICATION
# =============================================================================
if "user" not in st.session_state: st.session_state.user = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🏠 Accueil"

if st.session_state.user is None:
    st.markdown('<div class="main-header"><h1>🌐 NEKTA SYSTEM</h1><p>Accès Sécurisé à la Plateforme</p></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    
    with t1:
        le = st.text_input("Adresse Email", key="login_e")
        lp = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter 🚀", use_container_width=True):
            user = run_query("SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = 'admin123' OR password_hash = md5(%s))", (le, lp, lp), fetch="one")
            if user:
                st.session_state.user = user
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with t2:
        fn = st.text_input("Nom Complet", key="reg_fn")
        em = st.text_input("Email", key="reg_em")
        pw = st.text_input("Mot de passe", type="password", key="reg_pw")
        ut = st.selectbox("Type de compte", ["STUDENT", "PROFESSIONAL", "BUSINESS"], key="reg_ut")
        if st.button("S'inscrire ✨", use_container_width=True):
            if run_action("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'USER', %s)", (fn, em, pw, ut)):
                st.success("Compte créé ! Connectez-vous.")
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
# 5. PAGES
# =============================================================================

if choice == "🏠 Accueil":
    st.markdown('<div class="main-header"><h1>🚀 Bienvenue sur NEKTA</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌟 Profils à la Une")
        top = run_query("SELECT full_name, trust_score FROM vw_talents ORDER BY trust_score DESC LIMIT 5")
        st.table(pd.DataFrame(top))
    with c2:
        st.subheader("🔥 Missions Récentes")
        jobs = run_query("SELECT title, budget FROM vw_jobs_ouverts LIMIT 5")
        st.table(pd.DataFrame(jobs))

elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    s = st.text_input("Rechercher un nom...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    cols = st.columns(3)
    for idx, t in enumerate(talents):
        # Rale ID pou messagerie
        tid = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (t['full_name'],), fetch="one")['id']
        with cols[idx % 3]:
            st.markdown(f"<div class='card'><b>{t['full_name']}</b><br>Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg_txt = st.text_area("Message", key=f"m_{tid}")
                if st.button("Envoyer", key=f"b_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], tid, msg_txt)):
                        st.success("Envoyé !")

elif choice == "👤 Mon Profil":
    st.title("👤 Mon Profil Personnel")
    uid = st.session_state.user['id']
    profile = run_query("SELECT bio, trust_score FROM profiles WHERE user_id = %s", (uid,), fetch="one")
    new_bio = st.text_area("Ma Biographie", value=profile['bio'] if profile else "")
    if st.button("Sauvegarder"):
        # Ranje erè updated_at la
        if run_action("UPDATE profiles SET bio = %s, updated_at = NOW() WHERE user_id = %s", (new_bio, uid)):
            st.success("Profil mis à jour avec succès !")
        else:
            run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (uid, new_bio))
            st.success("Profil créé !")

elif choice == "🎯 Missions":
    st.title("🎯 Missions et Emplois")
    jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
    for j in jobs:
        with st.expander(f"📌 {j['title']} - {j['budget']}$"):
            st.write(j['description'])
            # Ranje professional_id pou "Déjà postulé"
            if st.button("Postuler", key=f"ap_{j['id']}"):
                if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id'])):
                    st.success("Candidature réussie !")
                else: st.error("Vous avez déjà postulé ou erreur technique.")

elif choice == "➕ Publier":
    st.title("➕ Publier une nouvelle mission")
    with st.form("publish"):
        t = st.text_input("Titre de la mission")
        d = st.text_area("Description")
        b = st.number_input("Budget (USD)", min_value=10)
        if st.form_submit_button("Lancer l'appel d'offre"):
            # Ranje user_id -> client_id
            if run_action("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state.user['id'], t, d, b)):
                st.success("Mission publiée avec succès !"); st.rerun()

elif choice == "📑 Candidatures":
    st.title("📑 Suivi des Candidatures")
    t1, t2 = st.tabs(["Mes Candidatures (Envoyées)", "Candidats Reçus (Pour mes jobs)"])
    with t1:
        my_apps = run_query("SELECT j.title, a.status, a.applied_at FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user['id'],))
        st.dataframe(pd.DataFrame(my_apps), use_container_width=True)
    with t2:
        reçus = run_query("SELECT a.id, u.full_name, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for r in reçus:
            st.write(f"**{r['full_name']}** souhaite travailler sur : *{r['title']}*")
            c1, c2 = st.columns(2)
            if c1.button("Accepter", key=f"acc_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if c2.button("Refuser", key=f"rej_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()

elif choice == "💬 Messagerie":
    st.title("💬 Boîte de Messagerie")
    t_in, t_new = st.tabs(["Messages Reçus (Inbox)", "Nouveau Message"])
    with t_in:
        msgs = run_query("SELECT u.full_name, m.content, m.sender_id, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
        for m in msgs:
            with st.container():
                st.markdown(f"<div class='card'><b>{m['full_name']}</b>: {m['content']}</div>", unsafe_allow_html=True)
                with st.expander(f"Répondre à {m['full_name']}"):
                    rep = st.text_area("Votre réponse", key=f"rep_{m['sender_id']}_{m['sent_at']}")
                    if st.button("Envoyer la réponse", key=f"btn_rep_{m['sender_id']}"):
                        run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], m['sender_id'], rep))
                        st.success("Réponse envoyée !")
    with t_new:
        dest = st.selectbox("Destinataire", [u['email'] for u in run_query("SELECT email FROM users WHERE id != %s", (st.session_state.user['id'],))])
        txt = st.text_area("Message")
        if st.button("Envoyer le message"):
            rid = run_query("SELECT id FROM users WHERE email = %s", (dest,), fetch="one")['id']
            run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], rid, txt))
            st.success("Message envoyé !")

elif choice == "📊 Statistiques":
    st.title("📊 Analyses & Statistiques")
    df = pd.DataFrame(run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type"))
    st.plotly_chart(px.pie(df, values='n', names='user_type', hole=0.5, title="Répartition des Utilisateurs"))

elif choice == "⚙️ Administration DBA":
    st.title("⚙️ Administration & Audit Logs")
    ta1, ta2 = st.tabs(["Liste des 100k", "Audit Trail (Triggers)"])
    with ta1:
        s = st.text_input("Chercher un utilisateur (Email)")
        res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s LIMIT 100", (f'%{s}%',))
        st.dataframe(pd.DataFrame(res), use_container_width=True)
    with ta2:
        # Montre vrè Audit Logs ki soti nan Triggers yo
        logs = run_query("SELECT * FROM audit_logs ORDER BY dat_chanjman DESC LIMIT 100")
        st.dataframe(pd.DataFrame(logs), use_container_width=True)