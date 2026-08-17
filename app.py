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
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; margin-bottom: 15px; color: #333; }
    .msg-bubble { background: #f1f5f9; padding: 15px; border-radius: 10px; border-left: 5px solid #1e3a8a; margin-bottom: 10px; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. CONNEXION SÉCURISÉE (NEON)
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_conn():
    try:
        return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    except: return None

def run_query(q, p=None):
    conn = get_conn()
    if not conn: return pd.DataFrame()
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_conn()
        return pd.read_sql(q, conn, params=p)
    except: return pd.DataFrame()

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
# 3. AUTHENTIFICATION
# =============================================================================
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1 style='text-align:center;'>🚀 BIENVENUE SUR NEKTA</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    
    with t1:
        with st.form("login_form"):
            le = st.text_input("Email", key="login_email")
            lp = st.text_input("Mot de passe", type="password", key="login_pass")
            if st.form_submit_button("Se connecter", use_container_width=True):
                # Sekirite : chèk modpas haché oswa kont admin
                u = run_query("SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR email = 'admin@nekta.ht')", (le, lp))
                if not u.empty:
                    st.session_state.user = u.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Email oswa modpas pa bon.")

    with t2:
        with st.form("signup_form"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("Créer mon compte", use_container_width=True):
                if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                    new_u = run_query("SELECT id FROM users WHERE email = %s", (em,))
                    run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (int(new_u.iloc[0]['id']), f"Expert {ut} disponible."))
                    st.success("Kont kreye! Ale nan tab Connexion an.")
                else: st.error("Email sa a deja itilize.")
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
    st.markdown('<div class="hero"><h1>NEKTA : Excellence & Confiance</h1><p>Gérez votre réputation et vos opportunités.</p></div>', unsafe_allow_html=True)
    
    # Seksyon Notifikasyon (Suivi kandidati)
    st.subheader("🔔 Suivi de mes candidatures")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user['id'],))
    if notifs.empty: st.info("Aucune candidature en cours.")
    else:
        for _, n in notifs.iterrows():
            color = "green" if n['status'] == 'ACCEPTED' else "red" if n['status'] == 'REJECTED' else "orange"
            st.markdown(f"• Misyon **{n['title']}** : <b style='color:{color}'>{n['status']}</b>", unsafe_allow_html=True)
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌟 Top Talents")
        st.table(run_query("SELECT full_name, trust_score FROM vw_talents ORDER BY trust_score DESC LIMIT 5"))
    with c2:
        st.subheader("🔥 Dernières Missions")
        st.table(run_query("SELECT title, budget FROM vw_jobs_ouverts ORDER BY created_at DESC LIMIT 5"))

elif choice == "💎 Talents":
    st.title("💎 Annuaire des Talents")
    s = st.text_input("🔍 Rechercher par métier ou nom...")
    talents = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    
    cols = st.columns(3)
    for idx, t in enumerate(talents.to_dict('records')):
        # Rale vrè ID a nan baz la pou nou ka kontakte moun nan
        u_info = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (t['full_name'],))
        tid = int(u_info.iloc[0]['id'])
        with cols[idx % 3]:
            st.markdown(f"<div class='card'><b>{t['full_name']}</b><br>Trust Score: {t['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg_txt = st.text_area("Tapez votre message", key=f"msg_{tid}")
                if st.button("Envoyer", key=f"btn_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], tid, msg_txt)):
                        st.success("Mesaj voye!")

elif choice == "💼 Missions":
    t1, t2, t3 = st.tabs(["📢 Offres", "👥 Candidats reçus", "➕ Publier"])
    
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for j in jobs.to_dict('records'):
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id'])):
                        st.success("Candidature envoyée!")
                    else: st.error("Erreur ou déjà postulé.")
                    
    with t2:
        st.subheader("Gérez les candidats")
        apps = run_query("SELECT a.id, u.full_name, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        if apps.empty: st.info("Aucun candidat en attente.")
        else:
            for r in apps.to_dict('records'):
                st.write(f"**{r['full_name']}** -> {r['title']}")
                ca, cr = st.columns(2)
                if ca.button("✅ Accepter", key=f"acc_{r['id']}"):
                    run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
                if cr.button("❌ Refuser", key=f"ref_{r['id']}"):
                    run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()
                    
    with t3:
        with st.form("pub_job"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Pousser l'offre"):
                if run_action("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state.user['id'], ti, de, bu)):
                    st.success("Offre publiée!"); st.rerun()

elif choice == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT m.id, u.full_name, m.sender_id, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
    if msgs.empty: st.info("Aucun message reçu.")
    else:
        for m in msgs.to_dict('records'):
            st.markdown(f"<div class='msg-bubble'><b>De: {m['full_name']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)
            with st.expander("Répondre"):
                rep = st.text_area("Votre réponse", key=f"rep_{m['id']}")
                if st.button("Envoyer la réponse", key=f"br_{m['id']}"):
                    run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], m['sender_id'], rep))
                    st.success("Réponse envoyée!")

elif choice == "📊 Statistiques":
    st.title("📊 Intelligence des Données")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    if not df_u.empty: st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Volume par Acteur"))
    df_s = run_query("SELECT trust_score FROM profiles LIMIT 1000")
    if not df_s.empty: st.plotly_chart(px.histogram(df_s, x="trust_score", title="Distribution de Fiabilité"))

elif choice == "🛡️ Administration DBA":
    st.title("🛡️ Contrôle Système")
    t_u, t_a = st.tabs(["📋 Base 100k", "📜 Audit Logs"])
    with t_u:
        s = st.text_input("🔍 Rechercher par ID ou Email")
        q = "SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
        st.dataframe(run_query(q, (f'%{s}%', s)), use_container_width=True)
    with t_a:
        st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 100"), use_container_width=True)