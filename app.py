import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from psycopg2.extras import RealDictCursor

# 1. KONFIGIRASYON PAJ LA
st.set_page_config(page_title="NEKTA | Excellence Professionnelle", page_icon="🇭🇹", layout="wide")

# 2. SISTÈM KONEKSYON (BLENDE)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True # Sa asire ke INSERT yo fèt touswit
        return conn
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

def run_query(query, params=None):
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_db_connection()
        return pd.read_sql(query, conn, params=params)
    except: return pd.DataFrame()

# 3. DESIGN CSS (Luxurious Style)
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .hero { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1521737711867-e3b97375f902?q=80&w=1350');
        background-size: cover; padding: 100px 40px; border-radius: 25px; color: white; text-align: center; margin-bottom: 30px;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-left: 8px solid #2563eb; margin-bottom: 20px; transition: 0.3s; }
    .card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
    .verified { background: #10b981; color: white; padding: 2px 10px; border-radius: 50px; font-size: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. SISTÈM AUTHENTIFICATION (LOGIN/SIGNUP SÈLMAN)
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<div style='text-align:center; padding-top:50px;'><h1>🚀 NEKTA : Excellence Professionnelle</h1><p>Veuillez vous connecter pour accéder au réseau.</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        t1, t2 = st.tabs(["🔑 Connexion", "📝 Création de compte"])
        
        with t1:
            with st.form("login_form"):
                e = st.text_input("Email")
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    # Tcheke modpas ak crypt oswa md5 (selon SQL nou an)
                    sql = "SELECT id, full_name, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                    res = run_query(sql, (e, p, p))
                    if not res.empty:
                        st.session_state.update({'auth':True, 'user':res.iloc[0].to_dict()})
                        st.rerun()
                    else: st.error("Identifiants incorrects.")
        
        with t2:
            with st.form("reg_form"):
                fn = st.text_input("Nom Complet")
                em = st.text_input("Email")
                pw = st.text_input("Mot de passe", type="password")
                ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
                if st.form_submit_button("S'inscrire"):
                    conn = get_db_connection(); cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'UTILISATEUR', %s)", (fn, em, pw, ut))
                        conn.commit(); st.success("Compte créé ! Connectez-vous.")
                    except: st.error("Email déjà utilisé.")
    st.stop()

# 5. NAVIGATION (Sidebar Sekirize)
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['user']['full_name']}")
    st.caption(f"{st.session_state['user']['user_type']} | Role: {st.session_state['user']['role']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    
    opts = ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics"]
    if st.session_state['user']['role'] == 'ADMIN': opts.append("🛡️ Administration")
    menu = st.radio("WORKSPACE", opts)

# --- LOGIQUE DES PAGES ---
conn = get_db_connection()

if menu == "🏠 Accueil":
    st.markdown("""
        <div class="hero">
            <h1>Bâtir la Confiance par la Donnée</h1>
            <p>La première plateforme de certification professionnelle en Haïti.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    avg_score = run_query("SELECT fn_get_trust_average()").iloc[0,0]
    col1.metric("Trust Score Moyen", f"{avg_score:.2f}%")
    total_u = run_query("SELECT COUNT(*) FROM users").iloc[0,0]
    col2.metric("Talents Certifiés", f"{total_u:,}")
    total_j = run_query("SELECT COUNT(*) FROM jobs").iloc[0,0]
    col3.metric("Missions Ouvertes", f"{total_j:,}")

elif menu == "💎 Talents":
    st.title("💎 Trouvez l'Expert de confiance")
    search = st.text_input("🔍 Recherche (Plombier, Informaticien, Nom...)")
    
    # Itilize VUE vw_talents nou te kreye a
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{search}%',))
    
    if df.empty: st.warning("Aucun talent trouvé pour cette recherche.")
    else:
        cols = st.columns(3)
        for i, r in df.iterrows():
            with cols[i % 3]:
                v = '<span class="verified">VERIFIED</span>' if r['is_verified'] else ''
                st.markdown(f"""
                    <div class="card">
                        <div style='display:flex; justify-content:space-between'><b>{r['full_name']}</b> {v}</div>
                        <h4 style='color:#2563eb; margin:5px 0;'>Score: {r['trust_score']}%</h4>
                        <p style='font-size:14px;'>Expert certifié disponible pour de nouvelles missions.</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("✉️ Contacter", key=f"msg_{i}"): st.info("Messagerie ouverte.")

elif menu == "💼 Missions & Jobs":
    t1, t2 = st.tabs(["📢 Offres Disponibles", "➕ Publier une offre"])
    
    with t1:
        # Itilize VUE vw_jobs_ouverts
        df_j = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for i, j in df_j.iterrows():
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                st.write("Description détaillée de la mission disponible sur demande.")
                if st.button("Postuler", key=f"app_{i}"):
                    st.success("Votre candidature a été envoyée !")

    with t2:
        st.subheader("Nouvelle mission")
        with st.form("job_publish", clear_on_submit=True):
            titre = st.text_input("Titre du poste")
            budg = st.number_input("Budget (USD)", min_value=0)
            desc = st.text_area("Description")
            if st.form_submit_button("Lancer l'offre"):
                cur = conn.cursor()
                cur.execute("INSERT INTO jobs (client_id, title, description, budget, status) VALUES (%s, %s, %s, %s, 'OPEN')", 
                            (st.session_state['user']['id'], titre, desc, budg))
                st.success("Mission publiée avec succès dans la base de données !")

elif menu == "📊 BI Analytics":
    st.title("📊 Intelligence des Données")
    df_u = run_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.6, title="Répartition des Talents"))

elif menu == "🛡️ Administration":
    if st.session_state['user']['role'] != 'ADMIN': st.error("Accès refusé.")
    else:
        st.title("🛡️ Panneau de Contrôle DBA")
        t_a1, t_a2 = st.tabs(["📋 Base des 100,000", "📜 Audit Logs (Trigger SQL)"])
        
        with t_a1:
            q_admin = st.text_input("🔍 Rechercher par ID ou Email dans les 100k records")
            if q_admin:
                if q_admin.isdigit(): df_res = run_query("SELECT id, full_name, email, role FROM users WHERE id = %s", (int(q_admin),))
                else: df_res = run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s LIMIT 50", (f'%{q_admin}%',))
                st.dataframe(df_res, use_container_width=True)
            else:
                st.dataframe(run_query("SELECT id, full_name, email, role FROM users ORDER BY id DESC LIMIT 100"), use_container_width=True)
        
        with t_a2:
            st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 100"), use_container_width=True)