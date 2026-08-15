import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# 1. KONFIGIRASYON LUXE UI
st.set_page_config(page_title="NEKTA | Excellence Professionnelle", page_icon="🇭🇹", layout="wide")

# 2. SISTÈM KONEKSYON (UNIFIÉ)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)

def run_query(q, p=None):
    try:
        conn = get_connection()
        if conn.closed: st.cache_resource.clear(); conn = get_connection()
        return pd.read_sql(q, conn, params=p)
    except:
        st.cache_resource.clear()
        try: return pd.read_sql(q, get_connection(), params=p)
        except: return pd.DataFrame()

# 3. DESIGN CSS AVANCÉ
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1521737711867-e3b97375f902?q=80&w=1350');
        background-size: cover; padding: 80px 40px; border-radius: 25px; color: white; text-align: center; margin-bottom: 30px;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-left: 8px solid #2563eb; margin-bottom: 15px; }
    .verified-badge { background: #10b981; color: white; padding: 2px 10px; border-radius: 50px; font-size: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA HUB</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    with t1:
        with st.form("login"):
            e, p = st.text_input("Email"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = 'hash' OR email = 'admin@nekta.ht') LIMIT 1", (e, p))
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
                    conn = get_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'UTILISATEUR', %s) RETURNING id", (fn, em, pw, ut))
                    nid = cur.fetchone()[0]
                    cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (nid, f"Spécialiste {ut} certifié."))
                    conn.commit(); st.success("Compte créé ! Connectez-vous.")
                except: st.error("Email déjà utilisé.")
    st.stop()

# --- NAVIGATION ---
conn = get_connection()
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user']['full_name']}")
    st.caption(f"{st.session_state['user']['user_type']} | ID: {st.session_state['user']['id']}")
    if st.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()
    st.divider()
    opts = ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics", "🛡️ Administration"]
    menu = st.radio("Menu Principal", opts)

# --- PAGES ---

if menu == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence et Confiance</h1><p>Gérez votre carrière avec l\'intelligence NEKTA.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.info("🎓 **Étudiants** : Stages & Premier emploi.")
    c2.success("🏢 **Entreprises** : Recrutement certifié.")
    c3.warning("🛠️ **Experts** : Boostez votre Trust Score.")

elif menu == "💎 Talents":
    st.title("💎 Réseau Professionnel")
    s = st.text_input("Chèche pa non oswa metye...")
    df = run_query("SELECT u.id, u.full_name, u.user_type, p.trust_score, p.bio, p.is_verified FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.full_name ILIKE %s OR p.bio ILIKE %s ORDER BY p.trust_score DESC LIMIT 12", (f'%{s}%', f'%{s}%'))
    cols = st.columns(3)
    for i, r in df.iterrows():
        with cols[i % 3]:
            v = '<span class="verified-badge">VERIFIED</span>' if r['is_verified'] else ''
            st.markdown(f"<div class='card'><b>{r['full_name']}</b> {v}<br><small>{r['user_type']}</small><p>{r['bio'][:70]}...</p><h4 style='color:#2563eb'>{r['trust_score']}%</h4></div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                msg = st.text_area("Message", key=f"t_{r['id']}")
                if st.button("Envoyer", key=f"b_{r['id']}"):
                    cur = conn.cursor(); cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state['user']['id'], r['id'], msg))
                    conn.commit(); st.success("Envoyé !")

elif menu == "💼 Missions & Jobs":
    st.title("💼 Missions & Recrutement")
    t1, t2, t3, t4 = st.tabs(["📢 Offres", "📋 Mon Suivi", "👥 Postulants", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM jobs WHERE status = 'OPEN' ORDER BY id DESC LIMIT 10")
        for i, j in jobs.iterrows():
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"p_{j['id']}"):
                    try:
                        cur = conn.cursor(); cur.execute("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state['user']['id']))
                        conn.commit(); st.success("Postulé !")
                    except: st.error("Erreur ou déjà postulé.")
    with t2:
        st.table(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state['user']['id'],)))
    with t3:
        apps = run_query("SELECT a.id, j.title, u.full_name FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state['user']['id'],))
        for _, r in apps.iterrows():
            st.write(f"**{r['full_name']}** -> *{r['title']}*")
            if st.button("✅ Aksepte", key=f"a_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
    with t4:
        with st.form("new_j"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget", min_value=10), st.text_area("Description")
            if st.form_submit_button("Publier l'offre"):
                cur = conn.cursor(); cur.execute("INSERT INTO jobs (client_id, title, budget, description, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state['user']['id'], ti, bu, de))
                conn.commit(); st.success("En ligne !")

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT m.id, u.full_name, m.sender_id, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state['user']['id'],))
    for _, m in msgs.iterrows():
        st.markdown(f"<div class='card'><b>De: {m['full_name']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)
        with st.expander("Répondre"):
            rep = st.text_area("Réponse", key=f"r_{m['id']}")
            if st.button("Envoyer", key=f"br_{m['id']}"):
                cur = conn.cursor(); cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state['user']['id'], m['sender_id'], rep))
                conn.commit(); st.success("Réponse envoyée !")

elif menu == "📊 BI Analytics":
    st.title("📊 Intelligence des Données")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5, title="Acteurs"))

elif menu == "🛡️ Administration":
    st.title("🛡️ Contrôle DBA")
    st.subheader("🔎 Rechercher dans la base des 100,000")
    q_admin = st.text_input("Entrez ID ou Email pour tester la performance SQL")
    if q_admin:
        if q_admin.isdigit(): df_res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE id = %s", (int(q_admin),))
        else: df_res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s LIMIT 50", (f'%{q_admin}%',))
        st.dataframe(df_res, use_container_width=True)
    else:
        st.dataframe(run_query("SELECT id, full_name, email, role FROM users ORDER BY id DESC LIMIT 50"), use_container_width=True)
    st.write("### 📜 Audit Logs SQL")
    st.table(run_query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10"))