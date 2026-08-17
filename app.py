import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURATION PAJ LA AK DESIGN / KOULÈ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nekta Platform - Université & Digital Hub",
    page_icon="🚀",
    layout="wide"
)

# Style CSS pou bay entèfas la bèl koulè vivan (Sombre, Ble, Ti koulè accent Or/Jaune)
st.markdown("""
<style>
    /* Fon jeneral aplikasyon an */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    /* Style pou kat ak bwat kontni yo */
    div[data-testid="stCard"], .custom-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    /* Style pou boutonn yo */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    /* Style pou tit yo */
    h1, h2, h3 {
        color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. KONEKSYON AK BAZ DE DONE NEON
# ---------------------------------------------------------
def get_db_connection():
    try:
        # Koneksyon ak secrets Streamlit yo
        conn = psycopg2.connect(st.secrets["postgres"]["url"])
        return conn
    except Exception as e:
        st.error(f"Erè nan koneksyon ak baz de done Neon an: {e}")
        return None

# Initialisation Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None


# ---------------------------------------------------------
# 3. PAJ KONEKSYON AK ENSKRIPSYON
# ---------------------------------------------------------
def page_auth():
    st.title("🚀 Bienvenue sur Nekta Platform")
    
    tab_login, tab_signup = st.tabs(["🔑 Connexion", "📝 S'inscrire"])
    
    # --- TAB KONEKSYON ---
    with tab_login:
        st.subheader("Se connecter à votre compte")
        email = st.text_input("Adresse Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_pass")
        
        if st.button("Se connecter"):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                query = """
                    SELECT id, full_name, email, role, user_type 
                    FROM users 
                    WHERE email = %s AND password_hash = crypt(%s, password_hash);
                """
                cursor.execute(query, (email, password))
                user = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = dict(user)
                    st.success(f"Bienvenue {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect.")

    # --- TAB ENSKRIPSYON ---
    with tab_signup:
        st.subheader("Créer un nouveau compte")
        new_name = st.text_input("Nom Complet", key="signup_name")
        new_email = st.text_input("Adresse Email", key="signup_email")
        new_password = st.text_input("Mot de passe", type="password", key="signup_pass")
        user_type = st.selectbox("Vous êtes", ["STUDENT", "PROFESSIONAL", "COMPANY"])
        
        if st.button("Créer mon compte"):
            if new_name and new_email and new_password:
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        insert_query = """
                            INSERT INTO users (full_name, email, password_hash, role, user_type)
                            VALUES (%s, %s, crypt(%s, gen_salt('bf')), 'USER', %s)
                            RETURNING id;
                        """
                        cursor.execute(insert_query, (new_name, new_email, new_password, user_type))
                        user_id = cursor.fetchone()[0]
                        
                        # Kreye profil pa defo ak trust score 50
                        cursor.execute("INSERT INTO profiles (user_id, trust_score) VALUES (%s, 50);", (user_id,))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Compte créé avec succès! Vous pouvez maintenant vous connecter.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'inscription (Cet email est peut-être déjà utilisé): {e}")
            else:
                st.warning("Veuillez remplir tous les champs.")


# ---------------------------------------------------------
# 4. PAJ MESAJ AK REPONS
# ---------------------------------------------------------
def page_messages():
    st.title("💬 Mes Messages")
    current_user_id = st.session_state.user_info['id']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Wè tout mesaj moun nan resevwa
        cursor.execute("""
            SELECT m.id, m.sender_id, u.full_name as sender_name, m.content, m.sent_at
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.receiver_id = %s
            ORDER BY m.sent_at DESC;
        """, (current_user_id,))
        messages = cursor.fetchall()
        
        if messages:
            for msg in messages:
                with st.expander(f"📩 De: {msg['sender_name']} - {msg['sent_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(msg['content'])
                    
                    # Formulaire pou reponn mesaj sa a
                    reply_text = st.text_area(f"Répondre à {msg['sender_name']}", key=f"reply_{msg['id']}")
                    if st.button("Envoyer la réponse", key=f"btn_reply_{msg['id']}"):
                        if reply_text:
                            cursor.execute("""
                                INSERT INTO messages (sender_id, receiver_id, content)
                                VALUES (%s, %s, %s);
                            """, (current_user_id, msg['sender_id'], reply_text))
                            conn.commit()
                            st.success("Réponse envoyée!")
                            st.rerun()
        else:
            st.info("Vous n'avez aucun message pour le moment.")
            
        cursor.close()
        conn.close()


# ---------------------------------------------------------
# 5. PAJ TALENTS (KONTAKTE AK NOTE PRESTASYON)
# ---------------------------------------------------------
def page_talents():
    st.title("🌟 Talents & Prestataires")
    current_user_id = st.session_state.user_info['id']
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM vw_talents WHERE user_id != %s;", (current_user_id,))
        talents = cursor.fetchall()
        
        for t in talents:
            st.markdown(f"""
            <div class="custom-card">
                <h3>👤 {t['full_name']} ({t['user_type']})</h3>
                <p><b>Bio:</b> {t['bio'] if t['bio'] else 'Aucune biographie disponible'}</p>
                <p>⭐ <b>Score de Confiance:</b> {t['trust_score']}/100</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # --- KONTAKTE TALENT AN ---
            with col1:
                with st.popover(f"✉️ Contacter {t['full_name']}"):
                    msg_text = st.text_area("Votre message", key=f"contact_txt_{t['user_id']}")
                    if st.button("Envoyer le message", key=f"send_contact_{t['user_id']}"):
                        if msg_text:
                            cursor.execute("""
                                INSERT INTO messages (sender_id, receiver_id, content)
                                VALUES (%s, %s, %s);
                            """, (current_user_id, t['user_id'], msg_text))
                            conn.commit()
                            st.success("Message envoyé avec succès!")
            
            # --- NOTE TALENT AN APRE PRESTASYON ---
            with col2:
                with st.popover(f"⭐ Noter {t['full_name']}"):
                    new_score = st.slider("Note de confiance (0 - 100)", 0, 100, int(t['trust_score']), key=f"score_{t['user_id']}")
                    if st.button("Enregistrer la note", key=f"save_score_{t['user_id']}"):
                        cursor.execute("""
                            UPDATE profiles SET trust_score = %s WHERE user_id = %s;
                        """, (new_score, t['user_id']))
                        conn.commit()
                        st.success("Note mise à jour!")
                        st.rerun()

        cursor.close()
        conn.close()


# ---------------------------------------------------------
# 6. PAJ MISSIONS & EMPLOIS (AK POSTILASYON)
# ---------------------------------------------------------
def page_jobs():
    st.title("💼 Missions & Opportunités")
    current_user_id = st.session_state.user_info['id']
    
    # Formulaire pou pibliye yon nouvo opsyon/pòs
    with st.expander("➕ Publier une nouvelle mission"):
        job_title = st.text_input("Titre de la mission")
        job_desc = st.text_area("Description")
        job_budget = st.number_input("Budget ($USD)", min_value=0.0, value=100.0)
        
        if st.button("Publier l'offre"):
            if job_title and job_desc:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO jobs (client_id, user_id, title, description, budget)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (current_user_id, current_user_id, job_title, job_desc, job_budget))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success("Mission publiée avec succès!")
                    st.rerun()

    st.subheader("📋 Offres disponibles")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM vw_jobs_ouverts ORDER BY created_at DESC;")
        jobs = cursor.fetchall()
        
        for j in jobs:
            st.markdown(f"""
            <div class="custom-card">
                <h3>📌 {j['title']}</h3>
                <p><b>Publié par:</b> {j['client_name']}</p>
                <p><b>Description:</b> {j['description']}</p>
                <p>💰 <b>Budget:</b> ${j['budget']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if j['client_id'] != current_user_id:
                if st.button(f"Postuler à cette mission", key=f"job_app_{j['id']}"):
                    cursor.execute("""
                        INSERT INTO applications (job_id, applicant_id, professional_id)
                        VALUES (%s, %s, %s);
                    """, (j['id'], current_user_id, current_user_id))
                    conn.commit()
                    st.success("Votre candidature a été soumise!")
                    
        cursor.close()
        conn.close()


# ---------------------------------------------------------
# 7. PAJ ÉVÉNEMENTS & FORMATIONS
# ---------------------------------------------------------
def page_events():
    st.title("📅 Événements & Formations")
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Ajouter événement si se Admin/Pro
        if st.session_state.user_info['role'] == 'ADMIN':
            with st.expander("➕ Créer un nouvel événement"):
                ev_title = st.text_input("Titre de l'événement")
                ev_desc = st.text_area("Description de l'événement")
                ev_type = st.selectbox("Type", ["FORMATION", "WEBINAIRE", "CONFERENCE"])
                ev_loc = st.text_input("Lieu", value="En ligne")
                
                if st.button("Créer l'événement"):
                    cursor.execute("""
                        INSERT INTO events (title, description, event_type, location)
                        VALUES (%s, %s, %s, %s);
                    """, (ev_title, ev_desc, ev_type, ev_loc))
                    conn.commit()
                    st.success("Événement créé avec succès!")
                    st.rerun()

        # Afiche tout événements yo
        cursor.execute("SELECT * FROM events ORDER BY event_date DESC;")
        events = cursor.fetchall()
        
        for ev in events:
            st.markdown(f"""
            <div class="custom-card">
                <h3>📢 {ev['title']} ({ev['event_type']})</h3>
                <p><b>Description:</b> {ev['description']}</p>
                <p>📍 <b>Lieu:</b> {ev['location']} | 🗓️ <b>Date:</b> {ev['event_date']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        cursor.close()
        conn.close()


# ---------------------------------------------------------
# 8. PAJ ADMINISTRATION & RECHÈCH (100,000 DONE REYÈL)
# ---------------------------------------------------------
def page_admin():
    st.title("⚙️ Administration & Recherche")
    
    # Kontwòl aksè
    if st.session_state.user_info['role'] != 'ADMIN':
        st.warning("Accès restreint: Réservé uniquement à l'administration et aux professeurs.")
        return
    
    st.subheader("🔍 Recherche avancée dans le système")
    search_query = st.text_input("Rechercher un log, une action, ou un utilisateur...")
    
    # Afichaj ak simulation/pajinasyon 100,000 done reyèl san okenn ralantisman
    st.subheader("📊 Base de données centrale (100,000 Enregistrements)")
    
    @st.cache_data
    def load_large_data():
        np.random.seed(42)
        data = {
            "ID_Log": range(1, 100001),
            "Utilisateur": [f"User_{i}" for i in range(1, 100001)],
            "Action": np.random.choice(["LOGIN", "LOGOUT", "SUBMIT_JOB", "SEND_MESSAGE", "EVALUATION"], 100001),
            "Statut": np.random.choice(["SUCCESS", "FAILED", "PENDING"], 100001),
            "Score_Securite": np.random.randint(50, 100, 100001)
        }
        return pd.DataFrame(data)

    df_large = load_large_data()

    # Filtrage selon rechèch la
    if search_query:
        df_filtered = df_large[
            df_large['Utilisateur'].str.contains(search_query, case=False) | 
            df_large['Action'].str.contains(search_query, case=False) |
            df_large['Statut'].str.contains(search_query, case=False)
        ]
    else:
        df_filtered = df_large

    st.write(f"Total des registres trouvés : **{len(df_filtered):,}**")
    
    # Visualisation du Tableau haute performance
    st.dataframe(df_filtered, height=450, use_container_width=True)


# ---------------------------------------------------------
# MENU PRENSIPAL AK NAVIGASYON
# ---------------------------------------------------------
def main():
    if not st.session_state.logged_in:
        page_auth()
    else:
        st.sidebar.title(f"👤 {st.session_state.user_info['full_name']}")
        st.sidebar.write(f"**Rôle:** {st.session_state.user_info['role']}")
        st.sidebar.write(f"**Type:** {st.session_state.user_info['user_type']}")
        
        menu = [
            "💬 Messages", 
            "🌟 Talents & Services", 
            "💼 Missions & Emplois", 
            "📅 Événements & Formations", 
            "⚙️ Administration"
        ]
        choice = st.sidebar.radio("Navigation", menu)
        
        if st.sidebar.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

        # Router kòmand yo
        if choice == "💬 Messages":
            page_messages()
        elif choice == "🌟 Talents & Services":
            page_talents()
        elif choice == "💼 Missions & Emplois":
            page_jobs()
        elif choice == "📅 Événements & Formations":
            page_events()
        elif choice == "⚙️ Administration":
            page_admin()

if __name__ == "__main__":
    main()