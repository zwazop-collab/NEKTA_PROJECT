import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# 1. KONFIGIRASYON PREMIUM UI
st.set_page_config(
    page_title="NEKTA | L'Excellence Certifiée",
    page_icon="🇭🇹",
    layout="wide"
)

# 2. SISTÈM KONEKSYON SEKIRIZE
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)

def run_secure_query(query, params=None):
    """Fonksyon ki jere lekti done yo ak sekirite SQL Injection"""
    try:
        conn = get_connection()
        if conn.closed:
            st.cache_resource.clear()
            conn = get_connection()
        # Asire tranzaksyon an pa rete nan eta "InFailedSqlTransaction"
        conn.autocommit = True
        return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.cache_resource.clear()
        st.error(f"Erè SQL: {e}")
        return pd.DataFrame()

def execute_action(query, params=None):
    """Fonksyon pou ekzekite INSERT, UPDATE, DELETE ak CALL procédure"""
    try:
        conn = get_connection()
        if conn.closed:
            st.cache_resource.clear()
            conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erè Ekzekisyon: {e}")
        return False

# 3. DESIGN CSS
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; font-weight: 600; }
    
    .hero-box { 
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1350');
        background-size: cover; padding: 60px 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .card { 
        background: white; padding: 20px; border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; 
        margin-bottom: 15px; color: #1e293b;
    }
    
    div[data-testid="stMetric"] { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); border-bottom: 4px solid #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTÈM AUTHENTIFICATION SEKIRIZE ---
if 'auth' not in st.session_state: 
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🇭🇹 NEKTA GATEWAY</h1><p style='text-align:center;'>La donnée au service de la confiance.</p>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Créer un compte"])
    
    with t1:
        with st.form("login_gate"):
            e = st.text_input("Email")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Vérifier les identifiants"):
                sql = "SELECT id, full_name, email, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                res = run_secure_query(sql, (e, p, p))
                if not res.empty:
                    st.session_state.update({'auth': True, 'user': res.iloc[0].to_dict()})
                    st.rerun()
                else: 
                    st.error("Accès refusé. Vérifiez vos informations.")
    
    with t2:
        with st.form("reg_gate"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Qui êtes-vous ?", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("Finaliser l'inscription"):
                success = execute_action(
                    "INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, md5(%s), %s)",
                    (fn, em, pw, ut)
                )
                if success:
                    # Kreyasyon profil otomatik la deja fèt pa trigger nan SQL la si w genyen l, swa nou asire p.user_id egziste:
                    user_res = run_secure_query("SELECT id FROM users WHERE email = %s", (em,))
                    if not user_res.empty:
                        uid = int(user_res.iloc[0]['id'])
                        execute_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, f"Profil de {fn}"))
                    st.success("Compte créé avec succès ! Connectez-vous.")
                else:
                    st.error("Erreur lors de la création du compte. Vérifiez l'email.")
    st.stop()

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=70)
    st.markdown(f"### 👤 {st.session_state['user']['full_name']}")
    st.caption(f"{st.session_state['user']['user_type']} | ID: {st.session_state['user']['id']}")
    if st.button("🚪 Déconnexion"): 
        st.session_state.clear()
        st.rerun()
    st.divider()
    
    menu_options = ["🏠 Accueil", "💎 Talents", "💼 Missions", "📥 Messagerie", "📊 BI Analytics"]
    if st.session_state['user']['role'] == 'ADMIN':
        menu_options.append("🛡️ Administration")
    
    menu = st.radio("WORKSPACE", menu_options)

# --- LOGIQUE DES PAGES ---

if menu == "🏠 Accueil":
    st.markdown('<div class="hero-box"><h1>L\'Excellence par la Confiance</h1><p>Algorithmes certifiés et traçabilité SQL totale.</p></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    avg_df = run_secure_query("SELECT fn_get_trust_average() as avg")
    avg_score = avg_df.iloc[0, 0] if not avg_df.empty else 0
    c1.metric("Score de Confiance Moyen", f"{float(avg_score):.2f}%")
    
    my_apps_df = run_secure_query("SELECT fn_count_user_apps(%s) as apps", (st.session_state['user']['id'],))
    my_apps = my_apps_df.iloc[0, 0] if not my_apps_df.empty else 0
    c2.metric("Vos Candidatures", my_apps)
    
    my_msgs_df = run_secure_query("SELECT fn_total_messages(%s) as msgs", (st.session_state['user']['id'],))
    my_msgs = my_msgs_df.iloc[0, 0] if not my_msgs_df.empty else 0
    c3.metric("Messages Reçus", my_msgs)

elif menu == "💎 Talents":
    st.title("💎 Réseau Professionnel (Vue: vw_talents)")
    search = st.text_input("🔍 Recherche paramétrée (Mete Nom oswa Mote cle)")
    df = run_secure_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{search}%',))
    
    if not df.empty:
        cols = st.columns(3)
        for i, r in df.iterrows():
            with cols[i % 3]:
                st.markdown(f"<div class='card'><b>{r['full_name']}</b><br>Score: {r['trust_score']}%<br>{'✅ Vérifié' if r['is_verified'] else '❌ Non Vérifié'}</div>", unsafe_allow_html=True)
    else:
        st.info("Aucun talent trouvé.")

elif menu == "💼 Missions":
    st.title("💼 Opportunités (Vue: vw_jobs_ouverts)")
    t1, t2 = st.tabs(["📢 Offres", "👥 Candidats"])
    with t1:
        st.dataframe(run_secure_query("SELECT * FROM vw_jobs_ouverts LIMIT 50"), use_container_width=True)
    with t2:
        apps = run_secure_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state['user']['id'],))
        if apps.empty: 
            st.info("Aucun candidat en attente pour vos missions.")
        else:
            for _, r in apps.iterrows():
                if st.button(f"Accepter {r['full_name']} ({r['title']})", key=f"btn_app_{r['id']}"):
                    if execute_action("CALL sp_accepter_candidature(%s)", (int(r['id']),)):
                        st.success("Candidat accepté ! Trust Score augmenté.")
                        st.rerun()

elif menu == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_secure_query("SELECT u.full_name as de, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC LIMIT 20", (st.session_state['user']['id'],))
    if not msgs.empty:
        for _, m in msgs.iterrows():
            st.markdown(f"<div class='card'><b>De: {m['de']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)
    else:
        st.info("Vous n'avez aucun message.")

elif menu == "📊 BI Analytics":
    st.title("📊 Intelligence des Données")
    df_u = run_secure_query("SELECT user_type, COUNT(*) as n FROM users GROUP BY user_type")
    if not df_u.empty:
        st.plotly_chart(px.pie(df_u, values='n', names='user_type', hole=0.6, title="Répartition des Talents par Type"))

elif menu == "🛡️ Administration":
    if st.session_state['user']['role'] != 'ADMIN': 
        st.error("Réservé au DBA.")
    else:
        st.title("🛡️ Administration Système")
        t_a1, t_a2 = st.tabs(["📋 Base 100,000 Users", "📜 Audit Trail (Vue)"])
        with t_a1:
            sid = st.text_input("🔍 Rechercher par ID ou Email")
            sql = "SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
            st.dataframe(run_secure_query(sql, (f'%{sid}%', sid)), use_container_width=True)
        with t_a2:
            st.dataframe(run_secure_query("SELECT * FROM vw_audit_trail LIMIT 100"), use_container_width=True)