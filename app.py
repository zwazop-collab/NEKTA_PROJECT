import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import plotly.express as px

# ----------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & DESIGN CSS
# ----------------------------------------------------
st.set_page_config(
    page_title="NEKTA - Réseau Professionnel",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0d1117 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; font-weight: 500; }
    
    .hero-box { 
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 35px 20px; border-radius: 16px; color: white; text-align: center; margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .card { 
        background: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #1e3a8a; 
        margin-bottom: 15px; color: #1e293b;
    }
    
    div[data-testid="stMetric"] { 
        background: white; padding: 15px; border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-bottom: 3px solid #1e3a8a; 
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. CONNEXION SÉCURISÉE & ULTRA-RAPIDE À NEON DB
# ----------------------------------------------------
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
    """Exécute les requêtes SELECT de manière sécurisée et rapide"""
    try:
        conn = get_db_connection()
        if not conn or conn.closed:
            st.cache_resource.clear()
            conn = get_db_connection()
        if not conn:
            return [] if fetch == "all" else None
        
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch == "all":
                return cur.fetchall()
            elif fetch == "one":
                return cur.fetchone()
            return None
    except Exception:
        return [] if fetch == "all" else None

def run_action(query, params=None):
    """Exécute INSERT, UPDATE, DELETE san blokaj ak san rapo erè wouj"""
    try:
        conn = get_db_connection()
        if not conn or conn.closed:
            st.cache_resource.clear()
            conn = get_db_connection()
        if not conn:
            return False
        
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        return True
    except Exception:
        return False

# ----------------------------------------------------
# 3. INITIALISATION SESSION & UTILISATEUR ACTIF
# ----------------------------------------------------
if "auth" not in st.session_state:
    st.session_state.auth = True  # Mode accès direct activé par défaut

if "user_id" not in st.session_state:
    user = run_query("SELECT id FROM users LIMIT 1", fetch="one")
    if user and isinstance(user, dict) and "id" in user:
        st.session_state.user_id = user["id"]
    else:
        run_action(
            "INSERT INTO users (full_name, email, role) VALUES (%s, %s, %s)",
            ("Super Admin NEKTA", "admin@nekta.com", "ADMIN")
        )
        new_user = run_query("SELECT id FROM users WHERE email = %s", ("admin@nekta.com",), fetch="one")
        if new_user and isinstance(new_user, dict) and "id" in new_user:
            st.session_state.user_id = new_user["id"]
            run_action(
                "INSERT INTO profiles (user_id, bio, headline, trust_score, avatar_url) VALUES (%s, %s, %s, %s, %s)",
                (st.session_state.user_id, "Administrateur principal du réseau NEKTA", "Super Admin", 100.00, "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")
            )
        else:
            st.session_state.user_id = 1

current_user = run_query("SELECT id, full_name, email, role FROM users WHERE id = %s", (st.session_state.user_id,), fetch="one")

# ----------------------------------------------------
# 4. BARRE DE NAVIGATION (SIDEBAR)
# ----------------------------------------------------
with st.sidebar:
    st.title("💼 NEKTA")
    if current_user and isinstance(current_user, dict):
        st.markdown(f"**Utilisateur:** {current_user.get('full_name', 'N/A')}")
        st.markdown(f"**Rôle:** {current_user.get('role', 'USER')}")
        st.markdown(f"**ID:** `{current_user.get('id', 'N/A')}`")
    
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

    st.divider()

    # Sélecteur d'utilisateur pour basculer facilement en mode Test
    all_users_list = run_query("SELECT id, full_name FROM users LIMIT 20")
    if all_users_list:
        user_map = {f"{u['full_name']} (ID: {u['id']})": u['id'] for u in all_users_list}
        selected_u = st.selectbox("🔄 Changer de compte (Test)", list(user_map.keys()))
        if st.button("Basculer vers ce compte"):
            st.session_state.user_id = user_map[selected_u]
            st.rerun()

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Accueil & Feed",
            "Talents & Services",
            "Missions & Opportunités",
            "Mes Candidatures & Offres",
            "Messagerie Directe",
            "Évaluations & Avis",
            "Statistiques (BI)"
        ]
    )

# ----------------------------------------------------
# 5. COMPOSANT : COMPOSANT PROFIL & INTERACTIONS
# ----------------------------------------------------
def display_profile_card(target_user_id):
    target = run_query(
        "SELECT u.id, u.full_name, u.email, p.bio, p.headline, p.avatar_url, p.trust_score "
        "FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = %s",
        (target_user_id,), fetch="one"
    )
    if not target or not isinstance(target, dict):
        st.error("Profil non trouvé.")
        return

    with st.expander(f"👤 Profil complet de : {target['full_name']}", expanded=True):
        col_img, col_info = st.columns([1, 3])
        with col_img:
            avatar = target.get('avatar_url') or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
            st.image(avatar, width=120)
        with col_info:
            st.subheader(target['full_name'])
            st.write(f"**Titre:** {target.get('headline') or 'Non spécifié'}")
            st.write(f"**Bio:** {target.get('bio') or 'Aucune biographie disponible.'}")
            st.write(f"**Trust Score:** ⭐ {target.get('trust_score') or 50.0}%")

        st.divider()
        col_msg, col_rev = st.columns(2)

        # Envoi de message direct
        with col_msg:
            st.markdown("### 💬 Envoyer un Message")
            msg_body = st.text_area("Votre message:", key=f"msg_txt_{target_user_id}")
            if st.button("Envoyer le Message", key=f"btn_send_{target_user_id}"):
                if msg_body.strip():
                    if run_action(
                        "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                        (st.session_state.user_id, target_user_id, msg_body)
                    ):
                        st.success("Message envoyé avec succès !")
                    else:
                        st.error("Impossible d'envoyer le message.")
                else:
                    st.warning("Le message ne peut pas être vide.")

        # Soumission d'une évaluation
        with col_rev:
            st.markdown("### ⭐ Évaluer ce Profil")
            rating = st.slider("Note (1 à 5)", 1, 5, 5, key=f"rate_{target_user_id}")
            comment = st.text_input("Avis / Commentaire:", key=f"comm_{target_user_id}")
            if st.button("Soumettre la note", key=f"btn_rate_{target_user_id}"):
                if run_action(
                    "INSERT INTO reviews (evaluator_id, evaluated_id, rating, comment) VALUES (%s, %s, %s, %s)",
                    (st.session_state.user_id, target_user_id, rating, comment)
                ):
                    st.success("Évaluation enregistrée !")
                else:
                    st.error("Impossible de soumettre l'évaluation.")

# ----------------------------------------------------
# PAGE 1: ACCUEIL & FEED
# ----------------------------------------------------
if page == "Accueil & Feed":
    st.markdown('<div class="hero-box"><h1>Bienvenue sur NEKTA</h1><p>Le réseau professionnel qui valorise les compétences et sécurise les échanges.</p></div>', unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    total_jobs_res = run_query("SELECT COUNT(*) as cnt FROM jobs", fetch="one")
    total_users_res = run_query("SELECT COUNT(*) as cnt FROM users", fetch="one")
    
    total_jobs = total_jobs_res["cnt"] if total_jobs_res and isinstance(total_jobs_res, dict) else 0
    total_users = total_users_res["cnt"] if total_users_res and isinstance(total_users_res, dict) else 0

    m1.metric("Membres Actifs", total_users)
    m2.metric("Opportunités Publiées", total_jobs)
    m3.metric("Trust Score Moyen", "85.0%")

    st.divider()

    st.subheader("🌟 Profils à la Une")
    top_talents = run_query(
        "SELECT u.id, u.full_name, p.headline, p.avatar_url, p.trust_score "
        "FROM users u JOIN profiles p ON u.id = p.user_id LIMIT 4"
    )
    if top_talents:
        cols = st.columns(len(top_talents))
        for idx, t in enumerate(top_talents):
            with cols[idx]:
                avatar = t.get('avatar_url') or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
                st.image(avatar, width=100)
                st.markdown(f"**{t['full_name']}**")
                st.caption(f"{t.get('headline') or 'Professionnel'}")
                if st.button("Voir Profil", key=f"home_prof_{t['id']}"):
                    st.session_state["selected_profile"] = t["id"]

    st.divider()

    st.subheader("📌 Dernières Opportunités Publiées")
    jobs = run_query(
        "SELECT j.id, j.title, j.category, j.budget, j.user_id, u.full_name "
        "FROM jobs j JOIN users u ON j.user_id = u.id ORDER BY j.id DESC LIMIT 5"
    )
    if jobs:
        for j in jobs:
            st.markdown(f"**{j['title']}** | Catégorie: `{j['category']}` | Budget: `${j['budget']}` | Publié par: **{j['full_name']}**")
    else:
        st.info("Aucune opportunité récente pour le moment.")

    if "selected_profile" in st.session_state:
        display_profile_card(st.session_state["selected_profile"])

# ----------------------------------------------------
# PAGE 2: TALENTS & SERVICES
# ----------------------------------------------------
elif page == "Talents & Services":
    st.header("💎 Réseau des Talents & Offres de Services")
    
    search_term = st.text_input("Rechercher un professionnel par nom, compétence ou biographie...")
    if search_term:
        talents = run_query(
            "SELECT u.id as user_id, u.full_name, p.bio, p.trust_score, p.avatar_url "
            "FROM users u LEFT JOIN profiles p ON u.id = p.user_id "
            "WHERE u.full_name ILIKE %s OR p.bio ILIKE %s",
            (f"%{search_term}%", f"%{search_term}%")
        )
    else:
        talents = run_query(
            "SELECT u.id as user_id, u.full_name, p.bio, p.trust_score, p.avatar_url "
            "FROM users u LEFT JOIN profiles p ON u.id = p.user_id LIMIT 10"
        )

    if talents:
        for t in talents:
            col_pic, col1, col2 = st.columns([1, 4, 1])
            with col_pic:
                avatar = t.get('avatar_url') or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
                st.image(avatar, width=80)
            with col1:
                st.markdown(f"### {t['full_name']}")
                st.write(f"**Bio:** {t.get('bio') or 'Pas de biographie spécifiée.'}")
                st.write(f"**Trust Score:** ⭐ {t.get('trust_score') or 50.0}%")
            with col2:
                if st.button("Voir Profil", key=f"view_talent_{t['user_id']}"):
                    st.session_state["selected_profile"] = t["user_id"]
            st.divider()
    else:
        st.info("Aucun talent trouvé.")

    if "selected_profile" in st.session_state:
        display_profile_card(st.session_state["selected_profile"])

# ----------------------------------------------------
# PAGE 3: MISSIONS & OPPORTUNITÉS
# ----------------------------------------------------
elif page == "Missions & Opportunités":
    st.header("💼 Offres d'Emplois & Missions")
    
    with st.expander("➕ Publier une nouvelle opportunité"):
        title = st.text_input("Titre du poste / mission")
        category = st.selectbox("Catégorie", ["Développement Web", "Design", "Marketing", "Autre"])
        budget = st.number_input("Budget ($)", min_value=0.0, step=10.0)
        desc = st.text_area("Description de l'offre")
        if st.button("Publier l'offre"):
            if title and desc:
                if run_action(
                    "INSERT INTO jobs (user_id, title, category, budget, description) VALUES (%s, %s, %s, %s, %s)",
                    (st.session_state.user_id, title, category, budget, desc)
                ):
                    st.success("Offre publiée avec succès ! Tout le monde peut maintenant la voir.")
                    st.rerun()
                else:
                    st.error("Erreur lors de la publication de l'offre.")
            else:
                st.warning("Veuillez remplir le titre et la description.")

    st.subheader("Offres disponibles")
    jobs = run_query("SELECT j.id, j.title, j.category, j.budget, j.description, j.user_id as employer_id, u.full_name as employer_name FROM jobs j JOIN users u ON j.user_id = u.id ORDER BY j.id DESC")
    if jobs:
        for job in jobs:
            st.markdown(f"### {job['title']}")
            st.write(f"**Employeur:** {job['employer_name']} | **Catégorie:** {job['category']} | **Budget:** ${job['budget']}")
            st.write(job['description'])
            
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("Postuler", key=f"postulate_{job['id']}"):
                    if run_action(
                        "INSERT INTO applications (job_id, applicant_id) VALUES (%s, %s)",
                        (job['id'], st.session_state.user_id)
                    ):
                        st.success("Candidature envoyée avec succès !")
                    else:
                        st.warning("Vous avez déjà postulé à cette offre.")
            with c2:
                if st.button("Profil Employeur", key=f"emp_prof_{job['id']}"):
                    st.session_state["selected_profile"] = job["employer_id"]
            st.divider()

    if "selected_profile" in st.session_state:
        display_profile_card(st.session_state["selected_profile"])

# ----------------------------------------------------
# PAGE 4: MES CANDIDATURES & OFFRES
# ----------------------------------------------------
elif page == "Mes Candidatures & Offres":
    st.header("📋 Gestion de vos Candidatures et Offres")

    tab1, tab2 = st.tabs(["Candidatures Reçues sur mes Offres", "Mes Candidatures Soumises"])

    with tab1:
        st.subheader("Candidatures à traiter")
        my_jobs = run_query("SELECT id, title FROM jobs WHERE user_id = %s", (st.session_state.user_id,))
        if my_jobs:
            for j in my_jobs:
                st.markdown(f"#### Offre: {j['title']}")
                apps = run_query(
                    "SELECT a.id as app_id, a.applicant_id, u.full_name, a.status "
                    "FROM applications a JOIN users u ON a.applicant_id = u.id WHERE a.job_id = %s",
                    (j['id'],)
                )
                if apps:
                    for app in apps:
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        col1.write(f"**Candidat:** {app['full_name']} | **Statut:** `{app['status']}`")
                        
                        if col2.button("Profil", key=f"view_app_p_{app['app_id']}"):
                            st.session_state["selected_profile"] = app['applicant_id']
                        
                        if col3.button("Accepter", key=f"acc_{app['app_id']}"):
                            run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (app['app_id'],))
                            st.success("Candidature Acceptée !")
                            st.rerun()

                        if col4.button("Refuser", key=f"rej_{app['app_id']}"):
                            run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (app['app_id'],))
                            st.error("Candidature Refusée !")
                            st.rerun()
                else:
                    st.write("Aucune candidature reçue pour cette offre.")
                st.divider()
        else:
            st.write("Vous n'avez publié aucune offre d'emploi.")

    with tab2:
        st.subheader("Offres auxquelles vous avez postulé")
        my_apps = run_query(
            "SELECT a.id, j.title, a.status, u.full_name as employer_name "
            "FROM applications a JOIN jobs j ON a.job_id = j.id "
            "JOIN users u ON j.user_id = u.id WHERE a.applicant_id = %s",
            (st.session_state.user_id,)
        )
        if my_apps:
            for ma in my_apps:
                st.write(f"**Poste:** {ma['title']} | **Employeur:** {ma['employer_name']} | **Statut:** `{ma['status']}`")
        else:
            st.write("Vous n'avez encore postulé à aucune offre.")

    if "selected_profile" in st.session_state:
        display_profile_card(st.session_state["selected_profile"])

# ----------------------------------------------------
# PAGE 5: MESSAGERIE DIRECTE
# ----------------------------------------------------
elif page == "Messagerie Directe":
    st.header("💬 Messagerie Professionnelle")

    t_inbox, t_send = st.tabs(["Boîte de Réception", "Nouveau Message"])

    with t_inbox:
        msgs = run_query(
            "SELECT m.id, m.sender_id, u.full_name as sender_name, m.content, m.created_at "
            "FROM messages m JOIN users u ON m.sender_id = u.id "
            "WHERE m.receiver_id = %s ORDER BY m.created_at DESC",
            (st.session_state.user_id,)
        )
        if msgs:
            for msg in msgs:
                st.markdown(f"**De:** {msg['sender_name']} (*{msg['created_at']}*)")
                st.info(msg['content'])
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Répondre / Profil", key=f"reply_msg_{msg['id']}"):
                        st.session_state["selected_profile"] = msg['sender_id']
                st.divider()
        else:
            st.write("Votre boîte de réception est vide.")

    with t_send:
        all_users = run_query("SELECT id, full_name FROM users WHERE id != %s", (st.session_state.user_id,))
        if all_users:
            user_opts = {u["full_name"]: u["id"] for u in all_users}
            target_name = st.selectbox("Destinataire", list(user_opts.keys()))
            new_msg = st.text_area("Message à envoyer")
            if st.button("Envoyer"):
                if new_msg.strip():
                    if run_action(
                        "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                        (st.session_state.user_id, user_opts[target_name], new_msg)
                    ):
                        st.success("Message envoyé avec succès !")
                    else:
                        st.error("Erreur d'envoi du message.")
                else:
                    st.warning("Veuillez saisir un message.")

    if "selected_profile" in st.session_state:
        display_profile_card(st.session_state["selected_profile"])

# ----------------------------------------------------
# PAGE 6: ÉVALUATIONS & AVIS
# ----------------------------------------------------
elif page == "Évaluations & Avis":
    st.header("⭐ Évaluations & Avis")

    st.subheader("Mes Avis Reçus")
    reviews = run_query(
        "SELECT r.rating, r.comment, r.created_at, u.full_name as evaluator_name "
        "FROM reviews r JOIN users u ON r.evaluator_id = u.id WHERE r.evaluated_id = %s",
        (st.session_state.user_id,)
    )
    if reviews:
        for r in reviews:
            st.markdown(f"**Par:** {r['evaluator_name']} | **Note:** ⭐ `{r['rating']}/5`")
            st.write(f"*{r['comment']}*")
            st.caption(f"Date: {r['created_at']}")
            st.divider()
    else:
        st.write("Vous n'avez pas encore reçu d'évaluations.")

# ----------------------------------------------------
# PAGE 7: STATISTIQUES (BI)
# ----------------------------------------------------
elif page == "Statistiques (BI)":
    st.header("📊 Business Intelligence & Dashboard")
    
    cat_stats = run_query("SELECT category, COUNT(*) as nombre FROM jobs GROUP BY category")
    if cat_stats:
        st.subheader("Répartition des Offres par Catégorie")
        df_cat = pd.DataFrame(cat_stats)
        fig = px.pie(df_cat, values='nombre', names='category', title="Offres d'Emploi par Catégorie", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas encore assez de données pour afficher les statistiques.")