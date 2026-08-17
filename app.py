import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import math

# 1. KONFIGIRASYON UI / PAGE CONFIG
st.set_page_config(
    page_title="NEKTA | Plateforme d'Opportunités & Confiance",
    page_icon="🇭🇹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. KONEKSYON AK BAZ DONE NEON (SSL)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)

def run_secure_query(query, params=None):
    """Lekti done sekirize"""
    try:
        conn = get_connection()
        if conn.closed:
            st.cache_resource.clear()
            conn = get_connection()
        conn.autocommit = True
        return pd.read_sql(query, conn, params=params)
    except Exception as e:
        st.cache_resource.clear()
        st.error(f"Erè nan lekti done: {e}")
        return pd.DataFrame()

def execute_action(query, params=None):
    """Ekzekisyon tranzaksyon (INSERT, UPDATE, DELETE, CALL)"""
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
        st.error(f"Erè nan ekzekisyon: {e}")
        return False

# 3. DESIGN CSS PERSONNALISÉ (MODÈN E ELEGANT)
st.markdown("""
    <style>
    /* Gradient Header & Theme */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important; 
    }
    [data-testid="stSidebar"] * { 
        color: #f8fafc !important; 
    }
    
    /* Hero Banner Custom */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 40px 25px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    /* Cards UI */
    .custom-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-top: 4px solid #2563eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        color: #0f172a;
    }
    
    .badge-job { background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }
    .badge-stage { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }
    .badge-event { background-color: #fce7f3; color: #9d174d; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }
    .badge-training { background-color: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; }

    /* Custom Metrics */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 5px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

# 4. GESTION DE LA SESSION & AUTHENTIFICATION
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.markdown("""
        <div class="hero-banner">
            <h1>🇭🇹 NEKTA PLATFORM</h1>
            <p>Emplois, Stages, Formations & Opportunités Certifiées en Haïti</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔑 Se Connecter", "📝 S'inscrire"])
    
    with tab_login:
        with st.form("form_login"):
            email_in = st.text_input("Adresse Email")
            pass_in = st.text_input("Mot de passe", type="password")
            btn_login = st.form_submit_button("Connexion", use_container_width=True)
            
            if btn_login:
                sql_auth = """
                    SELECT id, full_name, email, role, user_type 
                    FROM users 
                    WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) 
                    LIMIT 1
                """
                res = run_secure_query(sql_auth, (email_in, pass_in, pass_in))
                if not res.empty:
                    st.session_state.update({'auth': True, 'user': res.iloc[0].to_dict()})
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    with tab_register:
        with st.form("form_register"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type de Compte", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            rl = st.selectbox("Rôle Système", ["USER", "OPERATEUR", "ADMIN"])
            btn_reg = st.form_submit_button("Créer mon compte", use_container_width=True)
            
            if btn_reg:
                sql_reg = "INSERT INTO users (full_name, email, password_hash, user_type, role) VALUES (%s, %s, md5(%s), %s, %s)"
                if execute_action(sql_reg, (fn, em, pw, ut, rl)):
                    st.success("Compte créé avec succès ! Veuillez vous connecter.")
                else:
                    st.error("Impossible de créer le compte. Cet email existe déjà.")
    st.stop()

# 5. NAVIGATION SIDEBAR
user = st.session_state['user']
with st.sidebar:
    st.markdown(f"### 👤 {user['full_name']}")
    st.caption(f"Role: **{user['role']}** | Type: **{user['user_type']}**")
    st.caption(f"ID: `{user['id']}`")
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Meni ki adapte selon ròl itilizatè a
    menu_options = [
        "🏠 Accueil & Feed",
        "💎 Talents & Services",
        "💼 Missions & Opportunités",
        "📮 Postuler / Offrir",
        "💬 Messagerie Directe",
        "⭐ Évaluations & Avis",
        "📊 Statistiques (BI)"
    ]
    
    if user['role'] in ['OPERATEUR', 'ADMIN']:
        menu_options.append("⚙️ Espace Opérateur")
    if user['role'] == 'ADMIN':
        menu_options.append("🛡️ Administration (100k Data)")
        
    menu = st.radio("NAVIGATION", menu_options)

# ==========================================
# PAGE 1: ACCUEIL & FEED
# ==========================================
if menu == "🏠 Accueil & Feed":
    st.markdown("""
        <div class="hero-banner">
            <h2>Bienvenue sur NEKTA</h2>
            <p>Le réseau professionnel qui valorise les compétences et sécurise les échanges.</p>
        </div>
    """, unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    avg_score = run_secure_query("SELECT fn_get_trust_average()").iloc[0,0]
    m1.metric("Trust Score Moyen", f"{avg_score:.1f}%")
    
    total_jobs = run_secure_query("SELECT COUNT(*) FROM jobs").iloc[0,0]
    m2.metric("Total Opportunités", f"{total_jobs:,}")
    
    total_users = run_secure_query("SELECT COUNT(*) FROM users").iloc[0,0]
    m3.metric("Membres Actifs", f"{total_users:,}")
    
    my_msgs = run_secure_query("SELECT fn_total_messages(%s)", (user['id'],)).iloc[0,0]
    m4.metric("Mes Messages", my_msgs)
    
    st.subheader("📢 Dernières Opportunités Publiées")
    df_feed = run_secure_query("SELECT j.id, j.title, j.category, j.budget, u.full_name FROM jobs j JOIN users u ON j.client_id = u.id ORDER BY j.created_at DESC LIMIT 6")
    
    cols = st.columns(3)
    for idx, row in df_feed.iterrows():
        with cols[idx % 3]:
            st.markdown(f"""
                <div class="custom-card">
                    <span class="badge-job">{row['category']}</span>
                    <h4 style="margin-top:10px;">{row['title']}</h4>
                    <p><b>Publié par:</b> {row['full_name']}</p>
                    <p style="color:#2563eb; font-weight:bold;">Budget: ${row['budget']:,.2f}</p>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: TALENTS & SERVICES (CHERCHER / PUBLIER KONPETANS)
# ==========================================
elif menu == "💎 Talents & Services":
    st.title("💎 Réseau des Talents & Offres de Services")
    
    t_search, t_publish = st.tabs(["🔍 Rechercher un Talent", "➕ Publier mes Compétences"])
    
    with t_search:
        search_term = st.text_input("Rechercher un professionnel par nom, compétence...")
        df_talents = run_secure_query(
            "SELECT * FROM vw_talents WHERE full_name ILIKE %s OR bio ILIKE %s LIMIT 12",
            (f'%{search_term}%', f'%{search_term}%')
        )
        
        if not df_talents.empty:
            c_talents = st.columns(3)
            for i, r in df_talents.iterrows():
                with c_talents[i % 3]:
                    st.markdown(f"""
                        <div class="custom-card">
                            <h4>{r['full_name']}</h4>
                            <p><b>Score de Confiance:</b> {r['trust_score']}%</p>
                            <p><i>{r['bio'] if r['bio'] else 'Aucune description disponible.'}</i></p>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"💬 Contacter {r['full_name'].split()[0]}", key=f"contact_{r['user_id']}"):
                        st.session_state['target_msg_user'] = r['user_id']
                        st.info("Rendez-vous dans l'onglet 'Messagerie Directe' pour échanger.")
        else:
            st.info("Aucun talent trouvé.")
            
    with t_publish:
        st.subheader("Mettez vos compétences en avant")
        with st.form("form_profile"):
            bio_input = st.text_area("Décrivez vos compétences, formations et réalisations")
            submit_profile = st.form_submit_button("Mettre à jour mon profil")
            if submit_profile:
                sql_p = "INSERT INTO profiles (user_id, bio) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET bio = EXCLUDED.bio"
                if execute_action(sql_p, (user['id'], bio_input)):
                    st.success("Profil mis à jour avec succès !")

# ==========================================
# PAGE 3: MISSIONS, STAGES & ÉVÉNEMENTS
# ==========================================
elif menu == "💼 Missions & Opportunités":
    st.title("💼 Offres d'Emplois, Stages & Événements")
    
    category_filter = st.selectbox("Filtrer par type", ["TOUS", "EMPLOI", "STAGE", "FORMATION_GRATUITE", "EVENEMENT"])
    
    if category_filter == "TOUS":
        sql_jobs = "SELECT j.id, j.title, j.description, j.budget, j.category, u.full_name, j.client_id FROM jobs j JOIN users u ON j.client_id = u.id ORDER BY j.created_at DESC LIMIT 20"
        df_jobs = run_secure_query(sql_jobs)
    else:
        sql_jobs = "SELECT j.id, j.title, j.description, j.budget, j.category, u.full_name, j.client_id FROM jobs j JOIN users u ON j.client_id = u.id WHERE j.category = %s ORDER BY j.created_at DESC LIMIT 20"
        df_jobs = run_secure_query(sql_jobs, (category_filter,))
        
    for _, row in df_jobs.iterrows():
        col_main, col_action = st.columns([3, 1])
        with col_main:
            st.markdown(f"""
                <div class="custom-card">
                    <span class="badge-job">{row['category']}</span>
                    <h3 style="margin-top:5px;">{row['title']}</h3>
                    <p>{row['description']}</p>
                    <p><b>Publié par:</b> {row['full_name']} | <b>Budget/Prix:</b> ${row['budget']:,.2f}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_action:
            if row['client_id'] != user['id']:
                if st.button(f"📝 Postuler", key=f"apply_{row['id']}", use_container_width=True):
                    sql_apply = "INSERT INTO applications (job_id, professional_id, status) VALUES (%s, %s, 'PENDING')"
                    if execute_action(sql_apply, (row['id'], user['id'])):
                        st.success("Candidature envoyée !")
            else:
                st.caption("Votre annonce")

# ==========================================
# PAGE 4: POSTULER & GÉRER LES CANDIDATURES
# ==========================================
elif menu == "📮 Postuler / Offrir":
    st.title("📮 Publier une Opportunité & Gérer les Candidatures")
    
    tab_post, tab_manage = st.tabs(["➕ Publier une Annonce", "📥 Gérer mes Candidats"])
    
    with tab_post:
        with st.form("form_post_job"):
            j_title = st.text_input("Titre de l'annonce")
            j_cat = st.selectbox("Type d'opportunité", ["EMPLOI", "STAGE", "FORMATION_GRATUITE", "EVENEMENT"])
            j_budget = st.number_input("Budget ou Gratification ($)", min_value=0.0, value=100.0)
            j_desc = st.text_area("Description détaillée")
            btn_post = st.form_submit_button("Publier l'annonce")
            
            if btn_post:
                sql_pj = "INSERT INTO jobs (client_id, title, description, budget, category, status) VALUES (%s, %s, %s, %s, %s, 'OPEN')"
                if execute_action(sql_pj, (user['id'], j_title, j_desc, j_budget, j_cat)):
                    st.success("Annonce publiée avec succès !")
                    
    with tab_manage:
        st.subheader("Candidatures reçues sur vos annonces")
        sql_apps = """
            SELECT a.id as app_id, u.id as applicant_id, u.full_name, j.title, a.status 
            FROM applications a 
            JOIN jobs j ON a.job_id = j.id 
            JOIN users u ON a.professional_id = u.id 
            WHERE j.client_id = %s AND a.status = 'PENDING'
        """
        df_apps = run_secure_query(sql_apps, (user['id'],))
        
        if not df_apps.empty:
            for _, app in df_apps.iterrows():
                c_info, c_btn1, c_btn2 = st.columns([2, 1, 1])
                c_info.write(f"**{app['full_name']}** a postulé pour **{app['title']}**")
                
                if c_btn1.button("✅ Aksepte", key=f"acc_{app['app_id']}"):
                    execute_action("CALL sp_accepter_candidature(%s)", (int(app['app_id']),))
                    st.success("Candidat accepté ! Le Trust Score a été augmenté.")
                    st.rerun()
                    
                if c_btn2.button("❌ Refize", key=f"ref_{app['app_id']}"):
                    execute_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (int(app['app_id']),))
                    st.warning("Candidature refusée.")
                    st.rerun()
        else:
            st.info("Aucune candidature en attente.")

# ==========================================
# PAGE 5: MESSAGERIE DIRECTE
# ==========================================
elif menu == "💬 Messagerie Directe":
    st.title("💬 Messagerie Professionnelle")
    
    t_inbox, t_send = st.tabs(["📥 Boîte de Réception", "✉️ Envoyer un Message"])
    
    with t_inbox:
        sql_inbox = """
            SELECT m.id, u.full_name as expéditeur, m.content, m.sent_at 
            FROM messages m 
            JOIN users u ON m.sender_id = u.id 
            WHERE m.receiver_id = %s 
            ORDER BY m.sent_at DESC
        """
        df_inbox = run_secure_query(sql_inbox, (user['id'],))
        
        if not df_inbox.empty:
            for _, msg in df_inbox.iterrows():
                st.markdown(f"""
                    <div class="custom-card">
                        <b>De: {msg['expéditeur']}</b> <span style="float:right; font-size:12px; color:gray;">{msg['sent_at']}</span>
                        <p style="margin-top:10px;">{msg['content']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Votre boîte de réception est vide.")
            
    with t_send:
        with st.form("form_send_msg"):
            target_user_id = st.number_input("ID du Destinataire", min_value=1, step=1, value=st.session_state.get('target_msg_user', 1))
            msg_content = st.text_area("Votre message")
            btn_send = st.form_submit_button("Envoyer le message")
            
            if btn_send:
                sql_send = "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)"
                if execute_action(sql_send, (user['id'], target_user_id, msg_content)):
                    st.success("Message envoyé avec succès !")

# ==========================================
# PAGE 6: EVALUATIONS ET AVIS
# ==========================================
elif menu == "⭐ Évaluations & Avis":
    st.title("⭐ Évaluations et Avis des Services")
    
    with st.form("form_review"):
        reviewed_user_id = st.number_input("ID du Professionnel évalué", min_value=1, step=1)
        rating = st.slider("Note (1 à 5)", 1, 5, 5)
        comment = st.text_area("Votre avis sur la prestation")
        btn_rev = st.form_submit_button("Soumettre l'évaluation")
        
        if btn_rev:
            sql_rev = "INSERT INTO reviews (evaluator_id, evaluated_id, rating, comment) VALUES (%s, %s, %s, %s)"
            if execute_action(sql_rev, (user['id'], reviewed_user_id, rating, comment)):
                st.success("Évaluation enregistrée !")

# ==========================================
# PAGE 7: STATISTIQUES (BI)
# ==========================================
elif menu == "📊 Statistiques (BI)":
    st.title("📊 Business Intelligence & Dashboard")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        df_u_type = run_secure_query("SELECT user_type, COUNT(*) as nombre FROM users GROUP BY user_type")
        if not df_u_type.empty:
            fig1 = px.pie(df_u_type, values='nombre', names='user_type', title="Répartition des Utilisateurs", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
            
    with col_chart2:
        df_j_cat = run_secure_query("SELECT category, COUNT(*) as nombre FROM jobs GROUP BY category")
        if not df_j_cat.empty:
            fig2 = px.bar(df_j_cat, x='category', y='nombre', title="Annonces par Catégorie", color='category')
            st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# PAGE 8: ESPACE OPERATEUR
# ==========================================
elif menu == "⚙️ Espace Opérateur":
    st.title("⚙️ Panneau de Contrôle Opérateur")
    st.info("Cet espace permet la modération des comptes et la vérification des données système.")
    
    tab_mod, tab_verify = st.tabs(["🛡️ Modération des Annonces", "✅ Vérification des Profils"])
    
    with tab_mod:
        df_all_jobs = run_secure_query("SELECT id, title, category, status FROM jobs ORDER BY id DESC LIMIT 20")
        st.dataframe(df_all_jobs, use_container_width=True)
        
    with tab_verify:
        v_user_id = st.number_input("ID Utilisateur à vérifier", min_value=1, step=1)
        if st.button("Valider / Vérifier le Profil"):
            sql_v = "UPDATE profiles SET is_verified = TRUE WHERE user_id = %s"
            if execute_action(sql_v, (v_user_id,)):
                st.success(f"Profil ID {v_user_id} marqué comme VÉRIFIÉ !")

# ==========================================
# PAGE 9: ADMINISTRATION (100K DATA VIEW)
# ==========================================
elif menu == "🛡️ Administration (100k Data)":
    st.title("🛡️ Vue d'Ensemble des 100,000 Données")
    st.caption("Paginasyon rapid pou jere 100 000 itilizatè yo san okenn ralentissement.")
    
    page_size = 50
    total_records = run_secure_query("SELECT COUNT(*) FROM users").iloc[0,0]
    total_pages = math.ceil(total_records / page_size)
    
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    page_num = col_p2.number_input(f"Page (Total: {total_pages:,} pages)", min_value=1, max_value=total_pages, value=1)
    
    offset = (page_num - 1) * page_size
    
    search_admin = st.text_input("🔍 Rechercher par email ou ID dans les 100 000 utilisateurs")
    
    if search_admin:
        sql_admin = "SELECT id, full_name, email, role, user_type, created_at FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 50"
        df_100k = run_secure_query(sql_admin, (f'%{search_admin}%', search_admin))
    else:
        sql_admin = "SELECT id, full_name, email, role, user_type, created_at FROM users ORDER BY id ASC LIMIT %s OFFSET %s"
        df_100k = run_secure_query(sql_admin, (page_size, offset))
        
    st.dataframe(df_100k, use_container_width=True)
    st.success(f"Affichage de {len(df_100k)} enregistrements sur un total de {total_records:,} utilisateurs.")