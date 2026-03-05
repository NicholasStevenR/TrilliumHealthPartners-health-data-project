"""
Workforce Health Analytics Dashboard — Trillium Health Partners
Author: Nicholas Steven
Target Role: Data Specialist / Population Health Analytics Lead — THP
Repo: github.com/nicholasstevenr/TrilliumHealthPartners-health-data-project

Sick leave KPIs, WSIB claim frequency rates, RTW outcomes,
accommodation load analysis, and SPC XmR monitoring.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

ONTARIO_HEALTH_SECTOR_AVG_DAYS = 8.5   # sick days per FTE per year benchmark
WSIB_HOURS_BASE = 200_000              # WSIB claim frequency rate denominator
PROLONGED_ABSENCE_DAYS = 60           # threshold for "prolonged" RTW
ACCOMMODATION_FLAG_THRESHOLD = 0.10   # flag depts with >10% staff on open accommodation


# ── Load ──────────────────────────────────────────────────────────────────────

def load(hris_path: str, wsib_path: str, accom_path: str):
    hris  = pd.read_csv(hris_path,  parse_dates=["leave_start","leave_end"])
    wsib  = pd.read_csv(wsib_path,  parse_dates=["injury_date","rtw_date","claim_close_date"])
    accom = pd.read_csv(accom_path, parse_dates=["accom_start","accom_resolved_date"])
    print(f"HRIS events: {len(hris):,}  |  WSIB claims: {len(wsib):,}  |  Accommodations: {len(accom):,}")
    return hris, wsib, accom


# ── 1. Sick Leave Rate KPIs ────────────────────────────────────────────────────

def sick_leave_kpis(hris: pd.DataFrame) -> pd.DataFrame:
    hris["leave_days"] = (hris["leave_end"] - hris["leave_start"]).dt.days.clip(lower=0) + 1
    hris["period"]     = hris["leave_start"].dt.to_period("M").astype(str)

    kpis = (
        hris.groupby(["department","site_code","employee_type","period"])
        .agg(
            total_sick_days  = ("leave_days", "sum"),
            n_employees      = ("employee_id", "nunique"),
            n_leave_events   = ("leave_days", "count"),
        )
        .reset_index()
    )
    # Sick leave rate per FTE per period (annualised)
    kpis["sick_leave_rate_annualised"] = (kpis["total_sick_days"] / kpis["n_employees"] * 12).round(2)
    kpis["above_benchmark"] = kpis["sick_leave_rate_annualised"] > ONTARIO_HEALTH_SECTOR_AVG_DAYS

    dept_summary = (
        kpis.groupby("department")
        .agg(avg_sl_rate=("sick_leave_rate_annualised","mean"),
             pct_periods_above=("above_benchmark","mean"))
        .round(2).reset_index()
        .sort_values("avg_sl_rate", ascending=False)
    )
    print(f"\n── Sick Leave KPIs (top depts) ──")
    print(dept_summary.head(5).to_string(index=False))
    return kpis, dept_summary


# ── 2. WSIB Claim Frequency Rate ──────────────────────────────────────────────

def wsib_frequency_rate(wsib: pd.DataFrame, hris: pd.DataFrame) -> pd.DataFrame:
    # Total hours worked per dept (approx from HRIS: FTEs × FTE_hours)
    dept_fte = hris.groupby("department")["employee_id"].nunique().reset_index(name="n_fte")
    dept_fte["hours_worked"] = dept_fte["n_fte"] * 1950   # ~1950h/FTE/year

    claim_counts = (
        wsib.groupby(["department","injury_mechanism"])
        .size().reset_index(name="n_claims")
    )
    freq = claim_counts.merge(dept_fte, on="department", how="left")
    freq["frequency_rate"] = (freq["n_claims"] / freq["hours_worked"].replace(0, np.nan) * WSIB_HOURS_BASE).round(2)

    top_mechanisms = (
        wsib.groupby("injury_mechanism")
        .agg(n=("injury_mechanism","count"),
             avg_days_lost=("days_lost","mean"))
        .round(1).reset_index()
        .sort_values("n", ascending=False)
    )
    print(f"\n── WSIB Injury Mechanisms ──")
    print(top_mechanisms.to_string(index=False))
    return freq, top_mechanisms


# ── 3. Return-to-Work Outcomes ─────────────────────────────────────────────────

def rtw_outcomes(wsib: pd.DataFrame) -> tuple:
    wsib["days_to_rtw"] = (wsib["rtw_date"] - wsib["injury_date"]).dt.days.clip(lower=0)
    wsib["prolonged_absence"] = wsib["days_to_rtw"] > PROLONGED_ABSENCE_DAYS

    rtw_by_type = (
        wsib.groupby("injury_mechanism")
        .agg(n=("days_to_rtw","count"),
             median_rtw_days=("days_to_rtw","median"),
             prolonged_pct=("prolonged_absence","mean"))
        .round(2).reset_index()
    )
    rtw_by_type["prolonged_pct"] = (rtw_by_type["prolonged_pct"] * 100).round(1)

    # Logistic regression: prolonged RTW predictors
    feature_cols = ["days_lost_initial","severity_score","department_encoded"]
    if all(c in wsib.columns for c in ["days_lost_initial","severity_score"]):
        wsib["department_encoded"] = pd.Categorical(wsib["department"]).codes
        model_df = wsib[feature_cols + ["prolonged_absence"]].dropna()
        if len(model_df) >= 30:
            X = StandardScaler().fit_transform(model_df[feature_cols].values)
            y = model_df["prolonged_absence"].astype(int).values
            lr = LogisticRegression(max_iter=300, random_state=42)
            lr.fit(X, y)
            coef_df = pd.DataFrame({
                "feature":     feature_cols,
                "odds_ratio":  np.exp(lr.coef_[0]).round(3)
            }).sort_values("odds_ratio", ascending=False)
            print(f"\n── RTW Logistic Regression ──")
            print(coef_df.to_string(index=False))
        else:
            coef_df = pd.DataFrame()
    else:
        coef_df = pd.DataFrame()

    print(f"\n── RTW by Injury Type ──")
    print(rtw_by_type.to_string(index=False))
    return rtw_by_type, coef_df


# ── 4. Accommodation Load ─────────────────────────────────────────────────────

def accommodation_load(accom: pd.DataFrame, hris: pd.DataFrame) -> pd.DataFrame:
    accom["is_open"] = accom["accom_resolved_date"].isna()
    dept_fte = hris.groupby("department")["employee_id"].nunique().reset_index(name="n_fte")

    accom_summary = (
        accom.groupby("department")
        .agg(total_accommodations=("is_open","count"),
             open_accommodations=("is_open","sum"))
        .reset_index()
        .merge(dept_fte, on="department", how="left")
    )
    accom_summary["open_pct_of_fte"] = (
        accom_summary["open_accommodations"] / accom_summary["n_fte"].replace(0, np.nan) * 100
    ).round(1)
    accom_summary["flag_high_load"] = (
        accom_summary["open_pct_of_fte"] > ACCOMMODATION_FLAG_THRESHOLD * 100
    )
    print(f"\n── Accommodation Load ──")
    flagged = accom_summary[accom_summary["flag_high_load"]]
    print(f"  Depts with >10% open accommodation rate: {len(flagged)}")
    return accom_summary


# ── 5. SPC XmR for Sick Leave ─────────────────────────────────────────────────

def spc_sick_leave(kpis: pd.DataFrame, department: str) -> pd.DataFrame:
    dept = kpis[kpis["department"] == department].sort_values("period")
    if len(dept) < 8:
        return pd.DataFrame()
    x = dept["sick_leave_rate_annualised"].values
    cl = x.mean()
    mr_bar = np.abs(np.diff(x)).mean()
    ucl = cl + 3 * mr_bar / 1.128
    lcl = max(0, cl - 3 * mr_bar / 1.128)
    chart = dept[["department","period","sick_leave_rate_annualised"]].copy()
    chart["cl"] = cl; chart["ucl"] = ucl; chart["lcl"] = lcl
    chart["signal"] = (chart["sick_leave_rate_annualised"] > ucl) | (chart["sick_leave_rate_annualised"] < lcl)
    print(f"\n── SPC XmR: {department} — signals: {chart['signal'].sum()} ──")
    return chart


# ── Export ────────────────────────────────────────────────────────────────────

def export_all(results: dict, outdir: str = "output") -> None:
    import os; os.makedirs(outdir, exist_ok=True)
    for name, df in results.items():
        if isinstance(df, pd.DataFrame) and len(df):
            df.to_csv(f"{outdir}/{name}.csv", index=False)
            print(f"  Exported → output/{name}.csv")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    hris, wsib, accom = load(
        "data/thp_hris_leave_synthetic.csv",
        "data/thp_wsib_claims_synthetic.csv",
        "data/thp_accommodations_synthetic.csv",
    )
    sl_kpis, sl_dept   = sick_leave_kpis(hris)
    freq_df, mech_df   = wsib_frequency_rate(wsib, hris)
    rtw_df, rtw_coef   = rtw_outcomes(wsib)
    accom_df           = accommodation_load(accom, hris)
    spc_df             = spc_sick_leave(sl_kpis, sl_dept["department"].iloc[0] if len(sl_dept) else "ICU")

    export_all({"sick_leave_kpis": sl_kpis, "sick_leave_dept_summary": sl_dept,
                "wsib_frequency": freq_df, "injury_mechanisms": mech_df,
                "rtw_outcomes": rtw_df, "accommodation_load": accom_df, "spc_sick_leave": spc_df})
