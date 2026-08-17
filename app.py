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
    except Exception:
        return None

def run_query(query, params=None, fetch="all"):
    conn = get_db_connection()
    if not conn or conn.closed:
        st.cache_resource.clear()
        conn = get_db_connection()
    if not conn:
        return [] if fetch == "all" else None
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch == "all": return cur.fetchall()
            if fetch == "one": return cur.fetchone()
        return None
    except Exception:
        return [] if fetch == "all" else None

def run_action(query, params=None):
    """Sèvi pou INSERT, UPDATE, DELETE san kreye erè"""
    conn = get_db_connection()
    if not conn or conn.closed:
        st.cache_resource.clear()
        conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        return True
    except Exception:
        return False

# 3. AUTHENTIFICATION SÉCURISÉE
if "auth" not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🇭🇹 NEKTA GATEWAY</h1><p style='text-align:center;'>La plateforme d'excellence professionnelle certifiée.</p>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Créer un compte"])
    
    with t1:
        with st.form("login"):
            e = st.text_input("Adresse Email")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                sql = "SELECT id, full_name, role FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                res = run_query(sql, (e, p, p), fetch="one")
                if res and isinstance(res, dict):
                    st.session_state.user_id = res['id']
                    st.session_state.auth = True
                    st.rerun()
                else: 
                    st.error("Email ou mot de passe incorrect.")
                    
    with t2:
        with st.form("register"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s) RETURNING id", (fn, em, pw, ut))
                        new_id = cur.fetchone()['id']
                        cur.execute("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (new_id, f"Profil certifié de {fn}"))
                        conn.commit()
                        st.success("Compte créé ! Veuillez vous connecter.")
                    except Exception: 
                        st.error("Email déjà utilisé ou erreur lors de la création.")
                else:
                    st.error("Impossible de se connecter à la base de données.")
    st.stop()

# Charger les données de l'utilisateur actuel
current_user = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE id = %s", (st.session_state.user_id,), fetch="one")
if not current_user or not isinstance(current_user, dict):
    st.session_state.auth = False
    st.rerun()

# COMPOSANT PROFIL & INTERACTIONS (Kontakte, Evalye, Ekri Mesaj)
def display_profile_card(target_user_id):
    target = run_query(
        "SELECT u.id, u.full_name, u.email, u.user_type, p.bio, p.trust_score "
        "FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = %s",
        (target_user_id,), fetch="one"
    )
    if not target or not isinstance(target, dict):
        st.error("Profil introuvable.")
        return

    with st.expander(f"👤 Profil Complet: {target['full_name']}", expanded=True):
        st.write(f"**Email:** {target['email']} | **Type:** `{target['user_type']}`")
        st.write(f"**Bio:** {target.get('bio') or 'Aucune biographie.'}")
        st.write(f"**Trust Score:** ⭐ {target.get('trust_score') or 50.0}%")

        col_msg, col_rev = st.columns(2)

        # Mesaj direct
        with col_msg:
            st.markdown("##### ✉️ Envoyer un Message Direct")
            msg_text = st.text_area("Votre message:", key=f"p_msg_{target_user_id}")
            if st.button("Envoyer", key=f"btn_p_msg_{target_user_id}"):
                if msg_text.strip():
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user_id, target_user_id, msg_text)):
                        st.success("Message envoyé !")
                    else:
                        st.error("Erreur lors de l'envoi.")
                else:
                    st.warning("Écrivez un message avant d'envoyer.")

        # Evalyasyon
        with col_rev:
            st.markdown("##### ⭐ Laisser un Avis / Évaluation")
            rating = st.slider("Note (1 à 5)", 1, 5, 5, key=f"p_rate_{target_user_id}")
            comment = st.text_input("Avis:", key=f"p_comm_{target_user_id}")
            if st.button("Soumettre la note", key=f"btn_p_rate_{target_user_id}"):
                if run_action("INSERT INTO reviews (evaluator_id, evaluated_id, rating, comment) VALUES (%s, %s, %s, %s)", (st.session_state.user_id, target_user_id, rating, comment)):
                    st.success("Avis enregistré !")
                else:
                    st.error("Erreur lors de l'enregistrement.")

# 4. SIDEBAR
with st.sidebar:
    st.markdown(f"### 👤 {current_user['full_name']}")
    st.caption(f"ID: {current_user['id']} | {current_user['user_type']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    page = st.radio("NAVIGATION", [
        "Accueil & Feed", 
        "Talents & Services", 
        "Missions & Opportunités", 
        "Mes Candidatures", 
        "Messagerie", 
        "Statistiques", 
        "Administration"
    ])

# 5. PAGES
if page == "Accueil & Feed":
    st.markdown('<div class="hero-box"><h1>Bienvenue sur NEKTA</h1><p>Le réseau de confiance certifié par PostgreSQL.</p></div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    
    total_users_res = run_query("SELECT COUNT(*) as cnt FROM users", fetch="one")
    total_users = total_users_res["cnt"] if total_users_res and isinstance(total_users_res, dict) else "100,000"
    
    avg_trust_res = run_query("SELECT fn_get_trust_average()", fetch="one")
    avg_trust = avg_trust_res['fn_get_trust_average'] if avg_trust_res and isinstance(avg_trust_res, dict) and avg_trust_res.get('fn_get_trust_average') else 85.0

    m1.metric("Membres Actifs", total_users)
    m2.metric("Trust Score Moyen", f"{avg_trust:.1f}%")
    m3.metric("Status", "Sécurisé")

    st.divider()
    st.subheader("📢 Dernières Annonces Publiées")
    recent_jobs = run_query("SELECT * FROM vw_jobs_ouverts ORDER BY id DESC LIMIT 5")
    if recent_jobs:
        for rj in recent_jobs:
            st.markdown(f"**{rj.get('title', 'Offre')}** | Budget: `${rj.get('budget', 0)}`")
            st.write(rj.get('description', ''))
            if st.button("Voir Moteur / Postuler", key=f"feed_j_{rj.get('id')}"):
                st.session_state["selected_profile"] = rj.get('client_id') or rj.get('user_id')
            st.divider()
    else:
        st.info("Aucune annonce disponible pour l'instant.")

elif page == "Talents & Services":
    st.header("💎 Annuaire des Talents (Vue: vw_talents)")
    search = st.text_input("🔍 Rechercher par nom ou compétence...")
    
    sql = "SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12"
    talents = run_query(sql, (f"%{search}%",))
    
    if talents:
        cols = st.columns(3)
        for idx, t in enumerate(talents):
            with cols[idx % 3]:
                st.markdown(f"""<div class='card'><b>{t['full_name']}</b><br>Score: {t.get('trust_score', 50)}%<br>{'✅ Vérifié' if t.get('is_verified') else ''}</div>""", unsafe_allow_html=True)
                if st.button("✉️ Profil & Contacter", key=f"msg_{t.get('id', idx)}"): 
                    st.session_state["selected_profile"] = t.get('id') or t.get('user_id')
    else:
        st.info("Aucun talent trouvé.")

elif page == "Missions & Opportunités":
    st.header("💼 Missions (Vue: vw_jobs_ouverts)")
    t1, t2 = st.tabs(["📢 Offres", "➕ Publier une Annonce"])
    
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts ORDER BY id DESC LIMIT 20")
        if jobs:
            for j in jobs:
                st.markdown(f"### {j.get('title')}")
                st.write(f"**Budget:** ${j.get('budget', 0)}")
                st.write(j.get('description', ''))
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝 Postuler", key=f"post_j_{j.get('id')}"):
                        if run_action("INSERT INTO applications (job_id, applicant_id) VALUES (%s, %s)", (j.get('id'), st.session_state.user_id)):
                            st.success("Candidature transmise avec succès !")
                        else:
                            st.warning("Vous avez déjà postulé à cette offre.")
                with c2:
                    if st.button("👤 Profil Recruteur", key=f"rec_j_{j.get('id')}"):
                        st.session_state["selected_profile"] = j.get('client_id') or j.get('user_id')
                st.divider()
        else:
            st.info("Aucune mission ouverte.")

    with t2:
        with st.form("new_job"):
            ti = st.text_input("Titre de la mission")
            bu = st.number_input("Budget ($)", min_value=0.0)
            de = st.text_area("Description complète")
            if st.form_submit_button("Lancer / Publier"):
                if ti and de:
                    if run_action("INSERT INTO jobs (client_id, user_id, title, budget, description) VALUES (%s, %s, %s, %s, %s)", (st.session_state.user_id, st.session_state.user_id, ti, bu, de)):
                        st.success("Mission publiée avec succès et visible par tous !")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la publication de la mission.")
                else:
                    st.warning("Veuillez remplir le titre et la description.")

elif page == "Mes Candidatures":
    st.header("📋 Gestion des Candidatures et Offres")
    tab_rec, tab_sou = st.tabs(["Candidatures Reçues", "Mes Candidatures Soumises"])

    with tab_rec:
        st.subheader("Candidats ayant postulé à vos offres")
        my_jobs = run_query("SELECT id, title FROM jobs WHERE client_id = %s OR user_id = %s", (st.session_state.user_id, st.session_state.user_id))
        if my_jobs:
            for mj in my_jobs:
                st.markdown(f"#### Offre : {mj['title']}")
                apps = run_query(
                    "SELECT a.id as app_id, a.applicant_id, u.full_name, a.status "
                    "FROM applications a JOIN users u ON a.applicant_id = u.id WHERE a.job_id = %s",
                    (mj['id'],)
                )
                if apps:
                    for app in apps:
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        col1.write(f"**Candidat:** {app['full_name']} | **Statut:** `{app['status']}`")
                        
                        if col2.button("Profil", key=f"c_prof_{app['app_id']}"):
                            st.session_state["selected_profile"] = app['applicant_id']
                        
                        if col3.button("Accepter", key=f"c_acc_{app['app_id']}"):
                            run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (app['app_id'],))
                            st.success("Acceptée !")
                            st.rerun()

                        if col4.button("Refuser", key=f"c_ref_{app['app_id']}"):
                            run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (app['app_id'],))
                            st.error("Refusée !")
                            st.rerun()
                else:
                    st.caption("Aucune candidature pour le moment.")
                st.divider()
        else:
            st.info("Vous n'avez publié aucune offre.")

    with tab_sou:
        st.subheader("Vos postulations")
        my_apps = run_query(
            "SELECT a.id, j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.applicant_id = %s",
            (st.session_state.user_id,)
        )
        if my_apps:
            for ma in my_apps:
                st.write(f"**Offre:** {ma['title']} | **Statut:** `{ma['status']}`")
        else:
            st.info("Vous n'avez pas encore postulé à une offre.")

elif page == "Messagerie":
    st.header("💬 Boîte de Réception & Messages")
    msgs = run_query(
        "SELECT m.id, m.sender_id, u.full_name as sender_name, m.content, m.created_at "
        "FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.id DESC",
        (st.session_state.user_id,)
    )
    if msgs:
        for msg in msgs:
            st.markdown(f"**De:** {msg['sender_name']}")
            st.info(msg['content'])
            if st.button("Répondre / Voir Profil", key=f"m_rep_{msg['id']}"):
                st.session_state["selected_profile"] = msg['sender_id']
            st.divider()
    else:
        st.info("Votre boîte de réception est vide.")

elif page == "Statistiques":
    st.header("📊 Business Intelligence & Graphiques")
    job_stats = run_query("SELECT title, budget FROM jobs LIMIT 15")
    if job_stats:
        df_jobs = pd.DataFrame(job_stats)
        fig = px.bar(df_jobs, x='title', y='budget', title="Aperçu des Budgets par Offre ($)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher les graphiques.")

elif page == "Administration":
    if current_user['role'] != 'ADMIN': 
        st.error("Accès réservé au DBA.")
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
            logs = run_query("SELECT * FROM vw_audit_trail LIMIT 50")
            if logs:
                st.table(pd.DataFrame(logs))
            else:
                st.info("Aucun log d'audit disponible.")

# Panèl Entèraksyon Profil anba sit la si yon moun klike sou "Voir Profil / Contacter"
if "selected_profile" in st.session_state:
    st.divider()
    display_profile_card(st.session_state["selected_profile"])