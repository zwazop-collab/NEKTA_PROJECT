import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="NEKTA | Excellence & Confiance",
    page_icon="💼",
    layout="wide"
)

# 2. CONNEXION SÉCURISÉE & OPTIMISÉE (NEON DB)
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except Exception:
        return None

def run_query(query, params=None):
    """Exécute des requêtes SELECT et retourne un DataFrame Pandas"""
    conn = get_db_connection()
    if not conn or conn.closed:
        st.cache_resource.clear()
        conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        return pd.read_sql(query, conn, params=params)
    except Exception:
        return pd.DataFrame()

def run_action(query, params=None):
    """Exécute des requêtes INSERT, UPDATE, DELETE, CALL de façon sécurisée"""
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

# 3. DESIGN CSS (Luxurious, Clean & Responsive)
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0d1117 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; font-weight: 500; }
    
    .hero { 
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 50px 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .card { 
        background: white; padding: 22px; border-radius: 16px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; 
        margin-bottom: 15px; color: #1e293b; transition: all 0.3s ease;
    }
    .card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    
    div[data-testid="stMetric"] {
        background: white; padding: 18px; border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-bottom: 3px solid #1e3a8a;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. INITIALISATION DES VARIABLES DE SESSION
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'user' not in st.session_state: st.session_state['user'] = None

# COMPOSANT : MODAL / CARTE D'INTERACTION PROFIL
def display_profile_card(target_user_id):
    df_target = run_query(
        "SELECT u.id, u.full_name, u.email, u.user_type, p.bio, p.trust_score "
        "FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = %s",
        (int(target_user_id),)
    )
    if df_target.empty:
        st.error("Profil non trouvé.")
        return

    target = df_target.iloc[0].to_dict()
    
    with st.expander(f"👤 Profil Complet : {target['full_name']}", expanded=True):
        st.write(f"**Email:** {target['email']} | **Type:** `{target['user_type']}`")
        st.write(f"**Bio:** {target.get('bio') or 'Aucune biographie renseignée.'}")
        st.write(f"**Trust Score:** ⭐ {target.get('trust_score') or 50.0}%")

        c_msg, c_rate = st.columns(2)

        with c_msg:
            st.markdown("##### ✉️ Envoyer un Message")
            m_text = st.text_area("Message direct :", key=f"p_msg_{target_user_id}")
            if st.button("Envoyer Message", key=f"btn_p_msg_{target_user_id}"):
                if m_text.strip():
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", 
                                  (st.session_state.user['id'], target_user_id, m_text)):
                        st.success("Message transmis avec succès !")
                    else: st.error("Impossible d'envoyer le message.")
                else: st.warning("Veuillez rédiger un texte.")

        with c_rate:
            st.markdown("##### ⭐ Laisser une Évaluation")
            score = st.slider("Note sur 5", 1, 5, 5, key=f"p_rate_{target_user_id}")
            avis = st.text_input("Commentaire / Avis :", key=f"p_comm_{target_user_id}")
            if st.button("Soumettre la Note", key=f"btn_p_rate_{target_user_id}"):
                if run_action("INSERT INTO reviews (evaluator_id, evaluated_id, rating, comment) VALUES (%s, %s, %s, %s)",
                              (st.session_state.user['id'], target_user_id, score, avis)):
                    st.success("Évaluation enregistrée !")
                else: st.error("Erreur d'enregistrement.")

# --- ÉCRAN DE CONNEXION / INSCRIPTION ---
if not st.session_state['auth']:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA GATEWAY</h1><p style='text-align:center;'>Plateforme d'Excellence Professionnelle et Recrutement Certifié</p>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    
    with t1:
        with st.form("l_form"):
            e = st.text_input("Email")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", use_container_width=True):
                sql = "SELECT id, full_name, role, user_type FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s)) LIMIT 1"
                res = run_query(sql, (e, p, p))
                if not res.empty:
                    st.session_state.auth = True
                    st.session_state.user = res.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Identifiants incorrects.")
                
    with t2:
        with st.form("r_form"):
            fn = st.text_input("Nom Complet")
            em = st.text_input("Email")
            pw = st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type de Compte", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("Créer un compte", use_container_width=True):
                if fn and em and pw:
                    if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                        st.success("Compte créé avec succès ! Connectez-vous.")
                    else: st.error("Email déjà utilisé ou erreur système.")
                else: st.warning("Veuillez remplir tous les champs.")
    st.stop()

# --- SI KONEKTE : NAVIGATION & WORKSPACE ---
with st.sidebar:
    if st.session_state.user:
        st.markdown(f"### 👤 {st.session_state.user['full_name']}")
        st.caption(f"Role: **{st.session_state.user['role']}** | {st.session_state.user['user_type']} (ID: {st.session_state.user['id']})")
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()
        
    st.divider()
    menu = st.radio("WORKSPACE", ["🏠 Accueil", "💎 Talents", "💼 Missions & Offres", "📋 Candidatures", "📥 Messagerie", "📊 BI Analytics", "🛡️ Administration"])

# --- PAGES ---

# 1. ACCUEIL
if menu == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence et Confiance</h1><p>Réseau professionnel certifié PostgreSQL à haute performance.</p></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    df_avg = run_query("SELECT fn_get_trust_average() as avg")
    avg_val = df_avg.iloc[0]['avg'] if not df_avg.empty and pd.notnull(df_avg.iloc[0]['avg']) else 85.0
    c1.metric("Confiance Globale", f"{avg_val:.1f}%")
    
    df_msg = run_query("SELECT fn_total_messages(%s) as cnt", (st.session_state.user['id'],))
    msg_cnt = df_msg.iloc[0]['cnt'] if not df_msg.empty and pd.notnull(df_msg.iloc[0]['cnt']) else 0
    c2.metric("Messages Reçus", msg_cnt)
    
    df_jobs_cnt = run_query("SELECT COUNT(*) as cnt FROM jobs")
    jobs_cnt = df_jobs_cnt.iloc[0]['cnt'] if not df_jobs_cnt.empty else 0
    c3.metric("Missions Ouvertes", jobs_cnt)

    st.divider()
    st.subheader("🔥 Offres Récentes à la Une")
    recent_jobs = run_query("SELECT * FROM vw_jobs_ouverts ORDER BY id DESC LIMIT 4")
    if not recent_jobs.empty:
        for _, r in recent_jobs.iterrows():
            st.markdown(f"**{r.get('title', 'Offre')}** | Budget: `${r.get('budget', 0)}`")
            st.write(r.get('description', ''))
            st.divider()
    else:
        st.info("Aucune offre récente publiée.")

# 2. TALENTS
elif menu == "💎 Talents":
    st.title("💎 Réseau des Talents")
    search = st.text_input("🔍 Rechercher par nom ou compétence...", placeholder="Ex: Jean, Developer, Designer...")
    
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{search}%',))
    
    if not df.empty:
        cols = st.columns(3)
        for i, r in df.iterrows():
            with cols[i % 3]:
                st.markdown(f"<div class='card'><b>{r['full_name']}</b><br>Trust Score: ⭐ {r.get('trust_score', 50)}%</div>", unsafe_allow_html=True)
                target_user_id = r.get('id') or r.get('user_id')
                if st.button("👤 Voir Profil & Contacter", key=f"t_btn_{i}_{target_user_id}"):
                    st.session_state["selected_profile"] = target_user_id
    else:
        st.info("Aucun talent ne correspond à votre recherche.")

# 3. MISSIONS & OFFRES
elif menu == "💼 Missions & Offres":
    st.title("💼 Missions & Opportunités")
    t1, t2 = st.tabs(["📢 Explorer les Offres", "➕ Publier une Nouvelle Mission"])
    
    with t1:
        search_j = st.text_input("🔍 Filtre rapide par titre...", key="search_job_key")
        jobs_df = run_query("SELECT * FROM vw_jobs_ouverts WHERE title ILIKE %s ORDER BY id DESC LIMIT 50", (f'%{search_j}%',))
        
        if not jobs_df.empty:
            for _, r in jobs_df.iterrows():
                st.markdown(f"### {r['title']}")
                st.write(f"**Budget proposé:** `${r.get('budget', 0)}`")
                st.write(r.get('description', ''))
                
                col_act1, col_act2 = st.columns([1, 4])
                with col_act1:
                    if st.button("📝 Postuler", key=f"post_job_{r['id']}"):
                        if run_action("INSERT INTO applications (job_id, professional_id, applicant_id) VALUES (%s, %s, %s)", 
                                      (int(r['id']), st.session_state.user['id'], st.session_state.user['id'])):
                            st.success("Candidature envoyée !")
                        else:
                            st.warning("Vous avez déjà postulé ou une erreur s'est produite.")
                with col_act2:
                    client_id = r.get('client_id') or r.get('user_id')
                    if client_id and st.button("👤 Contact Recruteur", key=f"rec_job_{r['id']}"):
                        st.session_state["selected_profile"] = client_id
                st.divider()
        else:
            st.info("Aucune mission disponible.")

    with t2:
        with st.form("new_j_form"):
            ti = st.text_input("Titre du poste / projet")
            bu = st.number_input("Budget global ($)", min_value=0.0, step=10.0)
            de = st.text_area("Cahier des charges / Description")
            if st.form_submit_button("Publier Immédiatement", use_container_width=True):
                if ti and de:
                    if run_action("INSERT INTO jobs (client_id, user_id, title, budget, description) VALUES (%s, %s, %s, %s, %s)", 
                                  (st.session_state.user['id'], st.session_state.user['id'], ti, bu, de)):
                        st.success("Mission publiée avec succès !")
                        st.rerun()
                    else: st.error("Erreur lors de la publication.")
                else: st.warning("Veuillez compléter le titre et la description.")

# 4. CANDIDATURES
elif menu == "📋 Candidatures":
    st.title("📋 Suivi des Candidatures")
    tab_recu, tab_post = st.tabs(["📥 Candidatures Reçues sur vos Offres", "📤 Vos Postulations"])
    
    with tab_recu:
        apps = run_query(
            "SELECT a.id as app_id, u.id as applicant_id, u.full_name, j.title, a.status "
            "FROM applications a "
            "JOIN jobs j ON a.job_id = j.id "
            "JOIN users u ON (a.professional_id = u.id OR a.applicant_id = u.id) "
            "WHERE (j.client_id = %s OR j.user_id = %s) AND a.status = 'PENDING'",
            (st.session_state.user['id'], st.session_state.user['id'])
        )
        if not apps.empty:
            for _, r in apps.iterrows():
                col_info, col_p, col_acc, col_ref = st.columns([4, 2, 2, 2])
                col_info.write(f"**{r['full_name']}** -> *{r['title']}*")
                
                if col_p.button("Profil", key=f"p_app_{r['app_id']}"):
                    st.session_state["selected_profile"] = r['applicant_id']
                    
                if col_acc.button("Accepter", key=f"acc_app_{r['app_id']}"):
                    if run_action("CALL sp_accepter_candidature(%s)", (int(r['app_id']),)):
                        st.success("Candidature Acceptée !")
                        st.rerun()
                    else:
                        run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (int(r['app_id']),))
                        st.success("Statut mis à jour : Acceptée !")
                        st.rerun()
                        
                if col_ref.button("Refuser", key=f"ref_app_{r['app_id']}"):
                    run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (int(r['app_id']),))
                    st.error("Statut mis à jour : Refusée !")
                    st.rerun()
                st.divider()
        else:
            st.info("Aucune candidature en attente de validation.")

    with tab_post:
        my_apps = run_query(
            "SELECT a.id, j.title, a.status FROM applications a "
            "JOIN jobs j ON a.job_id = j.id "
            "WHERE a.professional_id = %s OR a.applicant_id = %s",
            (st.session_state.user['id'], st.session_state.user['id'])
        )
        if not my_apps.empty:
            for _, r in my_apps.iterrows():
                st.write(f"**Offre:** {r['title']} | **Statut:** `{r['status']}`")
        else:
            st.info("Vous n'avez soumis aucune candidature.")

# 5. MESSAGERIE
elif menu == "📥 Messagerie":
    st.title("📥 Boîte de Réception")
    msgs = run_query(
        "SELECT m.id, m.sender_id, u.full_name as de, m.content, m.created_at, m.sent_at "
        "FROM messages m JOIN users u ON m.sender_id = u.id "
        "WHERE m.receiver_id = %s ORDER BY m.id DESC",
        (st.session_state.user['id'],)
    )
    
    if msgs.empty:
        st.info("Votre boîte de réception est vide.")
    else:
        for _, m in msgs.iterrows():
            st.markdown(f"<div class='card'><b>De: {m['de']}</b><p>{m['content']}</p></div>", unsafe_allow_html=True)
            if st.button(f"Répondre à {m['de']}", key=f"reply_{m['id']}"):
                st.session_state["selected_profile"] = m['sender_id']

# 6. BI ANALYTICS
elif menu == "📊 BI Analytics":
    st.title("📊 Intelligence des Données & Statistiques")
    df_u = run_query("SELECT user_type, COUNT(*) as nombre FROM users GROUP BY user_type")
    
    if not df_u.empty:
        fig = px.pie(df_u, values='nombre', names='user_type', title="Répartition des Utilisateurs par Type", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour le graphique.")

# 7. ADMINISTRATION (DBA)
elif menu == "🛡️ Administration":
    if st.session_state.user['role'] != 'ADMIN':
        st.error("Accès strictement réservé aux Administrateurs et DBA.")
    else:
        st.title("🛡️ Panneau de Contrôle DBA")
        search_adm = st.text_input("🔍 Recherche rapide par ID ou Email")
        
        if search_adm:
            df_adm = run_query("SELECT id, full_name, email, role, user_type FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100", (f'%{search_adm}%', search_adm))
        else:
            df_adm = run_query("SELECT id, full_name, email, role, user_type FROM users ORDER BY id DESC LIMIT 100")
            
        st.dataframe(df_adm, use_container_width=True)
        
        st.write("### 📜 Audit Logs (Vue : vw_audit_trail)")
        df_audit = run_query("SELECT * FROM vw_audit_trail LIMIT 50")
        if not df_audit.empty:
            st.dataframe(df_audit, use_container_width=True)
        else:
            st.info("Aucun log d'audit disponible.")

# ACCÈS PROFIL SÉLECTIONNÉ (PANEL FLOTTANT D'INTERACTION)
if "selected_profile" in st.session_state:
    st.divider()
    display_profile_card(st.session_state["selected_profile"])