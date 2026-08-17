import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd

# 1. CONFIGURATION & DESIGN PREMIUM
st.set_page_config(page_title="NEKTA | Excellence & Confiance", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        [data-testid="stSidebar"] { background: #000000 !important; color: #ffffff !important; }
        [data-testid="stSidebar"] * { color: #ffffff !important; font-weight: 600; }
        .hero { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=1350'); 
                background-size: cover; padding: 80px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px; }
        .card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3a8a; margin-bottom: 15px; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

# 2. SISTÈM KONEKSYON SEKIRIZE
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except: return None

def run_query(query, params=None, fetch="all"):
    conn = get_db_connection()
    if not conn: return []
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall() if fetch == "all" else cur.fetchone()
    except: return []

def run_action(query, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        return True
    except: return False

# 3. AUTHENTIFICATION BLINDÉE
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1 style='text-align:center;'>🛡️ NEKTA SECURE GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    with t1:
        with st.form("login_form"):
            e = st.text_input("Email", key="l_email")
            p = st.text_input("Mot de passe", type="password", key="l_pass")
            if st.form_submit_button("Se connecter", use_container_width=True):
                # REKÈT KORIJE : Retire "OR email = admin" pou fòse chèk modpas la
                sql = "SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                u = run_query(sql, (e, p, p), fetch="one")
                if u:
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Accès refusé : Identifiants incorrects.")
    with t2:
        with st.form("reg_form"):
            fn, em, pw = st.text_input("Nom Complet"), st.text_input("Email"), st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                    new_u = run_query("SELECT id FROM users WHERE email = %s", (em,), fetch="one")
                    run_action("INSERT INTO profiles (user_id, bio, trust_score) VALUES (%s, %s, 50)", (new_u['id'], f"Membre {ut}"))
                    st.success("Compte créé ! Connectez-vous.")
                else: st.error("Erreur technique ou email déjà utilisé.")
    st.stop()

# 4. NAVIGATION SIDEBAR
user = st.session_state.user
with st.sidebar:
    st.markdown(f"### 👤 {user['full_name']}")
    st.caption(f"{user['user_type']} | ID: {user['id']}")
    if st.sidebar.button("Déconnexion 🚪", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "👥 Talents", "👤 Mon Profil", "💼 Missions", "📑 Candidatures", "💬 Messagerie", "📊 Statistiques"]
    if user['role'] == 'ADMIN': menu.append("⚙️ Administration DBA")
    choice = st.radio("Navigation", menu)

# 5. PAGES
if choice == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence & Confiance</h1><p>Algorithmes sécurisés et traçabilité SQL totale.</p></div>', unsafe_allow_html=True)
    st.subheader("🔔 Notifications")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (user['id'],))
    if not notifs: st.info("Aucune notification.")
    for n in notifs:
        color = "green" if n['status'] == 'ACCEPTED' else "red" if n['status'] == 'REJECTED' else "orange"
        st.markdown(f"• Statut candidature **{n['title']}** : <b style='color:{color}'>{n['status']}</b>", unsafe_allow_html=True)

elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    s = st.text_input("🔍 Rechercher un expert...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    cols = st.columns(3)
    for idx, t in enumerate(talents):
        tid = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (t['full_name'],), fetch="one")['id']
        with cols[idx % 3]:
            st.markdown(f"<div class='card'><b>{t['full_name']}</b><br>Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander(f"✉️ Envoyer un message"):
                msg_text = st.text_area("Votre message", key=f"msg_area_{tid}")
                if st.button("Envoyer", key=f"send_btn_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (user['id'], tid, msg_text)):
                        st.success("Message envoyé !")

elif choice == "👤 Mon Profil":
    st.title("👤 Mon Profil")
    p = run_query("SELECT bio, trust_score FROM profiles WHERE user_id = %s", (user['id'],), fetch="one")
    new_bio = st.text_area("Ma Biographie", value=p['bio'] if p else "")
    if st.button("Sauvegarder"):
        run_action("UPDATE profiles SET bio = %s WHERE user_id = %s", (new_bio, user['id']))
        st.success("Profil mis à jour !")

elif choice == "💼 Missions":
    t1, t2, t3 = st.tabs(["📢 Offres Ouvertes", "➕ Publier", "📄 Mes Missions"])
    with t1:
        s_job = st.text_input("🔍 Rechercher...")
        jobs = run_query("SELECT * FROM vw_jobs_ouverts WHERE title ILIKE %s ORDER BY created_at DESC", (f'%{s_job}%',))
        for j in jobs:
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], user['id'])):
                        st.success("Candidature envoyée !")
    with t2:
        with st.form("pj"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Lancer l'offre"):
                run_action("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (user['id'], ti, bu, de))
                st.success("Mission publiée !"); st.rerun()
    with t3:
        my_jobs = run_query("SELECT id, title, budget FROM jobs WHERE client_id = %s", (user['id'],))
        for mj in my_jobs:
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{mj['title']}** ({mj['budget']}$)")
            if c2.button("🗑️ Supprimer", key=f"del_{mj['id']}"):
                run_action("DELETE FROM jobs WHERE id = %s", (mj['id'],))
                st.warning("Supprimé !"); st.rerun()

elif choice == "📑 Candidatures":
    t1, t2 = st.tabs(["Candidatures Envoyées", "Candidats Reçus"])
    with t1:
        st.table(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (user['id'],)))
    with t2:
        reçus = run_query("SELECT a.id, u.full_name, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (user['id'],))
        for r in reçus:
            st.write(f"**{r['full_name']}** -> {r['title']}")
            col_acc, col_ref = st.columns(2)
            if col_acc.button("✅ Accepter", key=f"acc_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if col_ref.button("❌ Refuser", key=f"ref_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()

elif choice == "💬 Messagerie":
    st.title("💬 Boîte de réception")
    msgs = run_query("SELECT u.full_name, m.content, m.sender_id, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (user['id'],))
    if not msgs: st.info("Aucun message reçu.")
    for m in msgs:
        with st.container():
            st.markdown(f"<div class='card'><b>De: {m['full_name']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)
            with st.expander("Répondre"):
                rep = st.text_area("Votre réponse", key=f"rep_{m['sender_id']}_{m['sent_at']}")
                if st.button("Envoyer", key=f"br_{m['sender_id']}"):
                    run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (user['id'], m['sender_id'], rep))
                    st.success("Réponse envoyée !")

elif choice == "📊 Statistiques":
    df_u = pd.DataFrame(run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type"))
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Volume par Acteur"))

elif choice == "⚙️ Administration DBA":
    st.title("⚙️ Contrôle DBA")
    s = st.text_input("Email utilisateur")
    res = run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s LIMIT 100", (f'%{s}%',))
    st.dataframe(pd.DataFrame(res), use_container_width=True)
    st.write("### Audit Logs")
    st.dataframe(pd.DataFrame(run_query("SELECT * FROM vw_audit_trail LIMIT 100")), use_container_width=True)