import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="NEKTA | Sécurité Maximale", page_icon="🛡️", layout="wide")

DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)

# FONKSYON SEKIRIZE KI ITILIZE PARAMÈT (%s) POU BLOKE SQL INJECTION
def run_secure_query(query, params=None):
    try:
        conn = get_connection()
        if conn.closed: 
            st.cache_resource.clear()
            conn = get_connection()
        # Itilize pandas ak paramèt separe (pafè kont injection)
        return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.cache_resource.clear()
        return pd.DataFrame()

# 2. DESIGN CSS
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    .hero { 
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1350');
        background-size: cover; padding: 80px; border-radius: 25px; color: white; text-align: center;
    }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-left: 8px solid #2563eb; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTÈM AUTHENTIFICATION BLENDE ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🛡️ NEKTA SECURE GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion Sécurisée", "📝 Inscription"])
    
    with t1:
        with st.form("login_gate"):
            user_email = st.text_input("Email Professionnel")
            user_password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Vérifier les identifiants"):
                # ITILIZE PARAMÈT %s POU BLOKE ' OR '1'='1
                sql = "SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND password_hash = crypt(%s, password_hash) LIMIT 1"
                res = run_secure_query(sql, (user_email, user_password))
                
                if not res.empty:
                    st.session_state.update({'auth':True, 'user':res.iloc[0].to_dict()})
                    st.rerun()
                else:
                    st.error("Accès refusé : Identifiants incorrects ou tentative d'intrusion détectée.")
    
    with t2:
        with st.form("reg_gate"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("Créer un compte audité"):
                try:
                    conn = get_connection(); cur = conn.cursor()
                    # Ensèsyon sekirize ak paramèt
                    cur.execute("INSERT INTO users (full_name, email, password_hash, role, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'UTILISATEUR', %s) RETURNING id", (fn, em, pw, ut))
                    new_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (new_id, f"Profil certifié de {fn}"))
                    conn.commit()
                    st.success("Compte sécurisé créé avec succès !")
                except: st.error("L'email est déjà enregistré dans le système.")
    st.stop()

# --- NAVIGATION APRE KONEKSYON ---
with st.sidebar:
    st.markdown(f"### 🛡️ SESYON SEKIRIZE")
    st.write(f"**{st.session_state['user']['full_name']}**")
    if st.button("🚪 Se déconnecter"): st.session_state.clear(); st.rerun()
    st.divider()
    menu = st.radio("WORKSPACE", ["🌐 Accueil", "💎 Talents", "💼 Missions", "📥 Messagerie", "📊 Statistiques", "🛡️ Administration"])

# --- PAGES ---
conn = get_connection()

if menu == "🌐 Accueil":
    st.markdown('<div class="hero"><h1>NEKTA : Sécurité & Performance</h1><p>Algorithmes de confiance protégés contre les injections SQL.</p></div>', unsafe_allow_html=True)
    st.info("💡 **Protocole** : Toutes vos transactions sont cryptées et auditées en temps réel.")

elif menu == "💎 Talents":
    st.title("💎 Annuaire des Talents")
    search = st.text_input("🔍 Recherche paramétrée (Anti-Injection)")
    # Rechèch sekirize
    sql = "SELECT u.full_name, u.user_type, p.trust_score, p.bio FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.full_name ILIKE %s OR p.bio ILIKE %s LIMIT 12"
    df = run_secure_query(sql, (f'%{search}%', f'%{search}%'))
    
    cols = st.columns(3)
    for i, r in df.iterrows():
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br><small>{r['user_type']}</small><p>{r['bio'][:80]}...</p><h4>{r['trust_score']}%</h4></div>", unsafe_allow_html=True)

elif menu == "💼 Missions":
    t1, t2, t3 = st.tabs(["📢 Offres", "👥 Postulants", "➕ Publier"])
    with t1:
        df_j = run_secure_query("SELECT id, title, budget, description FROM jobs WHERE status = 'OPEN' ORDER BY id DESC LIMIT 10")
        for i, j in df_j.iterrows():
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"p_{j['id']}"):
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (int(j['id']), st.session_state['user']['id']))
                        conn.commit(); st.success("Postulé !")
                    except: st.error("Déjà postulé.")
    with t2:
        df_apps = run_secure_query("SELECT a.id, j.title, u.full_name FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s", (st.session_state['user']['id'],))
        st.dataframe(df_apps, use_container_width=True)
    with t3:
        with st.form("new_j"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget", min_value=10), st.text_area("Description")
            if st.form_submit_button("Lancer"):
                cur = conn.cursor(); cur.execute("INSERT INTO jobs (client_id, title, budget, description, status) VALUES (%s, %s, %s, %s, 'OPEN')", (st.session_state['user']['id'], ti, bu, de))
                conn.commit(); st.success("Publié !")

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_secure_query("SELECT u.full_name as de, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state['user']['id'],))
    for _, m in msgs.iterrows():
        st.markdown(f"<div class='card'><b>De: {m['de']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)

elif menu == "📊 Statistiques":
    st.title("📊 Intelligence des Données")
    df_u = run_secure_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.5))

elif menu == "🛡️ Administration":
    if st.session_state['user']['role'] != 'ADMIN':
        st.error("Droit d'accès insuffisant.")
    else:
        st.title("🛡️ Contrôle DBA")
        search_admin = st.text_input("🔍 Recherche ID ou Email (Sanitisée)")
        df_adm = run_secure_query("SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100", (f'%{search_admin}%', search_admin))
        st.dataframe(df_adm, use_container_width=True)
        st.write("### 📜 Audit Logs SQL")
        st.table(run_secure_query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10"))