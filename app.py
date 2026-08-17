import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd

# 1. CONFIGURATION
st.set_page_config(page_title="NEKTA | Hub Professionnel", page_icon="🇭🇹", layout="wide")

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

# --- STYLE ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .hero { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1350'); 
            background-size: cover; padding: 80px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;}
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; margin-bottom: 10px; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN & SIGNUP ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    
    with t1:
        with st.form("login"):
            e = st.text_input("Email", key="l_email")
            p = st.text_input("Mot de passe", type="password", key="l_pass")
            if st.form_submit_button("Se connecter"):
                # Nou tcheke modpas la ak tout fòma posib (crypt, md5) pou sekirite
                sql = "SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s) OR password_hash = %s) LIMIT 1"
                res = run_query(sql, (e, p, p, p))
                if not res.empty:
                    st.session_state.update({'auth':True, 'user':res.iloc[0].to_dict()})
                    st.rerun()
                else: st.error("Email oswa modpas pa bon. Tcheke si ou kouri SQL la nan Neon.")
                
    with t2:
        with st.form("signup"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("Créer mon compte"):
                conn = get_conn(); cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'UTILISATEUR', %s) RETURNING id", (fn, em, pw, ut))
                    new_id = cur.fetchone()['id']
                    cur.execute("INSERT INTO profiles (user_id, bio, trust_score) VALUES (%s, %s, 50)", (new_id, f"Profil de {fn}"))
                    conn.commit()
                    st.success("Kont kreye ak siksè! Kounye a, ale nan tab Connexion an.")
                except Exception as ex:
                    conn.rollback()
                    st.error(f"Erè: Email sa a genlè deja nan sistèm nan. ({ex})")
    st.stop()

# --- APP ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['full_name']}")
    st.caption(f"{st.session_state.user['user_type']} | ID: {st.session_state.user['id']}")
    if st.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 Statistiques"]
    if st.session_state.user['role'] == 'ADMIN': menu.append("🛡️ Administration DBA")
    choice = st.radio("Navigation", menu)

conn = get_conn()

if choice == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Bienvenue sur NEKTA</h1><p>Gérez vos candidatures et messages en temps réel.</p></div>', unsafe_allow_html=True)
    st.subheader("🔔 Suivi de mes candidatures")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user['id'],))
    if notifs.empty: st.write("Ou poko gen okenn kandidati.")
    else:
        for _, n in notifs.iterrows():
            color = "green" if n['status'] == 'ACCEPTED' else "red" if n['status'] == 'REJECTED' else "orange"
            st.markdown(f"• Misyon **{n['title']}** : <b style='color:{color}'>{n['status']}</b>", unsafe_allow_html=True)

elif choice == "💎 Talents":
    st.title("💎 Annuaire des Talents")
    s = st.text_input("Rechercher...")
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    cols = st.columns(3)
    for i, r in df.iterrows():
        u_info = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (r['full_name'],))
        tid = int(u_info.iloc[0]['id'])
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br>Score: {r['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg_txt = st.text_area("Message", key=f"m_{tid}")
                if st.button("Envoyer", key=f"b_{tid}"):
                    cur = conn.cursor()
                    cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], tid, msg_txt))
                    conn.commit(); st.success("Mesaj voye!")

elif choice == "💼 Missions & Jobs":
    t1, t2, t3 = st.tabs(["📢 Offres", "👥 Candidats reçus", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for j in jobs.to_dict('records'):
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id']))
                        conn.commit(); st.success("Candidature envoyée!")
                    except: conn.rollback(); st.error("Déjà postulé.")
    with t2:
        st.subheader("Gérez vos postulants")
        apps = run_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for r in apps.to_dict('records'):
            st.write(f"**{r['full_name']}** -> {r['title']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Accepter", key=f"acc_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
            if c2.button("❌ Refuser", key=f"ref_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
    with t3:
        with st.form("pj"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Publier"):
                cur = conn.cursor()
                cur.execute("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state.user['id'], ti, de, bu))
                conn.commit(); st.success("Offre publiée!")

elif choice == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT m.id, u.full_name, m.sender_id, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
    if msgs.empty: st.info("Aucun message.")
    else:
        for m in msgs.to_dict('records'):
            st.markdown(f"<div class='card'><b>De: {m['full_name']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)
            with st.expander("Répondre"):
                rep = st.text_area("Votre réponse", key=f"rep_{m['id']}")
                if st.button("Envoyer", key=f"br_{m['id']}"):
                    cur = conn.cursor()
                    cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], m['sender_id'], rep))
                    conn.commit(); st.success("Réponse envoyée!")

elif choice == "🛡️ Administration DBA":
    st.title("🛡️ Administration System")
    t_u, t_a = st.tabs(["Base 100k", "Audit Logs"])
    with t_u:
        s = st.text_input("🔍 Rechercher par ID/Email")
        q = "SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
        st.dataframe(run_query(q, (f'%{s}%', s)), use_container_width=True)
    with t_a:
        st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 100"), use_container_width=True)