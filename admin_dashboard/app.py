import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://backend:8000"
PUBLIC_API_URL = "http://localhost:8000"

st.set_page_config(page_title="CipherEye Admin", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    div.stButton > button { width: 100%; border-radius: 5px; }
    .success-msg { color: #2ecc71; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

query_params = st.experimental_get_query_params()
url_token = query_params.get("token", [None])[0]
url_email = query_params.get("email", [None])[0]

if 'token' not in st.session_state: st.session_state.token = url_token
if 'user_email' not in st.session_state: st.session_state.user_email = url_email
if 'is_admin' not in st.session_state: st.session_state.is_admin = True if url_token else False 

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def fetch_challenges():
    try:
        r = requests.get(f"{API_URL}/challenges/list")
        if r.status_code == 200: return r.json()
    except: return []
    return []

def login(email, password):
    try:
        r = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if r.status_code == 200:
            data = r.json()
            if not data.get('is_admin'):
                st.error("⛔ Access Denied: You are not an Admin.")
                return
            st.session_state.token = data.get("access_token")
            st.session_state.is_admin = True
            st.session_state.user_email = email
            st.experimental_set_query_params(token=st.session_state.token, email=email)
            st.success("Welcome back, Commander.")
            time.sleep(0.5)
            st.experimental_rerun()
        else: st.error("Invalid credentials")
    except Exception as e: st.error(f"Connection Error: {e}")

def signup(email, password):
    try:
        r = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
        if r.status_code == 200: st.success("✅ Account Created! Promote via terminal.");
        else: st.error(f"Signup Failed: {r.text}")
    except Exception as e: st.error(f"Connection Error: {e}")

def logout():
    st.session_state.token = None
    st.experimental_set_query_params() 
    st.experimental_rerun()

# --- APP ---
if not st.session_state.token:
    st.title("🛡️ Admin Restricted Area")
    t1, t2 = st.tabs(["🔑 Login", "📝 Register"])
    with t1:
        with st.form("l"):
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"): login(e, p)
    with t2:
        st.info("New accounts must be promoted via terminal.")
        with st.form("s"):
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Register"): signup(e, p)

else:
    st.sidebar.title("Command Center")
    st.sidebar.caption(f"User: {st.session_state.user_email}")
    mode = st.sidebar.radio("Module", ["Challenge Manager", "User Manager", "OSINT Scanner"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"): logout()

    # --- 1. CHALLENGE MANAGER ---
    if mode == "Challenge Manager":
        st.title("⚙️ Challenge Management")
        t_cr, t_del, t_ed = st.tabs(["➕ Create", "🗑️ Delete", "✏️ Edit"])
        
        with t_cr:
            with st.form("new", clear_on_submit=True):
                title = st.text_input("Title")
                c1, c2 = st.columns(2)
                with c1: lvl = st.selectbox("Level", [1,2,3])
                with c2: pts = st.number_input("Points", value=10, min_value=0, step=1)
                desc = st.text_area("Description")
                uf = st.file_uploader("Upload File")
                ext = st.text_input("Or Link")
                flag = st.text_input("Flag")
                
                if st.form_submit_button("Publish"):
                    res = ext
                    if uf:
                        try:
                            f = {"file": (uf.name, uf.getvalue(), uf.type)}
                            u = requests.post(f"{API_URL}/challenges/upload", files=f)
                            if u.status_code==200: res = PUBLIC_API_URL + u.json()['resource_url']
                        except: st.error("Upload failed")
                    try:
                        r = requests.post(f"{API_URL}/challenges/create", json={
                            "title":title, "description":desc, "resources":res, "flag":flag, "level":lvl, "points":pts
                        })
                        if r.status_code == 200: st.success("Published!")
                        else: st.error(r.text)
                    except: st.error("Connection Failed")

        with t_del:
            try:
                data = fetch_challenges()
                if data:
                    df = pd.DataFrame(data)
                    df.insert(0, "Select", False)
                    edf = st.data_editor(df, column_config={"Select": st.column_config.CheckboxColumn(required=True)}, hide_index=True)
                    if st.button("Delete Selected"):
                        for _, row in edf[edf["Select"]].iterrows():
                            requests.delete(f"{API_URL}/challenges/{row['id']}")
                        st.success("Deleted!")
                        time.sleep(1)
                        st.experimental_rerun()
                else: st.info("No challenges found.")
            except: pass

        with t_ed:
            challenges = fetch_challenges()
            if challenges:
                opts = {f"Lvl {c['level']} - {c['title']}": c for c in challenges}
                sel = st.selectbox("Choose Challenge", list(opts.keys()))
                if sel:
                    c = opts[sel]
                    with st.form("edit_form"):
                        e_title = st.text_input("Title", value=c['title'])
                        ec1, ec2 = st.columns(2)
                        with ec1: e_lvl = st.selectbox("Level", [1,2,3], index=[1,2,3].index(c['level']))
                        with ec2: e_pts = st.number_input("Points", value=c['points'], min_value=0, step=1)
                        e_desc = st.text_area("Description", value=c['description'])
                        e_res = st.text_input("Resource URL", value=c['resources'] if c['resources'] else "")
                        e_flag = st.text_input("Flag", value=c['flag'])
                        if st.form_submit_button("💾 Update"):
                            pl = {"title": e_title, "level": e_lvl, "points": e_pts, "description": e_desc, "resources": e_res, "flag": e_flag}
                            ur = requests.put(f"{API_URL}/challenges/{c['id']}", json=pl)
                            if ur.status_code == 200: st.success("Updated!"); time.sleep(1); st.experimental_rerun()
                            else: st.error(f"Failed: {ur.text}")
            else: st.info("No challenges.")

    # --- 2. USER MANAGER ---
    elif mode == "User Manager":
        st.title("👥 User Administration")
        
        # --- NEW: CREATE USER FORM ---
        with st.expander("➕ Create New User", expanded=False):
            with st.form("create_user_admin"):
                c1, c2 = st.columns(2)
                with c1: new_email = st.text_input("Email Address")
                with c2: new_pass = st.text_input("Password", type="password")
                is_admin_check = st.checkbox("Grant Admin Privileges?")
                
                if st.form_submit_button("Create User"):
                    if new_email and new_pass:
                        try:
                            payload = {
                                "email": new_email,
                                "password": new_pass,
                                "is_admin": is_admin_check
                            }
                            r = requests.post(f"{API_URL}/auth/users", json=payload, headers=get_headers())
                            if r.status_code == 200:
                                st.success(f"User {new_email} created successfully!")
                                time.sleep(1)
                                st.experimental_rerun()
                            else:
                                st.error(f"Error: {r.json().get('detail')}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")
                    else:
                        st.warning("Email and Password are required.")

        st.divider()
        st.subheader("Existing Users")
        
        try:
            ur = requests.get(f"{API_URL}/auth/users", headers=get_headers())
            
            if ur.status_code != 200:
                st.error("⚠️ Session Invalid. Please Re-login.")
                if st.button("Relogin"): logout()
            else:
                users = ur.json()
                st.dataframe(pd.DataFrame(users)[["email", "score", "is_admin"]], use_container_width=True)
                
                st.divider()
                st.subheader("📝 Manage Selected User")
                
                u_opts = {f"{u['email']} (Score: {u['score']})": u for u in users}
                u_sel = st.selectbox("Select Target User", list(u_opts.keys()))
                
                if u_sel:
                    target = u_opts[u_sel]
                    current = target['score']
                    
                    c1, c2 = st.columns(2)
                    with c1: 
                        st.info("📉 Penalty")
                        deduct_amt = st.number_input("Points to Remove", min_value=0, value=0, step=10)
                        if st.button("🔴 Deduct Points", type="primary"):
                            new_score = max(0, current - deduct_amt)
                            r = requests.put(f"{API_URL}/auth/users/{target['id']}/score", json={"score": new_score}, headers=get_headers())
                            if r.status_code==200: st.success(f"Deducted! New Score: {new_score}"); time.sleep(1); st.experimental_rerun()
                    
                    with c2:
                        st.info("💾 Adjustment")
                        set_amt = st.number_input("Set Exact Score", min_value=0, value=current)
                        if st.button("💾 Save Score"):
                            r = requests.put(f"{API_URL}/auth/users/{target['id']}/score", json={"score": set_amt}, headers=get_headers())
                            if r.status_code==200: st.success("Score Updated!"); time.sleep(1); st.experimental_rerun()
                    
                    st.divider()
                    
                    with st.expander("Danger Zone (Delete User)"):
                        st.warning(f"You are about to delete **{target['email']}**.")
                        if st.button("🗑️ Confirm Delete"):
                            r = requests.delete(f"{API_URL}/auth/users/{target['id']}", headers=get_headers())
                            if r.status_code == 200:
                                st.success("User Deleted.")
                                time.sleep(1)
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed: {r.json().get('detail')}")

        except Exception as e: st.error(f"Error: {e}")

    elif mode == "OSINT Scanner":
        st.title("🕵️ OSINT Tools")
        mod = st.selectbox("Module", ["whois_module", "dns_module"])
        tgt = st.text_input("Target")
        if st.button("Run"):
            try:
                requests.post(f"{API_URL}/api/run", json={"module":mod, "target":tgt})
                st.success("Job Sent.")
            except: st.error("Backend Offline")
