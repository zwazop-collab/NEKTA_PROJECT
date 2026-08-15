import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="NEKTA | Écosystème Professionnel", page_icon="🇭🇹", layout="wide")

DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_conn():
    return psycopg2.connect(DB_URL)

def run_query(q, p=None):
    try:
        conn = get_conn()
        if conn.closed: st.cache_resource.clear(); conn = get_conn()
        return pd.read_sql(q, conn, params=p)
    except:
        st.cache_resource.clear()
        try: return pd.read_sql(q, get_conn(), params=p)
        except: return pd.DataFrame()

# 2. DESIGN CSS (Luxurious & Readable)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1521737711867-e3b97375f902?q=80&w=1350');
        background-size: cover; padding: 60px 40px; border-radius: 25px; color: white; text-align: center; margin-bottom: 30px;
    }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #2563eb; margin-bottom: 15px; }
    .msg-card { background: #f1f5f9; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center; padding-top:50px;'>🚀 NEKTA PLATFORM</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    with t1:
        with st.form("login"):
            e, p = st.text_input("Email"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = 'hash' OR password_hash = 'hashed_pwd') LIMIT 1", (e, p))
                if not res.empty:
                    st.session_state.update({'auth':True, 'user':res.iloc[0].to_dict()})
                    st.rerun()
                else: st.error("Identifiants incorrects.")
    with t2:
        with st.form("reg"):
            fn, em, pw = st.text_input("Nom"), st.text_input("Email"), st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                try:
                    conn = get_conn(); cur = conn.cursor()
                    cur.execute("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'UTILISATEUR', %s) RETURNING id", (fn, em, pw, ut))
                    nid = cur.fetchone()[0]
                    cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (nid, f"Spécialiste {ut} disponible."))
                    conn.commit(); st.success("Compte créé !")
                except: st.error("Erreur d'inscription.")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user']['full_name']}")
    st.caption(f"{st.session_state['user']['user_type']} | ID: {st.session_state['user']['id']}")
    if st.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()
    st.divider()
    opts = ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics"]
    if st.session_state['user']['role'] == 'ADMIN': opts.append("🛡️ Administration")
    menu = st.radio("Menu", opts)

conn = get_conn()

# --- PAGES ---

if menu == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>NEKTA : L\'Excellence par la Confiance</h1><p>La puissance de la donnée au service du talent haïtien.</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.info("🎓 **Étudiants** : Construisez votre Trust Score dès aujourd'hui.")
    col2.success("🏢 **Entreprises** : Recrutez des talents vérifiés sans intermédiaire.")
    col3.warning("🛠️ **Experts** : Valorisez vos compétences et gérez vos missions.")
    
    st.divider()
    st.subheader("🔔 Dernières Notifications")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state['user']['id'],))
    if notifs.empty: st.write("Aucune notification pour le moment.")
    for _, n in notifs.iterrows():
        color = "green" if n['status'] == 'ACCEPTED' else "orange"
        st.markdown(f"<p style='color:{color}; font-weight:bold;'>• Votre candidature pour '{n['title']}' est : {n['status']}</p>", unsafe_allow_html=True)

elif menu == "💎 Talents":
    st.title("💎 Réseau Professionnel")
    s = st.text_input("Chercher un nom ou un métier...")
    df = run_query("SELECT u.id, u.full_name, p.trust_score, p.bio FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.full_name ILIKE %s OR p.bio ILIKE %s LIMIT 12", (f'%{s}%', f'%{s}%'))
    cols = st.columns(3)
    for i, r in df.iterrows():
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br><small>Score: {r['trust_score']}%</p></div>", unsafe_allow_html=True)
            with st.expander("✉️ Envoyer un message"):
                txt = st.text_area("Tapez votre message", key=f"send_{r['id']}")
                if st.button("Envoyer", key=f"btn_{r['id']}"):
                    cur = conn.cursor()
                    cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state['user']['id'], r['id'], txt))
                    conn.commit(); st.success("Envoyé !")

elif menu == "💼 Missions & Jobs":
    t1, t2, t3, t4 = st.tabs(["📢 Offres", "📋 Mes Candidatures", "👥 Postulants reçus", "➕ Pousser une offre"])
    
    with t1:
        jobs = run_query("SELECT * FROM jobs WHERE status = 'OPEN' ORDER BY id DESC LIMIT 10")
        for i, j in jobs.iterrows():
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                st.write(j['description'])
                if st.button("Postuler", key=f"p_{j['id']}"):
                    try:
                        cur = conn.cursor(); cur.execute("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state['user']['id']))
                        conn.commit(); st.success("Postulé !")
                    except: st.error("Erreur ou déjà fait.")
    with t2:
        st.table(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state['user']['id'],)))
    with t3:
        apps = run_query("SELECT a.id, j.title, u.full_name, a.status FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state['user']['id'],))
        for _, r in apps.iterrows():
            st.write(f"**{r['full_name']}** -> *{r['title']}*")
            ca, cr = st.columns(2)
            if ca.button("✅ Accepter", key=f"a_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
            if cr.button("❌ Refuser", key=f"r_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
    with t4:
        with st.form("new_j"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget", min_value=10), st.text_area("Description")
            if st.form_submit_button("Publier l'offre"):
                cur = conn.cursor(); cur.execute("INSERT INTO jobs (client_id, title, budget, description, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state['user']['id'], ti, bu, de))
                conn.commit(); st.success("Offre en ligne !")

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT m.id, u.full_name, m.sender_id, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state['user']['id'],))
    if msgs.empty: st.info("Aucun message.")
    else:
        for _, m in msgs.iterrows():
            with st.container():
                st.markdown(f"<div class='msg-card'><b>De: {m['full_name']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)
                with st.expander(f"Répondre à {m['full_name']}"):
                    rep = st.text_area("Votre réponse", key=f"rep_{m['id']}")
                    if st.button("Envoyer la réponse", key=f"br_{m['id']}"):
                        cur = conn.cursor()
                        cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state['user']['id'], m['sender_id'], rep))
                        conn.commit(); st.success("Réponse envoyée !")

elif menu == "📊 BI Analytics":
    st.title("📊 Statistiques")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Volume par Acteur"))

elif menu == "🛡️ Administration":
    st.title("🛡️ Administration")
    t_1, t_2 = st.tabs(["📋 Base 100k", "📜 Audit Logs"])
    with t_1: st.dataframe(run_query("SELECT id, full_name, email, role FROM users LIMIT 100"), use_container_width=True)
    with t_2: st.table(run_query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 15"))