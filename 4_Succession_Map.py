import streamlit as st
import pandas as pd
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
st.title("🎯 Succession Map")

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
    "Jobtitle": "JobTitle"
})

# Brand
master_df["Division/Brand"] = master_df["Department"].str.split().str[-1]

# Kota
master_df = pd.merge(master_df, store_kota_df, on="Outlet", how="left")

# Job Level Mapping
JOB_LEVEL_MAP = {
    "Sales Associate": "SA",
    "Sr. Sales Associate": "SSA",
    "Asst. Spv. Store": "ASPV",
    "Spv. Store": "SPV",
    "Asst. Store Head": "ASM",
    "Full Store Head": "SM"
}

JOB_LEVEL_ORDER = {
    "SA": 1,
    "SSA": 2,
    "ASPV": 3,
    "SPV": 4,
    "ASM": 5,
    "SM": 6
}

master_df["Job Level"] = master_df["JobTitle"].map(JOB_LEVEL_MAP)
master_df["Level Rank"] = master_df["Job Level"].map(JOB_LEVEL_ORDER)

# =========================
# FILTER STORE ONLY
# =========================
dept_pattern = r"Operation.*(AX|CK|EA7|Pedro|Pomelo)"
master_df = master_df[master_df["Department"].str.contains(dept_pattern, regex=True, na=False)]

# =========================
# MERGE ASSESSMENT
# =========================
df = pd.merge(master_df, assess_df, on="NIK", how="left")

# =========================
# ONLY DATA WITH KPI
# =========================
df = df[df["KPI"].notna()]

# =========================
# CALCULATE PERFORMANCE & POTENTIAL
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

# =========================
# CATEGORY & READINESS (MATCH 9 BOX SIMPLE)
# =========================
def category(perf, pot):
    if perf >= 8 and pot >= 8:
        return "Future Leader", "0–1 years"
    elif perf >= 8:
        return "High Performer", "0–1 years"
    elif pot >= 8:
        return "Emerging Talent", "0–1 years"
    elif perf < 6 and pot < 6:
        return "Low Performer", "3–5 years"
    else:
        return "Solid Contributor", "1–3 years"

df[["Category", "Readiness Index"]] = df.apply(
    lambda x: pd.Series(category(x["Performance"], x["Potential"])),
    axis=1
)

# =========================
# GENERATE SUCCESSION MAP
# =========================
results = []

group_cols = ["Division/Brand", "Kota", "Job Level"]

for (brand, kota, job), group in df.groupby(group_cols):

    # ❌ skip SA (no successor)
    if job == "SA":
        continue

    # =========================
    # CRITICAL ROLE (TOP KPI)
    # =========================
    critical = group.sort_values("KPI", ascending=False).iloc[0]

    current_rank = critical["Level Rank"]
    lower_rank = current_rank - 1

    # =========================
    # SUCCESSOR CANDIDATES
    # =========================
    candidates = df[
        (df["Division/Brand"] == brand) &
        (df["Kota"] == kota) &
        (df["Level Rank"] == lower_rank)
    ].sort_values("KPI", ascending=False)

    top3 = candidates.head(3)

    names = top3["Nama"].tolist()
    names += [None] * (3 - len(names))

    # =========================
    # STATUS
    # =========================
    if len(top3) == 0:
        status = "Belum ada kandidat"
    else:
        status = f"Ada {len(top3)} kandidat potensial"

    results.append({
        "Division/Brand": brand,
        "Posisi Kritis": job,
        "Kota": kota,
        "NIK": critical["NIK"],
        "Nama": critical["Nama"],
        "Potential Successor 1": names[0],
        "Potential Successor 2": names[1],
        "Potential Successor 3": names[2],
        "Status Kandidat": status,
        "Readiness Index": critical["Readiness Index"],
        "Catatan / Rencana Pengembangan": critical["Category"]
    })

succession_df = pd.DataFrame(results)

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.subheader("🔍 Filter")

brand_filter = st.sidebar.selectbox(
    "Brand", ["All"] + sorted(succession_df["Division/Brand"].dropna().unique())
)

if brand_filter != "All":
    succession_df = succession_df[succession_df["Division/Brand"] == brand_filter]

# =========================
# DISPLAY
# =========================
st.dataframe(succession_df, use_container_width=True)