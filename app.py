import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="NEKTA | Système de Confiance", page_icon="🇭🇹", layout="wide")

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

# 2. DESIGN CSS
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
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA : Excellence Professionnelle</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    with t1:
        with st.form("login"):
            e, p = st.text_input("Email"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = 'hash' OR password_hash = 'admin123') LIMIT 1", (e, p))
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
                    cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (nid, f"Profil de {fn}."))
                    conn.commit(); st.success("Compte créé ! Connectez-vous.")
                except: st.error("Erreur d'inscription.")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user']['full_name']}")
    if st.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()
    st.divider()
    menu = st.radio("Menu", ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics", "🛡️ Administration"])

conn = get_connection()

# --- PAGES ---

if menu == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Dashboard NEKTA</h1><p>Gérez vos données avec la puissance de PostgreSQL.</p></div>', unsafe_allow_html=True)
    st.success("✅ Bienvenue dans votre écosystème professionnel.")

elif menu == "💎 Talents":
    st.title("💎 Annuaire")
    s = st.text_input("Chercher un talent...")
    df = run_query("SELECT u.id, u.full_name, p.trust_score, p.bio FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.full_name ILIKE %s OR p.bio ILIKE %s LIMIT 12", (f'%{s}%', f'%{s}%'))
    cols = st.columns(3)
    for i, r in df.iterrows():
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br><small>Score: {r['trust_score']}%</p></div>", unsafe_allow_html=True)
            with st.expander("✉️ Message"):
                msg = st.text_area("Texte", key=f"t_{r['id']}")
                if st.button("Envoyer", key=f"b_{r['id']}"):
                    cur = conn.cursor(); cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state['user']['id'], r['id'], msg))
                    conn.commit(); st.success("Envoyé !")

elif menu == "💼 Missions & Jobs":
    t1, t2, t3, t4 = st.tabs(["📢 Offres", "📋 Mon Suivi", "👥 Postulants", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM jobs WHERE status = 'OPEN' ORDER BY id DESC LIMIT 10")
        for i, j in jobs.iterrows():
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"p_{j['id']}"):
                    try:
                        cur = conn.cursor(); cur.execute("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state['user']['id']))
                        conn.commit(); st.success("Postulé !")
                    except: st.error("Déjà postulé.")
    with t2:
        st.table(run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state['user']['id'],)))
    with t3:
        apps = run_query("SELECT a.id, j.title, u.full_name FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state['user']['id'],))
        for _, r in apps.iterrows():
            st.write(f"**{r['full_name']}** -> *{r['title']}*")
            if st.button("✅ Accepter", key=f"a_{r['id']}"):
                cur = conn.cursor(); cur.execute("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); conn.commit(); st.rerun()
    with t4:
        with st.form("new_j"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget", min_value=10), st.text_area("Description")
            if st.form_submit_button("Publier"):
                cur = conn.cursor(); cur.execute("INSERT INTO jobs (client_id, title, budget, description, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state['user']['id'], ti, bu, de))
                conn.commit(); st.success("Publiée !")

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT u.full_name as de, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state['user']['id'],))
    for _, m in msgs.iterrows():
        st.markdown(f"<div class='card'><b>De: {m['de']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)

elif menu == "📊 BI Analytics":
    st.title("📊 Statistiques")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5))

elif menu == "🛡️ Administration":
    st.title("🛡️ Espace de Contrôle DBA")
    st.write("Gestion massive des 100,000 enregistrements.")
    
    # 🔍 BA RECHÈCH ADMIN (GWO EPI PWÒP)
    st.subheader("🔎 Rechercher dans la base des 100,000")
    q_admin = st.text_input("Tapez un ID (ex: 85000) ou un Email", placeholder="Ex: 55234 ou user_850@nekta.ht")
    
    if q_admin:
        if q_admin.isdigit():
            df_res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE id = %s", (int(q_admin),))
        else:
            df_res = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s LIMIT 50", (f'%{q_admin}%',))
        st.success(f"Résultat pour: {q_admin}")
        st.dataframe(df_res, use_container_width=True)
    else:
        st.info("Affichage des 100 derniers inscrits (Utilisez la barre au-dessus pour chercher un ID spécifique)")
        df_last = run_query("SELECT id, full_name, email, role, user_type FROM users ORDER BY id DESC LIMIT 100")
        st.dataframe(df_last, use_container_width=True)
    
    st.divider()
    st.write("### 📜 Audit Logs")
    st.table(run_query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10"))