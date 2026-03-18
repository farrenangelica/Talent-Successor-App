import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Talent Successor System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SESSION STATE INIT
# =========================
if "role" not in st.session_state:
    st.session_state.role = None

# =========================
# HEADER
# =========================
st.title("📊 Talent Successor System")
st.markdown("Integrated Talent Management & Succession Planning Dashboard")

# =========================
# SIDEBAR - ROLE (PALING ATAS)
# =========================
st.sidebar.title("👤 User Role")

role = st.sidebar.selectbox(
    "Select Your Role",
    ["Select Role", "HR", "Supervisor", "Manager"]
)

if role != "Select Role":
    st.session_state.role = role

st.sidebar.markdown("---")

# =========================
# SIDEBAR - NAVIGATION INFO
# =========================
st.sidebar.title("🧭 Navigation")
st.sidebar.info(
    """
    Use the sidebar to access:
    - Input Assessment
    - Master Data
    - 9 Box Talent
    - Succession Map
    """
)

# =========================
# MAIN CONTENT
# =========================
if st.session_state.role is None:
    st.warning("⚠️ Please select your role from the sidebar to continue.")
    st.stop()

# =========================
# ROLE-BASED INFO
# =========================
st.success(f"Logged in as: {st.session_state.role}")

if st.session_state.role == "HR":
    st.info("You have full access to all features including succession planning.")

elif st.session_state.role == "Supervisor":
    st.info("You can input and review assessment data.")

elif st.session_state.role == "Manager":
    st.info("You can view reports and talent insights.")

# =========================
# DASHBOARD OVERVIEW (OPTIONAL)
# =========================
st.markdown("## 📌 Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Employees", "—")

with col2:
    st.metric("High Performers", "—")

with col3:
    st.metric("Future Leaders", "—")

st.markdown("---")

st.markdown("### 🚀 Next Steps")
st.write(
    """
    1. Go to **Input Assessment** to enter employee evaluation data  
    2. Check **Master Data** for computed results  
    3. Explore **9 Box Talent** visualization  
    4. Review **Succession Map** for leadership planning  
    """
)