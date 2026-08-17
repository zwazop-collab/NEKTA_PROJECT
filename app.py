import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd

# =============================================================================
# 1. CONFIGURATION PAGE
# =============================================================================
st.set_page_config(
    page_title="NEKTA - Plateforme de Talents & Missions",
    page_icon="💼",
    layout="wide"
)

# =============================================================================
# 2. CONNEXION SÉCURISÉE & OPTIMISÉE (NEON DB)
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DB_URL)

# Maintien de la session utilisateur
if "user" not in st.session_state:
    st.session_state.user = None

# =============================================================================
# 3. SYSTÈME D'AUTHENTIFICATION (SÉCURISÉ AVEC BCRYPT / PGCRYPTO)
# =============================================================================
def login_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT id, full_name, email, role, user_type 
        FROM users 
        WHERE email = %s AND password_hash = crypt(%s, password_hash);
    """
    cur.execute(query, (email, password))
    user = cur.fetchone()
    
    if user:
        cur.execute("INSERT INTO login_logs (user_id) VALUES (%s);", (user['id'],))
        conn.commit()
    
    cur.close()
    conn.close()
    return user

def logout_user():
    st.session_state.user = None
    st.rerun()

# Sidebar - Connexion / Déconnexion
st.sidebar.title("🔐 Authentification")
if st.session_state.user is None:
    st.sidebar.subheader("Se connecter")
    email_input = st.sidebar.text_input("Email")
    password_input = st.sidebar.text_input("Mot de passe", type="password")
    if st.sidebar.button("Connexion"):
        auth_user = login_user(email_input, password_input)
        if auth_user:
            st.session_state.user = auth_user
            st.sidebar.success(f"Bienvenue {auth_user['full_name']}!")
            st.rerun()
        else:
            st.sidebar.error("Email ou mot de passe incorrect.")
else:
    st.sidebar.write(f"👤 **{st.session_state.user['full_name']}**")
    st.sidebar.caption(f"Rôle: {st.session_state.user['role']} | Type: {st.session_state.user['user_type']}")
    if st.sidebar.button("Déconnexion"):
        logout_user()

st.sidebar.markdown("---")

# Navigation Principale
menu = [
    "🏠 Accueil", 
    "👥 Talents", 
    "👤 Mon Profil", 
    "🎯 Missions", 
    "➕ Publier", 
    "📑 Candidatures", 
    "💬 Messagerie", 
    "📅 Événements & Formations", 
    "📊 Statistiques", 
    "⚙️ Administration DBA"
]
choice = st.sidebar.radio("Navigation", menu)

# =============================================================================
# PAJ 1: 🏠 ACCUEIL
# =============================================================================
if choice == "🏠 Accueil":
    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); padding: 35px; border-radius: 12px; color: white; text-align: center;">
            <h1 style="color: white; margin-bottom: 5px;">🚀 Bienvenue sur NEKTA</h1>
            <p style="font-size: 1.2em;">La plateforme haïtienne de mise en relation entre étudiants, professionnels et entreprises.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM users WHERE user_type IN ('STUDENT', 'PROFESSIONAL');")
    total_talents = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'OPEN';")
    total_jobs = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applications;")
    total_apps = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM messages;")
    total_msgs = cur.fetchone()[0]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Talents Inscrits", total_talents)
    col2.metric("Missions Ouvertes", total_jobs)
    col3.metric("Candidatures Soumises", total_apps)
    col4.metric("Messages Échangés", total_msgs)
    
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🌟 Top Talents (Trust Score Élevé)")
        df_talents = pd.read_sql("SELECT full_name, user_type, trust_score FROM vw_talents ORDER BY trust_score DESC LIMIT 5;", conn)
        st.dataframe(df_talents, use_container_width=True)
        
    with c2:
        st.subheader("🔥 Dernières Offres De Mission")
        df_jobs = pd.read_sql("SELECT title, budget, client_name, created_at FROM vw_jobs_ouverts ORDER BY created_at DESC LIMIT 5;", conn)
        st.dataframe(df_jobs, use_container_width=True)
        
    conn.close()

# =============================================================================
# PAJ 2: 👥 TALENTS
# =============================================================================
elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    
    c_search1, c_search2, c_search3 = st.columns([2, 2, 1])
    search_name = c_search1.text_input("Rechercher par nom")
    search_type = c_search2.selectbox("Type d'utilisateur", ["Tous", "STUDENT", "PROFESSIONAL"])
    min_trust = c_search3.slider("Trust Score Min", 0, 100, 50)
    
    page_size = 10
    page_number = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page_number - 1) * page_size
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT user_id, full_name, user_type, bio, trust_score 
        FROM vw_talents 
        WHERE trust_score >= %s AND full_name ILIKE %s
    """
    params = [min_trust, f"%{search_name}%"]
    
    if search_type != "Tous":
        query += " AND user_type = %s"
        params.append(search_type)
        
    query += " ORDER BY trust_score DESC LIMIT %s OFFSET %s;"
    params.extend([page_size, offset])
    
    cur.execute(query, tuple(params))
    talents = cur.fetchall()
    conn.close()
    
    for t in talents:
        with st.container():
            st.markdown(f"### {t['full_name']} `({t['user_type']})`")
            st.caption(f"⭐ **Trust Score:** {t['trust_score']}/100")
            st.write(t['bio'] or "Aucune biographie fournie.")
            if st.button(f"Contacter {t['full_name']}", key=f"btn_contact_{t['user_id']}"):
                st.info("Rendez-vous dans l'onglet **Messagerie** pour envoyer un message.")
            st.markdown("---")

# =============================================================================
# PAJ 3: 👤 MON PROFIL
# =============================================================================
elif choice == "👤 Mon Profil":
    if not st.session_state.user:
        st.warning("Veuillez vous connecter pour voir votre profil.")
    else:
        u_id = st.session_state.user['id']
        st.title("👤 Mon Profil Personnel")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT u.full_name, u.email, p.bio, p.trust_score FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.id = %s;", (u_id,))
        profile = cur.fetchone()
        
        col_prof1, col_prof2 = st.columns([1, 2])
        with col_prof1:
            st.metric("Trust Score", f"{profile['trust_score']}/100")
            st.file_uploader("Upload Foto (JPG/PNG)", type=["jpg", "png"])
            st.file_uploader("Téléverser CV (PDF)", type=["pdf"])
            
        with col_prof2:
            new_name = st.text_input("Nom Complet", value=profile['full_name'])
            new_bio = st.text_area("Ma Bio / Compétences", value=profile['bio'] or "")
            if st.button("Mettre à jour le profil"):
                cur.execute("UPDATE users SET full_name = %s WHERE id = %s;", (new_name, u_id))
                cur.execute("UPDATE profiles SET bio = %s, updated_at = NOW() WHERE user_id = %s;", (new_bio, u_id))
                conn.commit()
                st.success("Profil mis à jour avec succès!")
                
        conn.close()

# =============================================================================
# PAJ 4: 🎯 MISSIONS
# =============================================================================
elif choice == "🎯 Missions":
    st.title("🎯 Offres de Missions Disponibles")
    
    col_f1, col_f2 = st.columns(2)
    min_budget = col_f1.number_input("Budget Minimum ($)", min_value=0, value=0)
    search_title = col_f2.text_input("Mot clé (titre/description)")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
        SELECT id, client_id, title, description, budget, client_name, created_at 
        FROM vw_jobs_ouverts 
        WHERE budget >= %s AND (title ILIKE %s OR description ILIKE %s)
        ORDER BY created_at DESC LIMIT 20;
    """
    cur.execute(query, (min_budget, f"%{search_title}%", f"%{search_title}%"))
    jobs = cur.fetchall()
    
    for j in jobs:
        with st.expander(f"📌 {j['title']} — ${j['budget']}"):
            st.write(f"**Client:** {j['client_name']}")
            st.write(j['description'])
            if st.session_state.user:
                if st.button("Postuler à cette mission", key=f"app_{j['id']}"):
                    try:
                        cur.execute("""
                            INSERT INTO applications (job_id, professional_id, applicant_id) 
                            VALUES (%s, %s, %s);
                        """, (j['id'], st.session_state.user['id'], st.session_state.user['id']))
                        conn.commit()
                        st.success("Candidature envoyée !")
                    except Exception:
                        conn.rollback()
                        st.error("Vous avez déjà postulé à cette offre.")
            else:
                st.info("Connectez-vous pour postuler.")
    conn.close()

# =============================================================================
# PAJ 5: ➕ PUBLIER
# =============================================================================
elif choice == "➕ Publier":
    if not st.session_state.user:
        st.warning("Veuillez vous connecter pour publier.")
    else:
        st.title("➕ Publier du Contenu")
        pub_type = st.radio("Que voulez-vous publier ?", ["Nouvelle Mission", "Nouvel Événement / Formation"])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if pub_type == "Nouvelle Mission":
            title = st.text_input("Titre de la mission")
            description = st.text_area("Description détaillée")
            budget = st.number_input("Budget ($)", min_value=10.0, step=10.0)
            
            if st.button("Publier la mission"):
                cur.execute("""
                    INSERT INTO jobs (client_id, user_id, title, description, budget) 
                    VALUES (%s, %s, %s, %s, %s);
                """, (st.session_state.user['id'], st.session_state.user['id'], title, description, budget))
                conn.commit()
                st.success("Mission publiée avec succès!")
                
        else:
            ev_title = st.text_input("Titre de l'événement / formation")
            ev_desc = st.text_area("Description")
            ev_type = st.selectbox("Type", ["FORMATION", "WORKSHOP", "NETWORKING"])
            ev_date = st.date_input("Date")
            
            if st.button("Publier l'événement"):
                cur.execute("""
                    INSERT INTO events (title, description, event_type, event_date) 
                    VALUES (%s, %s, %s, %s);
                """, (ev_title, ev_desc, ev_type, ev_date))
                conn.commit()
                st.success("Événement enregistré!")
                
        conn.close()

# =============================================================================
# PAJ 6: 📑 CANDIDATURES
# =============================================================================
elif choice == "📑 Candidatures":
    if not st.session_state.user:
        st.warning("Veuillez vous connecter pour gérer les candidatures.")
    else:
        u_id = st.session_state.user['id']
        st.title("📑 Gestion des Candidatures")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        tab1, tab2 = st.tabs(["Mes Candidatures Soumises", "Candidatures Reçues sur Mes Offres"])
        
        with tab1:
            cur.execute("""
                SELECT a.id, j.title, a.status, a.applied_at 
                FROM applications a 
                JOIN jobs j ON a.job_id = j.id 
                WHERE a.professional_id = %s;
            """, (u_id,))
            my_apps = cur.fetchall()
            st.dataframe(pd.DataFrame(my_apps), use_container_width=True)
            
        with tab2:
            cur.execute("""
                SELECT a.id AS app_id, j.title, u.full_name AS candidat, a.status 
                FROM applications a 
                JOIN jobs j ON a.job_id = j.id 
                JOIN users u ON a.professional_id = u.id 
                WHERE j.client_id = %s;
            """, (u_id,))
            received_apps = cur.fetchall()
            
            for ra in received_apps:
                c_a1, c_a2, c_a3 = st.columns([3, 1, 1])
                c_a1.write(f"**{ra['candidat']}** sur *{ra['title']}* (`{ra['status']}`)")
                if ra['status'] == 'PENDING':
                    if c_a2.button("Accepter", key=f"acc_{ra['app_id']}"):
                        cur.execute("CALL sp_accepter_candidature(%s);", (ra['app_id'],))
                        conn.commit()
                        st.rerun()
                    if c_a3.button("Refuser", key=f"ref_{ra['app_id']}"):
                        cur.execute("UPDATE applications SET status='REJECTED' WHERE id=%s;", (ra['app_id'],))
                        conn.commit()
                        st.rerun()
        conn.close()

# =============================================================================
# PAJ 7: 💬 MESSAGERIE
# =============================================================================
elif choice == "💬 Messagerie":
    if not st.session_state.user:
        st.warning("Veuillez vous connecter pour accéder à vos messages.")
    else:
        u_id = st.session_state.user['id']
        st.title("💬 Messagerie Intégrée")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT id, full_name FROM users WHERE id <> %s ORDER BY full_name LIMIT 50;", (u_id,))
        users_list = cur.fetchall()
        recipient_map = {u['full_name']: u['id'] for u in users_list}
        
        if recipient_map:
            selected_recipient = st.selectbox("Sélectionner un destinataire", list(recipient_map.keys()))
            dest_id = recipient_map[selected_recipient]
            
            cur.execute("""
                SELECT sender_id, content, sent_at 
                FROM messages 
                WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
                ORDER BY sent_at ASC;
            """, (u_id, dest_id, dest_id, u_id))
            messages_chat = cur.fetchall()
            
            for m in messages_chat:
                sender_label = "Moi" if m['sender_id'] == u_id else selected_recipient
                st.text(f"[{m['sent_at'].strftime('%H:%M')}] {sender_label}: {m['content']}")
                
            msg_text = st.text_input("Votre message...")
            if st.button("Envoyer Message"):
                if msg_text.strip():
                    cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s);", (u_id, dest_id, msg_text))
                    conn.commit()
                    st.rerun()
        else:
            st.info("Aucun utilisateur disponible pour discuter.")
        conn.close()

# =============================================================================
# PAJ 8: 📅 ÉVÉNEMENTS & FORMATIONS
# =============================================================================
elif choice == "📅 Événements & Formations":
    st.title("📅 Formations & Événements à venir")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM events ORDER BY event_date ASC;")
    events = cur.fetchall()
    conn.close()
    
    for e in events:
        st.subheader(f"[{e['event_type']}] {e['title']}")
        st.caption(f"📅 Date: {e['event_date']} | Lieu: {e['location']}")
        st.write(e['description'])
        if st.button("S'inscrire à l'événement", key=f"ev_{e['id']}"):
            if st.session_state.user:
                st.success("Inscription enregistrée!")
            else:
                st.error("Veuillez vous connecter pour vous inscrire.")
        st.markdown("---")

# =============================================================================
# PAJ 9: 📊 STATISTIQUES (PLOTLY EXCLUSIF)
# =============================================================================
elif choice == "📊 Statistiques":
    st.title("📊 Tableaux de Bord analytiques (Plotly)")
    
    conn = get_db_connection()
    
    df_users = pd.read_sql("SELECT user_type, COUNT(*) as count FROM users GROUP BY user_type;", conn)
    fig_users = px.pie(df_users, values='count', names='user_type', title="Répartition des Utilisateurs par Catégorie", hole=0.4)
    st.plotly_chart(fig_users, use_container_width=True)
    
    df_scores = pd.read_sql("SELECT trust_score FROM profiles;", conn)
    fig_scores = px.histogram(df_scores, x='trust_score', nbins=20, title="Distribution des Trust Scores", color_discrete_sequence=['#2a5298'])
    st.plotly_chart(fig_scores, use_container_width=True)
    
    conn.close()

# =============================================================================
# PAJ 10: ⚙️ ADMINISTRATION DBA
# =============================================================================
elif choice == "⚙️ Administration DBA":
    if not st.session_state.user or st.session_state.user['role'] != 'ADMIN':
        st.error("⛔ Accès refusé. Cette section est réservée aux administrateurs de la base de données.")
    else:
        st.title("⚙️ Dashboard DBA & Audit Logs")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        st.subheader("📋 Logs d'Audit du Système (audit_logs)")
        df_audit = pd.read_sql("SELECT * FROM vw_audit_trail LIMIT 50;", conn)
        st.dataframe(df_audit, use_container_width=True)
        
        st.subheader("🔑 Connexions Récents (login_logs)")
        df_login = pd.read_sql("SELECT l.id, u.email, l.login_time FROM login_logs l JOIN users u ON l.user_id = u.id ORDER BY l.login_time DESC LIMIT 20;", conn)
        st.dataframe(df_login, use_container_width=True)
        
        conn.close()