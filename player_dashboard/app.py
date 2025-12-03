import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://backend:8000"
PUBLIC_API_URL = "http://localhost:8000"

st.set_page_config(page_title="CipherEye CTF", layout="wide", page_icon="🎮")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    div.stButton > button { width: 100%; border-radius: 5px; background-color: #ff4b4b; color: white; border: none;}
    div.stButton > button:hover { background-color: #ff3333; }
    .challenge-box { border: 1px solid #333; padding: 20px; border-radius: 10px; background: #1f2129; margin-bottom: 20px; }
    h3 { color: #ff4b4b !important; }
</style>
""", unsafe_allow_html=True)

# --- SESSION & PERSISTENCE ---
# 1. Check URL for token (Persistence)
query_params = st.experimental_get_query_params()
url_token = query_params.get("token", [None])[0]
url_email = query_params.get("email", [None])[0]

if 'token' not in st.session_state: 
    st.session_state.token = url_token
if 'user_email' not in st.session_state: 
    st.session_state.user_email = url_email
if 'my_score' not in st.session_state: 
    st.session_state.my_score = 0

# --- AUTH FUNCTIONS ---
def login(email, password):
    try:
        r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            token = r.json().get("access_token")
            st.session_state.token = token
            st.session_state.user_email = email
            # Save to URL so it survives refresh
            st.experimental_set_query_params(token=token, email=email)
            st.success("🚀 Access Granted!")
            time.sleep(0.5)
            st.experimental_rerun()
        else: st.error("❌ Invalid credentials")
    except Exception as e: st.error(f"⚠️ Server Offline: {e}")

def signup(email, password):
    try:
        r = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
        if r.status_code == 200: st.success("✅ Registered! Please Log In."); 
        else: st.error(f"❌ Error: {r.json().get('detail')}")
    except Exception as e: st.error(f"⚠️ Server Offline: {e}")

def logout():
    st.session_state.token = None
    st.session_state.user_email = None
    st.experimental_set_query_params() # Clear URL
    st.experimental_rerun()

# --- VIEW: GUEST ---
if not st.session_state.token:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🎮 Join the Game")
        t1, t2 = st.tabs(["Login", "Register"])
        with t1:
            with st.form("l"):
                e = st.text_input("Email", key="l_e")
                p = st.text_input("Password", type="password", key="l_p")
                if st.form_submit_button("Enter Arena"): login(e, p)
        with t2:
            with st.form("s"):
                re = st.text_input("Email", key="r_e")
                rp = st.text_input("Password", type="password", key="r_p")
                if st.form_submit_button("Create Profile"): signup(re, rp)

# --- VIEW: PLAYER ---
else:
    c1, c2, c3 = st.columns([1, 6, 1])
    with c1: st.image("https://img.icons8.com/color/96/hacker.png", width=60)
    with c2: st.title("CipherEye Arena")
    with c3: 
        if st.button("Logout"): logout()

    st.markdown("---")
    
    # 2. Fetch Leaderboard (Async update)
    try:
        lb_data = requests.get(f"{API_URL}/challenges/leaderboard").json()
        # Update score from leaderboard if available
        for u in lb_data:
            if u['email'] == st.session_state.user_email.split('@')[0]:
                st.session_state.my_score = u['score']
                break
    except: pass

    # 3. Metrics Display (Uses Session State for instant updates)
    m1, m2, m3 = st.columns(3)
    m1.metric("YOUR SCORE", f"{st.session_state.my_score} PTS")
    m2.metric("PLAYER", st.session_state.user_email)
    m3.metric("STATUS", "ONLINE", delta_color="normal")

    if lb_data:
        with st.expander("📊 Live Leaderboard"):
            st.bar_chart(pd.DataFrame(lb_data).set_index("email"))

    st.markdown("---")
    st.header("🎯 Active Missions")
    
    try:
        challenges = requests.get(f"{API_URL}/challenges/list").json()
        t1, t2, t3 = st.tabs(["🟢 Level 1", "🟡 Level 2", "🔴 Level 3"])
        
        def render_cards(lvl):
            clist = [c for c in challenges if c['level'] == lvl]
            if not clist: st.info("No missions available."); return
            
            cols = st.columns(3)
            for i, c in enumerate(clist):
                with cols[i%3]:
                    with st.container():
                        st.markdown(f"""
                        <div class="challenge-box">
                            <h3>{c['title']}</h3>
                            <p style='color:#bbb;'>REWARD: <b>{c['points']} PTS</b></p>
                            <hr style='border-color: #444;'>
                            <p>{c['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if c.get('resources'):
                            res = c['resources']
                            if "/static/" in res and not res.startswith("http"):
                                res = PUBLIC_API_URL + res
                            st.link_button("📂 Intel Data", res)
                        
                        flag = st.text_input("Enter Flag", key=f"f_{c['id']}")
                        
                        if st.button("Submit", key=f"b_{c['id']}"):
                            try:
                                res = requests.post(f"{API_URL}/challenges/verify", 
                                    json={"user_email": st.session_state.user_email, "challenge_id": c['id'], "flag": flag}).json()
                                
                                if res['correct']:
                                    # 4. INSTANT SCORE UPDATE
                                    st.session_state.my_score = res['new_total_score']
                                    st.balloons()
                                    st.success(res['message'])
                                    time.sleep(1)
                                    st.experimental_rerun()
                                else:
                                    st.error(res['message'])
                            except: st.error("System Error")
                    st.divider()
        
        with t1: render_cards(1)
        with t2: render_cards(2)
        with t3: render_cards(3)
    except: st.error("Failed to load missions.")
