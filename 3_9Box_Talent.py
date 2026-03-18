import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os

# =========================
# ACCESS CONTROL
# =========================
if "role" not in st.session_state or st.session_state.role is None:
    st.warning("⚠️ Please select your role first.")
    st.stop()

if st.session_state.role not in ["HR", "Manager"]:
    st.error("⛔ You do not have access to this page.")
    st.stop()

# =========================
# TITLE
# =========================
st.title("📈 9 Box Talent")

MASTER_PATH = "data/master_data.csv"
ASSESS_PATH = "data/assessment_data.csv"
STORE_KOTA_PATH = "data/store_kota_mapping.csv"
BG_PATH = "assets/9box_background.png"

# =========================
# LOAD DATA
# =========================
master_df = pd.read_csv(MASTER_PATH)

if os.path.exists(ASSESS_PATH):
    try:
        assess_df = pd.read_csv(ASSESS_PATH)
    except:
        assess_df = pd.DataFrame()
else:
    assess_df = pd.DataFrame()

store_kota_df = pd.read_csv(STORE_KOTA_PATH)

# =========================
# CLEAN & TRANSFORM
# =========================
master_df["Outlet"] = master_df["Outlet"].str.strip()
store_kota_df["Outlet"] = store_kota_df["Outlet"].str.strip()

master_df = master_df.rename(columns={
    "Name": "Nama",
    "Jobtitle": "JobTitle",
    "Join Date": "JoinDate"
})

def extract_brand(dept):
    if pd.isna(dept):
        return None
    return str(dept).split()[-1]

master_df["Brand"] = master_df["Department"].apply(extract_brand)

master_df = pd.merge(master_df, store_kota_df, on="Outlet", how="left")

# Job Level mapping
JOB_LEVEL_MAP = {
    "Sales Associate": "SA",
    "Sr. Sales Associate": "SSA",
    "Asst. Spv. Store": "ASPV",
    "Spv. Store": "SPV",
    "Asst. Store Head": "ASM",
    "Full Store Head": "SM"
}
master_df["Job Level"] = master_df["JobTitle"].map(JOB_LEVEL_MAP)

# =========================
# FILTER RAW (STORE ONLY)
# =========================
dept_pattern = r"Operation.*(AX|CK|EA7|Pedro|Pomelo)"
mask_dept = master_df["Department"].str.contains(dept_pattern, regex=True, na=False)

allowed_jobs = list(JOB_LEVEL_MAP.keys())
mask_job = master_df["JobTitle"].isin(allowed_jobs)

master_df = master_df[mask_dept & mask_job]

# =========================
# MERGE
# =========================
df = pd.merge(master_df, assess_df, on="NIK", how="left")

# =========================
# CALCULATION
# =========================
def safe_avg(values):
    valid = [v for v in values if pd.notna(v)]
    return sum(valid) / len(valid) if valid else None

def calc(row):
    perf = safe_avg([row.get("KPI"), row.get("PA360")])
    obp_sop = safe_avg([row.get("OBP"), row.get("SOP")])
    pot = safe_avg([row.get("Psikogram"), row.get("Competency"), obp_sop])
    return pd.Series([perf, pot])

df[["Performance", "Potential"]] = df.apply(calc, axis=1)

df = df.dropna(subset=["Performance", "Potential"])

# =========================
# CATEGORY (SIMPLE)
# =========================
def category(perf, pot):
    if perf >= 8 and pot >= 8:
        return "Future Leader"
    elif perf >= 8:
        return "High Performer"
    elif pot >= 8:
        return "Emerging Talent"
    elif perf < 6 and pot < 6:
        return "Low Performer"
    else:
        return "Solid Contributor"

df["Category"] = df.apply(lambda x: category(x["Performance"], x["Potential"]), axis=1)

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.subheader("🔍 Filter")

brand = st.sidebar.selectbox("Brand", ["All"] + sorted(df["Brand"].dropna().unique()))
kota = st.sidebar.selectbox("Kota", ["All"] + sorted(df["Kota"].dropna().unique()))
job = st.sidebar.selectbox("Job Level", ["All"] + sorted(df["Job Level"].dropna().unique()))
cat = st.sidebar.selectbox("Category", ["All"] + sorted(df["Category"].dropna().unique()))

filtered_df = df.copy()

if brand != "All":
    filtered_df = filtered_df[filtered_df["Brand"] == brand]

if kota != "All":
    filtered_df = filtered_df[filtered_df["Kota"] == kota]

if job != "All":
    filtered_df = filtered_df[filtered_df["Job Level"] == job]

if cat != "All":
    filtered_df = filtered_df[filtered_df["Category"] == cat]

# =========================
# LOAD IMAGE (FIXED)
# =========================
img = Image.open(BG_PATH)

# =========================
# PLOT
# =========================
fig = go.Figure()

# Background
fig.add_layout_image(
    dict(
        source=img,
        xref="x",
        yref="y",
        x=0,
        y=10,
        sizex=10,
        sizey=10,
        sizing="stretch",
        layer="below"
    )
)

# Scatter
fig.add_trace(go.Scatter(
    x=filtered_df["Performance"],
    y=filtered_df["Potential"],
    mode="markers",
    marker=dict(size=10, color="blue"),
    text=filtered_df["Nama"],
    hovertemplate=
    "<b>%{text}</b><br>" +
    "Performance: %{x}<br>" +
    "Potential: %{y}<extra></extra>"
))

# AXIS (BALANCED)
fig.update_xaxes(
    range=[0, 10],
    title="N. Performance",
    showgrid=False,
    zeroline=False,
    ticks="outside"
)

fig.update_yaxes(
    range=[0, 10],
    title="N. Potential",
    showgrid=False,
    zeroline=False,
    scaleanchor="x",
    ticks="outside"
)

# LAYOUT (BIAR GA GEDE PADDING)
fig.update_layout(
    height=720,
    width=720,
    margin=dict(l=40, r=20, t=20, b=40),  # kasih sedikit space buat axis
)

st.plotly_chart(fig, use_container_width=False)

# =========================
# TABLE
# =========================
st.subheader("📋 Talent Data")

st.dataframe(
    filtered_df[[
        "Brand", "Kota", "Outlet", "Job Level",
        "NIK", "Nama", "Category"
    ]],
    use_container_width=True
)