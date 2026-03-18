import streamlit as st
import pandas as pd
import os
import re

# =========================
# ACCESS CONTROL
# =========================
if "role" not in st.session_state or st.session_state.role is None:
    st.warning("⚠️ Please select your role first.")
    st.stop()

if st.session_state.role not in ["HR", "Supervisor", "Manager"]:
    st.error("⛔ You do not have access to this page.")
    st.stop()

# =========================
# TITLE
# =========================
st.title("📊 Master Data Talent")

MASTER_PATH = "data/master_data.csv"
ASSESS_PATH = "data/assessment_data.csv"
STORE_KOTA_PATH = "data/store_kota_mapping.csv"

# =========================
# LOAD DATA
# =========================
master_df = pd.read_csv(MASTER_PATH)

if os.path.exists(ASSESS_PATH):
    try:
        assess_df = pd.read_csv(ASSESS_PATH)
        if assess_df.empty:
            st.warning("⚠️ Assessment data is empty")
    except pd.errors.EmptyDataError:
        st.warning("⚠️ Assessment file kosong, pakai template kosong")
        assess_df = pd.DataFrame(columns=[
            "NIK","KPI","PA360","Psikogram",
            "Competency","OBP","SOP","Wellness"
        ])
else:
    assess_df = pd.DataFrame(columns=[
        "NIK","KPI","PA360","Psikogram",
        "Competency","OBP","SOP","Wellness"
    ])

store_kota_df = pd.read_csv(STORE_KOTA_PATH)

# =========================
# FILTER RAW DATA
# =========================

# Filter Department (Operation Store brand tertentu)
dept_pattern = r"Operation.*(AX|CK|EA7|Pedro|Pomelo)"
mask_dept = master_df["Department"].str.contains(dept_pattern, regex=True, na=False)

# Filter Job Title
job_pattern = r"Asst\. Store Head|Sr\. Sales Associate|Sales Associate|Asst\. Spv\. Store|Spv\. Store|Full Store Head"
mask_job = master_df["Jobtitle"].str.contains(job_pattern, regex=True, na=False)

# Apply filter
master_df = master_df[mask_dept & mask_job]

# =========================
# CLEANING
# =========================
master_df["Outlet"] = master_df["Outlet"].str.strip()
store_kota_df["Outlet"] = store_kota_df["Outlet"].str.strip()

# =========================
# TRANSFORM MASTER DATA
# =========================

# Rename kolom
master_df = master_df.rename(columns={
    "Name": "Nama",
    "Jobtitle": "JobTitle",
    "Join Date": "JoinDate"
})

# =========================
# BRAND (dari Department)
# =========================
def extract_brand(dept):
    if pd.isna(dept):
        return None
    parts = str(dept).split()
    return parts[-1] if len(parts) >= 2 else None

master_df["Brand"] = master_df["Department"].apply(extract_brand)

# =========================
# KOTA (dari mapping CSV)
# =========================
master_df = pd.merge(
    master_df,
    store_kota_df,
    on="Outlet",
    how="left"
)

# =========================
# JOB LEVEL
# =========================
JOB_LEVEL_MAP = {
    "Sales Associate": "SA",
    "Sales Associate B": "SA",
    "Sr. Sales Associate": "SSA",
    "Sr. Sales Associate B": "SSA",
    "Asst. Spv. Store": "ASPV",
    "Asst. Spv. Store B": "ASPV",
    "Spv. Store": "SPV",
    "Spv. Store B": "SPV",
    "Asst. Store Head": "ASM",
    "Asst. Store Head B": "ASM",
    "Full Store Head": "SM",
    "Full Store Head B": "SM"
}

master_df["Job Level"] = master_df["JobTitle"].map(JOB_LEVEL_MAP)

# =========================
# MERGE ASSESSMENT
# =========================
df = pd.merge(master_df, assess_df, on="NIK", how="left")

# =========================
# SAFE AVG
# =========================
def safe_avg(values):
    valid = [v for v in values if pd.notna(v)]
    return sum(valid) / len(valid) if valid else None

# =========================
# DETECT STORE / HO
# =========================
def is_store(row):
    return "Operation Store" in str(row.get("Department", ""))

# =========================
# CALCULATION
# =========================
def calculate_scores(row):
    perf = safe_avg([row.get("KPI"), row.get("PA360")])
    obp_sop = safe_avg([row.get("OBP"), row.get("SOP")])

    if is_store(row):
        pot = safe_avg([
            row.get("Psikogram"),
            row.get("Competency"),
            obp_sop
        ])
        overall = safe_avg([perf, pot])
    else:
        pot = safe_avg([
            row.get("Psikogram"),
            row.get("Competency"),
            obp_sop,
            row.get("Wellness")
        ])
        overall = (0.4 * perf + 0.6 * pot) if perf and pot else None

    return pd.Series([perf, pot, overall])

df[["Performance", "Potential", "Overall"]] = df.apply(calculate_scores, axis=1)

# =========================
# CATEGORY RULES
# =========================
CATEGORY_RULES = [
    ("Future Leader", "0–1 years", 8, 10, 8, 10),
    ("High Performer", "0–1 years", 8, 10, 6, 8),
    ("Expert", "0–1 years", 8, 10, 0, 6),
    ("Emerging Talent", "0–1 years", 6, 8, 8, 10),
    ("Solid Contributor", "1–3 years", 6, 8, 6, 8),
    ("Underutilized", "1–3 years", 6, 8, 0, 6),
    ("High Risk", "1–3 years", 0, 6, 8, 10),
    ("Inconsistent Performance", "1–3 years", 0, 6, 6, 8),
    ("Low Performer", "3–5 years", 0, 6, 0, 6),
]

def map_category(perf, pot):
    if pd.isna(perf) or pd.isna(pot):
        return None, None

    for cat, ready, pmin, pmax, tmin, tmax in CATEGORY_RULES:
        if pmin <= perf <= pmax and tmin <= pot <= tmax:
            return cat, ready

    return None, None

df[["Category", "Readiness Index"]] = df.apply(
    lambda row: pd.Series(map_category(row["Performance"], row["Potential"])),
    axis=1
)

# =========================
# SIDEBAR FILTER (PAKAI DATA HASIL TRANSFORM)
# =========================
st.sidebar.subheader("🔍 Filter")

brand = st.sidebar.selectbox("Brand", ["All"] + sorted(df["Brand"].dropna().unique()))
kota = st.sidebar.selectbox("Kota", ["All"] + sorted(df["Kota"].dropna().unique()))
job = st.sidebar.selectbox("Job Level", ["All"] + sorted(df["Job Level"].dropna().unique()))

filtered_df = df.copy()

if brand != "All":
    filtered_df = filtered_df[filtered_df["Brand"] == brand]

if kota != "All":
    filtered_df = filtered_df[filtered_df["Kota"] == kota]

if job != "All":
    filtered_df = filtered_df[filtered_df["Job Level"] == job]

# =========================
# DISPLAY
# =========================
st.subheader("📋 Talent Data")

st.dataframe(
    filtered_df[[
        "NIK", "Nama", "Brand", "JobTitle", "Job Level", "Grade",
        "Outlet", "Kota", "JoinDate",
        "KPI", "PA360", "Psikogram", "Competency",
        "OBP", "SOP", "Wellness",
        "Performance", "Potential", "Overall",
        "Category", "Readiness Index"
    ]],
    use_container_width=True,
    column_config={
        "NIK": st.column_config.Column(pinned=True),
        "Nama": st.column_config.Column(pinned=True),
        "Brand": st.column_config.Column(pinned=True),
    }
)