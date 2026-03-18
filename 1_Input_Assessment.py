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

if st.session_state.role not in ["HR", "Supervisor"]:
    st.error("⛔ You do not have access to this page.")
    st.stop()

# =========================
# TITLE
# =========================
st.title("📝 Input Assessment")

MASTER_PATH = "data/master_data.csv"
ASSESS_PATH = "data/assessment_data.csv"

# =========================
# LOAD MASTER DATA
# =========================
master_df = pd.read_csv(MASTER_PATH)

# =========================
# FILTER RAW (SAMA SEPERTI MASTER DATA)
# =========================
dept_pattern = r"Operation.*(AX|CK|EA7|Pedro|Pomelo)"
mask_dept = master_df["Department"].str.contains(dept_pattern, regex=True, na=False)

allowed_jobs = [
    "Asst. Store Head",
    "Sr. Sales Associate",
    "Sales Associate",
    "Asst. Spv. Store",
    "Spv. Store",
    "Full Store Head"
]

mask_job = master_df["Jobtitle"].isin(allowed_jobs)

master_df = master_df[mask_dept & mask_job]

# =========================
# RENAME
# =========================
master_df = master_df.rename(columns={
    "Name": "Nama",
    "Jobtitle": "JobTitle"
})

# =========================
# LOAD ASSESSMENT
# =========================
if os.path.exists(ASSESS_PATH):
    try:
        assess_df = pd.read_csv(ASSESS_PATH)
    except:
        assess_df = pd.DataFrame(columns=[
            "NIK","KPI","PA360","Psikogram",
            "Competency","OBP","SOP","Wellness"
        ])
else:
    assess_df = pd.DataFrame(columns=[
        "NIK","KPI","PA360","Psikogram",
        "Competency","OBP","SOP","Wellness"
    ])

# =========================
# FILTER SECTION
# =========================
st.subheader("🔍 Filter Employee")

col1, col2, col3 = st.columns(3)

with col1:
    brand_list = master_df["Department"].str.split().str[-1].dropna().unique()
    brand = st.selectbox("Brand", ["All"] + sorted(brand_list))

with col2:
    outlet = st.selectbox("Outlet", ["All"] + sorted(master_df["Outlet"].dropna().unique()))

with col3:
    job = st.selectbox("Job Title", ["All"] + sorted(master_df["JobTitle"].dropna().unique()))

filtered_df = master_df.copy()

if brand != "All":
    filtered_df = filtered_df[filtered_df["Department"].str.contains(brand)]

if outlet != "All":
    filtered_df = filtered_df[filtered_df["Outlet"] == outlet]

if job != "All":
    filtered_df = filtered_df[filtered_df["JobTitle"] == job]

# =========================
# SELECT EMPLOYEE
# =========================
st.subheader("👤 Select Employee")

if filtered_df.empty:
    st.warning("No employee found")
    st.stop()

employee = st.selectbox(
    "Choose Employee",
    filtered_df["NIK"] + " - " + filtered_df["Nama"]
)

selected_nik = employee.split(" - ")[0]

# =========================
# GET EXISTING DATA (IF ANY)
# =========================
existing_row = assess_df[assess_df["NIK"] == selected_nik]

def get_value(col):
    if not existing_row.empty:
        val = existing_row.iloc[0].get(col)
        return float(val) if pd.notna(val) else 0.0
    return 0.0

# =========================
# INPUT FORM
# =========================
st.subheader("📊 Input Scores")
st.info("📌 All scores must be between 0 and 10")

col1, col2, col3 = st.columns(3)

with col1:
    kpi = st.number_input("KPI (0–10)", 0.0, 10.0, step=0.1, value=get_value("KPI"))
    pa360 = st.number_input("PA360 (0–10)", 0.0, 10.0, step=0.1, value=get_value("PA360"))

with col2:
    psikogram = st.number_input("Psikogram (0–10)", 0.0, 10.0, step=0.1, value=get_value("Psikogram"))
    competency = st.number_input("Competency (0–10)", 0.0, 10.0, step=0.1, value=get_value("Competency"))

with col3:
    obp = st.number_input("OBP (0–10)", 0.0, 10.0, step=0.1, value=get_value("OBP"))
    sop = st.number_input("SOP (0–10)", 0.0, 10.0, step=0.1, value=get_value("SOP"))

# =========================
# STORE / HO CHECK
# =========================
employee_row = master_df[master_df["NIK"] == selected_nik].iloc[0]

is_store = "Operation Store" in str(employee_row["Department"])

if not is_store:
    wellness = st.number_input("Wellness (0–10)", 0.0, 10.0, step=0.1, value=get_value("Wellness"))
else:
    wellness = None

# =========================
# SAVE LOGIC (UPDATE, NOT DUPLICATE)
# =========================
if st.button("💾 Save Assessment"):

    new_data = {
        "NIK": selected_nik,
        "KPI": kpi,
        "PA360": pa360,
        "Psikogram": psikogram,
        "Competency": competency,
        "OBP": obp,
        "SOP": sop,
        "Wellness": wellness
    }

    # remove old row if exists
    assess_df = assess_df[assess_df["NIK"] != selected_nik]

    # append new
    assess_df = pd.concat([assess_df, pd.DataFrame([new_data])], ignore_index=True)

    assess_df.to_csv(ASSESS_PATH, index=False)

    st.success("✅ Data saved successfully!")