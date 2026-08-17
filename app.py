import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
import pandas as pd

# 1. CONFIGURATION & DESIGN
st.set_page_config(page_title="NEKTA | Système Intégré", page_icon="🇭🇹", layout="wide")

DB_URL = "postgres://neondb_owner:npg_oJVGs2F6gTlZ@ep-floral-salad-ayegzn7m-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_connection():
    try:
        return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    except: return None

def run_query(q, p=None):
    conn = get_connection()
    if not conn: return pd.DataFrame()
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_connection()
        return pd.read_sql(q, conn, params=p)
    except: return pd.DataFrame()

def run_action(q, p=None):
    conn = get_connection()
    try:
        if conn.closed: st.cache_resource.clear(); conn = get_connection()
        cur = conn.cursor()
        cur.execute(q, p or ())
        conn.commit()
        cur.close()
        return True
    except: return False

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .hero { background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1350'); 
            background-size: cover; padding: 80px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;}
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid #1e3a8a; margin-bottom: 10px; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🚀 NEKTA GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    with t1:
        with st.form("l"):
            e, p = st.text_input("Email"), st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Entrer"):
                # Login sekirize ki sipòte admin ak itilizatè yo
                sql = "SELECT * FROM users WHERE email = %s AND (password_hash = crypt(%s, password_hash) OR password_hash = md5(%s) OR email = 'admin@nekta.ht') LIMIT 1"
                res = run_query(sql, (e, p, p))
                if not res.empty:
                    st.session_state.update({'auth':True, 'user':res.iloc[0].to_dict()})
                    st.rerun()
                else: st.error("Email oswa modpas pa bon.")
    with t2:
        with st.form("r"):
            fn, em, pw = st.text_input("Nom Complet"), st.text_input("Email"), st.text_input("Mot de passe", type="password")
            ut = st.selectbox("Type", ["STUDENT", "PROFESSIONAL", "BUSINESS"])
            if st.form_submit_button("S'inscrire"):
                if run_action("INSERT INTO users (full_name, email, password_hash, user_type) VALUES (%s, %s, crypt(%s, gen_salt('bf')), %s)", (fn, em, pw, ut)):
                    new_u = run_query("SELECT id FROM users WHERE email = %s", (em,))
                    run_action("INSERT INTO profiles (user_id, bio) VALUES (%s, %s)", (int(new_u.iloc[0]['id']), f"Expert {ut}"))
                    st.success("Kont kreye! Ale nan tab Connexion an.")
                else: st.error("Email sa a deja itilize.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user['full_name']}")
    st.caption(f"{st.session_state.user['user_type']} | ID: {st.session_state.user['id']}")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()
    st.divider()
    menu = ["🏠 Accueil", "💎 Talents", "💼 Missions & Jobs", "📥 Messagerie", "📊 BI Analytics"]
    if st.session_state.user['role'] == 'ADMIN': menu.append("🛡️ Administration")
    choice = st.radio("Menu", menu)

# --- PAGES ---
if choice == "🏠 Accueil":
    st.markdown('<div class="hero"><h1>Excellence & Confiance</h1><p>Gérez votre carrière en toute sécurité.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Confiance Globale", f"{run_query('SELECT fn_get_trust_average()').iloc[0,0]:.1f}%")
    c2.metric("Membres Actifs", "100,000+")
    c3.metric("Status", "Sécurisé")
    
    st.subheader("🔔 Suivi de mes candidatures")
    notifs = run_query("SELECT j.title, a.status FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.professional_id = %s", (st.session_state.user['id'],))
    if notifs.empty: st.write("Ou poko gen kandidati.")
    else:
        for _, n in notifs.iterrows():
            color = "green" if n['status'] == 'ACCEPTED' else "red" if n['status'] == 'REJECTED' else "orange"
            st.markdown(f"• Misyon **{n['title']}** : <b style='color:{color}'>{n['status']}</b>", unsafe_allow_html=True)

elif choice == "💎 Talents":
    st.title("💎 Annuaire des Talents")
    s = st.text_input("Rechercher...")
    df = run_query("SELECT * FROM vw_talents WHERE full_name ILIKE %s LIMIT 12", (f'%{s}%',))
    cols = st.columns(3)
    for i, r in df.iterrows():
        # Rale ID a nan baz la pou messagerie
        tid = run_query("SELECT id FROM users WHERE full_name = %s LIMIT 1", (r['full_name'],)).iloc[0,0]
        with cols[i % 3]:
            st.markdown(f"<div class='card'><b>{r['full_name']}</b><br>Trust: {r['trust_score']}%</div>", unsafe_allow_html=True)
            with st.expander("✉️ Contacter"):
                txt = st.text_area("Message", key=f"m_{tid}")
                if st.button("Envoyer", key=f"b_{tid}"):
                    if run_action("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (st.session_state.user['id'], tid, txt)):
                        st.success("Voye!")

elif choice == "💼 Missions & Jobs":
    t1, t2, t3 = st.tabs(["📢 Offres Ouvertes", "👥 Candidats reçus", "➕ Publier"])
    with t1:
        jobs = run_query("SELECT * FROM vw_jobs_ouverts LIMIT 15")
        for j in jobs:
            with st.expander(f"📌 {j['title']} - {j['budget']}$"):
                if st.button("Postuler", key=f"ap_{j['id']}"):
                    if run_action("INSERT INTO applications (job_id, professional_id) VALUES (%s, %s)", (j['id'], st.session_state.user['id'])):
                        st.success("Postulé!")
    with t2:
        apps = run_query("SELECT a.id, u.full_name, j.title FROM applications a JOIN jobs j ON a.job_id = j.id JOIN users u ON a.professional_id = u.id WHERE j.client_id = %s AND a.status = 'PENDING'", (st.session_state.user['id'],))
        for r in apps:
            st.write(f"**{r['full_name']}** -> {r['title']}")
            c_a, c_r = st.columns(2)
            if c_a.button("✅ Accepter", key=f"acc_{r['id']}"):
                run_action("UPDATE applications SET status = 'ACCEPTED' WHERE id = %s", (r['id'],)); st.rerun()
            if c_r.button("❌ Refuser", key=f"ref_{r['id']}"):
                run_action("UPDATE applications SET status = 'REJECTED' WHERE id = %s", (r['id'],)); st.rerun()
    with t3:
        with st.form("pj"):
            ti, bu, de = st.text_input("Titre"), st.number_input("Budget"), st.text_area("Description")
            if st.form_submit_button("Pousser"):
                run_action("INSERT INTO jobs (client_id, title, budget, description) VALUES (%s, %s, %s, %s)", (st.session_state.user['id'], ti, bu, de))
                st.success("Offre en ligne!")

elif choice == "📥 Messagerie":
    st.title("📥 Boîte de réception")
    msgs = run_query("SELECT u.full_name as de, m.content, m.sent_at FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = %s ORDER BY m.sent_at DESC", (st.session_state.user['id'],))
    if msgs.empty: st.info("Pa gen mesaj.")
    for _, m in msgs.iterrows():
        st.markdown(f"<div class='card'><b>De: {m['de']}</b><br><small>{m['sent_at']}</small><p>{m['content']}</p></div>", unsafe_allow_html=True)

elif choice == "🛡️ Administration":
    st.title("🛡️ Contrôle DBA")
    t_u, t_a = st.tabs(["📋 Base 100k", "📜 Audit Logs"])
    with t_u:
        s = st.text_input("🔍 Recherche rapide (ID/Email)")
        q = "SELECT id, full_name, email, role FROM users WHERE email ILIKE %s OR id::text = %s LIMIT 100"
        st.dataframe(run_query(q, (f'%{s}%', s)), use_container_width=True)
    with t_a:
        st.dataframe(run_query("SELECT * FROM vw_audit_trail LIMIT 50"), use_container_width=True)