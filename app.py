import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE & DESIGN LUXUEUX
st.set_page_config(
    page_title="NEKTA - Réseau Professionnel",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
    <style>
    /* Sidebar pwofesyonèl nwa */
    [data-testid="stSidebar"] { background-color: #0d1117 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; font-weight: 500; }
    
    /* Hero Box ak gradyan */
    .hero-box { 
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 50px 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    /* Cards Talent */
    .card { 
        background: #ffffff; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; 
        margin-bottom: 15px; color: #1e293b; transition: 0.3s;
    }
    .card:hover { transform: translateY(-5px); box-shadow: 0 12px 30px rgba(0,0,0,0.1); }
    
    /* Metrics */
    div[data-testid="stMetric"] { 
        background: white; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-bottom: 4px solid #1e3a8a; 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION SÉCURISÉE À LA BASE DE DONNÉES (NEON)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        return None

def run_query(query, params=None, fetch="all"):
    conn = get_db_connection()
    if not conn or conn.closed:
        st.cache_resource.clear()
        conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch == "all": return cur.fetchall()
            if fetch == "one": return cur.fetchone()
        return None
    except: return [] if fetch == "all" else None

# 3. AUTHENTIFICATION SÉCURISÉE
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🇭🇹 NEKTA GATEWAY</h1><p style='text-align:center;'>La plateforme d'excellence professionnelle certifiée.</p>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Créer un compte"])
    
    with t1:
        with st.form("login"):
            e = st.text_input("Adresse Email")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                # ITILIZE %s POU BLOKE SQL INJECTION (Sekirite pwofese a mande a)
                sql = "SELECT id, full_name, role FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                res = run_query(sql, (e, p, p), fetch="one")
                if res:
                    st.session_state.user_id = res['id']
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Email ou mot de passe incorrect.")
                    
    with t2:
        with st.form("register"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                conn = get_db_connection(); cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s) RETURNING id", (fn, em, pw, ut))
                    new_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (new_id, f"Profil certifié de {fn}"))
                    conn.commit(); st.success("Compte créé ! Veuillez vous connecter.")
                except: st.error("Email déjà utilisé.")
    st.stop()

# Charger les données de l'utilisateur actuel
current_user = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE id = %s", (st.session_state.user_id,), fetch="one")

# 4. SIDEBAR
with st.sidebar:
    st.markdown(f"### 👤 {current_user['full_name']}")
    st.caption(f"ID: {current_user['id']} | {current_user['user_type']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    page = st.radio("NAVIGATION", ["Accueil & Feed", "Talents & Services", "Missions & Opportunités", "Mes Candidatures", "Messagerie", "Statistiques", "Administration"])

# 5. PAGES
if page == "Accueil & Feed":
    st.markdown('<div class="hero-box"><h1>Bienvenue sur NEKTA</h1><p>Le réseau de confiance certifié par PostgreSQL.</p></div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Membres Actifs", "100,000")
    m2.metric("Trust Score Moyen", f"{run_query('SELECT fn_get_trust_average()', fetch='one')['fn_get_trust_average']:.1f}%")
    m3.metric("Status", "Sécurisé")

elif page == "Talents & Services":
    st.header("💎 Annuaire des Talents (Vue: vw_talents)")
    search = st.text_input("🔍 Rechercher par nom ou compétence...")
    # Sèvi ak VUE vw_talents pou n ale rapid
    sql = "SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12"
    talents = run_query(sql, (f"%{search}%",))
    
    cols = st.columns(3)
    for idx, t in enumerate(talents):
        with cols[idx % 3]:
            st.markdown(f"""<div class='card'><b>{t['full_name']}</b><br>Score: {t['trust_score']}%<br>{'✅ Vérifié' if t['is_verified'] else ''}</div>""", unsafe_allow_html=True)
            if st.button("✉️ Contacter", key=f"msg_{idx}"): st.info("Messagerie ouverte.")

elif page == "Missions & Opportunités":
    st.header("💼 Missions (Vue: vw_jobs_ouverts)")
    t1, t2 = st.tabs(["📢 Offres", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 20")
        st.dataframe(pd.DataFrame(jobs), use_container_width=True)
    with t2:
        with st.form("new_job"):
            ti = st.text_input("Titre"); bu = st.number_input("Budget"); de = st.text_area("Description")
            if st.form_submit_button("Lancer"):
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO jobs (client_id, title, budget, description) VALUES (%s, %s, %s, %s)", (st.session_state.user_id, ti, bu, de))
                conn.commit(); st.success("Mission publiée !")

elif page == "Administration":
    if current_user['role'] != 'ADMIN': st.error("Accès réservé au DBA.")
    else:
        st.header("🛡️ Panneau d'Administration")
        tab_a1, tab_a2 = st.tabs(["📋 Base 100k", "📜 Audit Trail"])
        with tab_a1:
            q_admin = st.text_input("🔍 Recherche par ID ou Email")
            if q_admin:
                df_adm = run_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100", (f'%{q_admin}%', q_admin))
            else:
                df_adm = run_query("SELECT id, full_name, email, role FROM users ORDER BY id DESC LIMIT 100")
            st.dataframe(pd.DataFrame(df_adm), use_container_width=True)
        with tab_a2:
            # Itilize VUE vw_audit_trail
            logs = run_query("SELECT * FROM vw_audit_trail LIMIT 50")
            st.table(pd.DataFrame(logs))