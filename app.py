import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd

# =============================================================================
# 1. CONFIGURATION PAGE & STYLES CUSTOM
# =============================================================================
st.set_page_config(
    page_title="NEKTA - Plateforme de Talents & Missions",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
    <style>
        .stButton>button {
            border-radius: 8px;
            font-weight: bold;
        }
        .main-header {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            padding: 40px;
            border-radius: 15px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            margin-bottom: 25px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2027 0%, #203a43 100%);
            color: white;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CONNEXION SÉCURISÉE (NEON DB)
# =============================================================================
DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        return None

if "user" not in st.session_state:
    st.session_state.user = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🏠 Accueil"

if "msg_recipient_id" not in st.session_state:
    st.session_state.msg_recipient_id = None

# =============================================================================
# 3. FONKSYON AUTHENTIFICATION & INSCRIPTION
# =============================================================================
def login_user(email, password):
    conn = get_db_connection()
    if not conn:
        st.error("⚠️ Impossible de se connecter à la base de données Neon.")
        return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT id, full_name, email, role, user_type 
            FROM users 
            WHERE email = %s AND password_hash = crypt(%s, password_hash);
        """
        cur.execute(query, (email, password))
        user = cur.fetchone()
        
        if user:
            try:
                cur.execute("INSERT INTO login_logs (user_id) VALUES (%s);", (user['id'],))
                conn.commit()
            except Exception:
                conn.rollback()
        
        cur.close()
        conn.close()
        return user
    except Exception as e:
        st.error(f"⚠️ Erreur d'authentification: {e}")
        if conn:
            conn.close()
        return None

def register_user(full_name, email, password, user_type):
    conn = get_db_connection()
    if not conn:
        st.error("⚠️ Impossible de se connecter à la base de données.")
        return False
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO users (full_name, email, password_hash, role, user_type)
            VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'USER', %s)
            RETURNING id;
        """
        cur.execute(query, (full_name, email, password, user_type))
        new_user_id = cur.fetchone()[0]
        
        try:
            cur.execute("INSERT INTO profiles (user_id, bio, trust_score) VALUES (%s, %s, %s);", (new_user_id, 'Nouveau membre NEKTA', 50))
        except Exception:
            pass
            
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        st.error(f"⚠️ Erreur lors de l'inscription : {e}. Assurez-vous que l'extension pgcrypto est activée.")
        return False

def logout_user():
    st.session_state.user = None
    st.rerun()

# =============================================================================
# 4. LOGIN AK INSCRIPTION
# =============================================================================
if st.session_state.user is None:
    st.markdown("""
        <div class="main-header">
            <h1 style="color: white; margin-bottom: 0px;">🌐 NEKTA SYSTEM</h1>
            <p style="font-size: 1.1em; opacity: 0.9;">Portail d'Accès Sécurisé & Plateforme de Talents</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_left, col_auth, col_right = st.columns([1, 2, 1])
    
    with col_auth:
        tab_login, tab_signup = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab_login:
            st.markdown("### 🔑 Accéder à votre compte")
            email_input = st.text_input("Adresse Email", key="login_email", placeholder="exemple@nekta.ht")
            password_input = st.text_input("Mot de passe", type="password", key="login_pass")
            
            if st.button("Se connecter 🚀", type="primary", use_container_width=True):
                if email_input and password_input:
                    auth_user = login_user(email_input, password_input)
                    if auth_user:
                        st.session_state.user = auth_user
                        st.success(f"Bienvenue {auth_user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects ou compte inexistant.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

        with tab_signup:
            st.markdown("### 📋 Créer un nouveau compte")
            reg_name = st.text_input("Nom Complet", key="reg_name", placeholder="Jean Baptiste")
            reg_email = st.text_input("Adresse Email", key="reg_email", placeholder="jean@example.com")
            reg_pass = st.text_input("Mot de passe", type="password", key="reg_pass")
            reg_type = st.selectbox("Type de compte", ["STUDENT", "PROFESSIONAL"], key="reg_type")
            
            if st.button("S'inscrire maintenant ✨", use_container_width=True):
                if reg_name and reg_email and reg_pass:
                    if register_user(reg_name, reg_email, reg_pass, reg_type):
                        st.success("🎉 Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

    st.stop()

# =============================================================================
# 5. APPLICATION PRINCIPALE
# =============================================================================
st.sidebar.title("💼 NEKTA Platform")
st.sidebar.write(f"👤 **{st.session_state.user['full_name']}**")
st.sidebar.caption(f"Rôle: `{st.session_state.user['role']}` | Type: `{st.session_state.user['user_type']}`")
if st.sidebar.button("Déconnexion 🚪", use_container_width=True):
    logout_user()

st.sidebar.markdown("---")

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

if st.session_state.active_tab not in menu:
    st.session_state.active_tab = "🏠 Accueil"

choice = st.sidebar.radio("Navigation", menu, index=menu.index(st.session_state.active_tab))
st.session_state.active_tab = choice

# -----------------------------------------------------------------------------
# PAJ 1: 🏠 ACCUEIL
# -----------------------------------------------------------------------------
if choice == "🏠 Accueil":
    st.markdown("""
        <div class="main-header">
            <h1 style="color: white; margin-bottom: 5px;">🚀 Bienvenue sur NEKTA</h1>
            <p style="font-size: 1.2em;">La plateforme haïtienne de mise en relation entre étudiants, professionnels et entreprises.</p>
        </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            def get_count(query):
                try:
                    cur.execute(query)
                    return cur.fetchone()[0]
                except Exception:
                    conn.rollback()
                    return 0

            total_talents = get_count("SELECT COUNT(*) FROM users WHERE user_type IN ('STUDENT', 'PROFESSIONAL');")
            total_jobs = get_count("SELECT COUNT(*) FROM jobs WHERE status = 'OPEN';")
            total_apps = get_count("SELECT COUNT(*) FROM applications;")
            total_msgs = get_count("SELECT COUNT(*) FROM messages;")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Talents Inscrits", total_talents)
            col2.metric("Missions Ouvertes", total_jobs)
            col3.metric("Candidatures Soumises", total_apps)
            col4.metric("Messages Échangés", total_msgs)
            
            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🌟 Top Talents")
                try:
                    df_talents = pd.read_sql("SELECT full_name, user_type, trust_score FROM vw_talents ORDER BY trust_score DESC LIMIT 5;", conn)
                    st.dataframe(df_talents, use_container_width=True)
                except Exception:
                    conn.rollback()
                    st.info("Information indisponible.")
                
            with c2:
                st.subheader("🔥 Dernières Offres De Mission")
                try:
                    df_jobs = pd.read_sql("SELECT title, budget, client_name, created_at FROM vw_jobs_ouverts ORDER BY created_at DESC LIMIT 5;", conn)
                    st.dataframe(df_jobs, use_container_width=True)
                except Exception:
                    conn.rollback()
                    st.info("Information indisponible.")
            conn.close()
        except Exception:
            st.warning("Erreur d'affichage de l'accueil.")

# -----------------------------------------------------------------------------
# PAJ 2: 👥 TALENTS
# -----------------------------------------------------------------------------
elif choice == "👥 Talents":
    st.title("👥 Annuaire des Talents")
    
    c_search1, c_search2, c_search3 = st.columns([2, 2, 1])
    search_name = c_search1.text_input("Rechercher par nom")
    search_type = c_search2.selectbox("Type d'utilisateur", ["Tous", "STUDENT", "PROFESSIONAL"])
    min_trust = c_search3.slider("Trust Score Min", 0, 100, 0)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            query = "SELECT user_id, full_name, user_type, bio, trust_score FROM vw_talents WHERE trust_score >= %s AND full_name ILIKE %s"
            params = [min_trust, f"%{search_name}%"]
            
            if search_type != "Tous":
                query += " AND user_type = %s"
                params.append(search_type)
                
            query += " ORDER BY trust_score DESC LIMIT 20;"
            
            cur.execute(query, tuple(params))
            talents = cur.fetchall()
            
            if talents:
                for t in talents:
                    with st.container():
                        st.markdown(f"### {t['full_name']} `({t['user_type']})`")
                        st.caption(f"⭐ **Trust Score:** {t['trust_score'] or 0}/100")
                        st.write(t['bio'] or "Aucune biographie.")
                        
                        col_btn1, col_btn2 = st.columns([1, 2])
                        with col_btn1:
                            if st.button(f"💬 Contacter {t['full_name']}", key=f"contact_{t['user_id']}"):
                                st.session_state.msg_recipient_id = t['user_id']
                                st.session_state.active_tab = "💬 Messagerie"
                                st.rerun()
                                
                        with col_btn2:
                            with st.expander(f"⭐ Évaluer {t['full_name']}"):
                                new_score = st.slider("Note (0 à 100)", 0, 100, int(t['trust_score'] or 50), key=f"rate_val_{t['user_id']}")
                                if st.button("Enregistrer", key=f"rate_btn_{t['user_id']}"):
                                    try:
                                        cur.execute("UPDATE profiles SET trust_score = %s WHERE user_id = %s;", (new_score, t['user_id']))
                                        conn.commit()
                                        st.success("Note enregistrée!")
                                        st.rerun()
                                    except Exception as ex:
                                        conn.rollback()
                                        st.error(f"Erreur: {ex}")
                        st.markdown("---")
            else:
                st.info("Aucun talent trouvé.")
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Erreur d'accès aux talents: {e}")

# -----------------------------------------------------------------------------
# PAJ 3: 👤 MON PROFIL
# -----------------------------------------------------------------------------
elif choice == "👤 Mon Profil":
    u_id = st.session_state.user['id']
    st.title("👤 Mon Profil Personnel")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT u.full_name, u.email, p.bio, p.trust_score FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = %s;", (u_id,))
            profile = cur.fetchone()
            
            col_prof1, col_prof2 = st.columns([1, 2])
            with col_prof1:
                st.metric("Trust Score", f"{profile['trust_score'] if profile and profile.get('trust_score') else 0}/100")
                
            with col_prof2:
                new_name = st.text_input("Nom Complet", value=profile['full_name'] if profile else "")
                new_bio = st.text_area("Ma Bio / Compétences", value=profile['bio'] if profile and profile.get('bio') else "")
                if st.button("Mettre à jour"):
                    cur.execute("UPDATE users SET full_name = %s WHERE id = %s;", (new_name, u_id))
                    cur.execute("INSERT INTO profiles (user_id, bio, updated_at) VALUES (%s, %s, NOW()) ON CONFLICT (user_id) DO UPDATE SET bio = EXCLUDED.bio, updated_at = NOW();", (u_id, new_bio))
                    conn.commit()
                    st.success("Profil mis à jour!")
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Erreur profil: {e}")

# -----------------------------------------------------------------------------
# PAJ 4: 🎯 MISSIONS
# -----------------------------------------------------------------------------
elif choice == "🎯 Missions":
    st.title("🎯 Offres de Missions Disponibles")
    
    col_f1, col_f2 = st.columns(2)
    min_budget = col_f1.number_input("Budget Minimum ($)", min_value=0, value=0)
    search_title = col_f2.text_input("Mot clé")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            query = """
                SELECT id, client_id, title, description, budget, client_name, created_at 
                FROM vw_jobs_ouverts 
                WHERE budget >= %s AND (title ILIKE %s OR description ILIKE %s)
                ORDER BY created_at DESC LIMIT 20;
            """
            cur.execute(query, (min_budget, f"%{search_title}%", f"%{search_title}%"))
            jobs = cur.fetchall()
            
            if jobs:
                for j in jobs:
                    with st.expander(f"📌 {j['title']} — ${j['budget']}"):
                        st.write(f"**Client:** {j['client_name']}")
                        st.write(j['description'])
                        if st.button("Postuler", key=f"app_{j['id']}"):
                            try:
                                cur.execute("INSERT INTO applications (job_id, professional_id, applicant_id) VALUES (%s, %s, %s);", (j['id'], st.session_state.user['id'], st.session_state.user['id']))
                                conn.commit()
                                st.success("Candidature envoyée !")
                            except Exception:
                                conn.rollback()
                                st.error("Déjà postulé ou erreur.")
            else:
                st.info("Aucune mission disponible.")
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du chargement des missions: {e}")

# -----------------------------------------------------------------------------
# PAJ 5: ➕ PUBLIER
# -----------------------------------------------------------------------------
elif choice == "➕ Publier":
    st.title("➕ Publier une offre ou un événement")
    pub_type = st.radio("Type", ["Nouvelle Mission", "Nouvel Événement"])
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            if pub_type == "Nouvelle Mission":
                title = st.text_input("Titre de la mission")
                description = st.text_area("Description")
                budget = st.number_input("Budget ($)", min_value=10.0, step=10.0)
                
                if st.button("Publier la mission"):
                    cur.execute("INSERT INTO jobs (client_id, user_id, title, description, budget, status) VALUES (%s, %s, %s, %s, %s, 'OPEN');", (st.session_state.user['id'], st.session_state.user['id'], title, description, budget))
                    conn.commit()
                    st.success("Mission publiée !")
                    st.session_state.active_tab = "🎯 Missions"
                    st.rerun()
            else:
                ev_title = st.text_input("Titre de l'événement")
                ev_desc = st.text_area("Description")
                ev_type = st.selectbox("Type", ["FORMATION", "WORKSHOP", "NETWORKING"])
                ev_date = st.date_input("Date")
                
                if st.button("Publier l'événement"):
                    cur.execute("INSERT INTO events (title, description, event_type, event_date) VALUES (%s, %s, %s, %s);", (ev_title, ev_desc, ev_type, ev_date))
                    conn.commit()
                    st.success("Événement enregistré!")
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Erreur: {e}")

# -----------------------------------------------------------------------------
# PAJ 6: 📑 CANDIDATURES
# -----------------------------------------------------------------------------
elif choice == "📑 Candidatures":
    u_id = st.session_state.user['id']
    st.title("📑 Candidatures")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT a.id, j.title, a.status, a.applied_at FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s;", (u_id,))
            my_apps = cur.fetchall()
            st.dataframe(pd.DataFrame(my_apps), use_container_width=True)
            conn.close()
        except Exception:
            st.info("Aucune candidature enregistrée.")

# -----------------------------------------------------------------------------
# PAJ 7: 💬 MESSAGERIE
# -----------------------------------------------------------------------------
elif choice == "💬 Messagerie":
    u_id = st.session_state.user['id']
    st.title("💬 Messagerie")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, full_name FROM users WHERE id <> %s ORDER BY full_name;", (u_id,))
            users_list = cur.fetchall()
            recipient_map = {u['full_name']: u['id'] for u in users_list}
            id_to_name = {u['id']: u['full_name'] for u in users_list}
            
            if recipient_map:
                default_idx = 0
                if st.session_state.msg_recipient_id in id_to_name:
                    target_name = id_to_name[st.session_state.msg_recipient_id]
                    keys = list(recipient_map.keys())
                    if target_name in keys:
                        default_idx = keys.index(target_name)
                
                selected_recipient = st.selectbox("Destinataire", list(recipient_map.keys()), index=default_idx)
                dest_id = recipient_map[selected_recipient]
                
                cur.execute("SELECT sender_id, content, sent_at FROM messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) ORDER BY sent_at ASC;", (u_id, dest_id, dest_id, u_id))
                messages_chat = cur.fetchall()
                
                if messages_chat:
                    for m in messages_chat:
                        sender_label = "Moi" if m['sender_id'] == u_id else selected_recipient
                        st.markdown(f"**{sender_label}:** {m['content']}")
                else:
                    st.info("Aucun message.")
                    
                msg_text = st.text_input("Votre message...")
                if st.button("Envoyer"):
                    if msg_text.strip():
                        cur.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s);", (u_id, dest_id, msg_text))
                        conn.commit()
                        st.rerun()
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Erreur messagerie: {e}")

# -----------------------------------------------------------------------------
# PAJ 8: 📅 ÉVÉNEMENTS
# -----------------------------------------------------------------------------
elif choice == "📅 Événements & Formations":
    st.title("📅 Événements")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM events ORDER BY event_date ASC;")
            events = cur.fetchall()
            conn.close()
            if events:
                for e in events:
                    st.subheader(e.get('title', 'Sans titre'))
                    st.write(e.get('description', ''))
            else:
                st.info("Aucun événement répertorié.")
        except Exception:
            st.info("Aucun événement répertorié.")

# -----------------------------------------------------------------------------
# PAJ 9: 📊 STATISTIQUES
# -----------------------------------------------------------------------------
elif choice == "📊 Statistiques":
    st.title("📊 Statistiques")
    conn = get_db_connection()
    if conn:
        try:
            df_users = pd.read_sql("SELECT user_type, COUNT(*) as count FROM users GROUP BY user_type;", conn)
            fig_users = px.pie(df_users, values='count', names='user_type', title="Utilisateurs par Type")
            st.plotly_chart(fig_users, use_container_width=True)
            conn.close()
        except Exception:
            st.info("Statistiques indisponibles.")

# -----------------------------------------------------------------------------
# PAJ 10: ⚙️ ADMINISTRATION DBA
# -----------------------------------------------------------------------------
elif choice == "⚙️ Administration DBA":
    if st.session_state.user.get('role') != 'ADMIN':
        st.error("⛔ Accès réservé aux administrateurs.")
    else:
        st.title("⚙️ Administration DBA")
        conn = get_db_connection()
        if conn:
            search_query = st.text_input("Rechercher un utilisateur")
            if search_query:
                try:
                    df_search = pd.read_sql("SELECT id, full_name, email, role, user_type FROM users WHERE full_name ILIKE %s OR email ILIKE %s LIMIT 50;", conn, params=(f"%{search_query}%", f"%{search_query}%"))
                    st.dataframe(df_search, use_container_width=True)
                except Exception as ex:
                    st.error(f"Erreur: {ex}")
            conn.close()