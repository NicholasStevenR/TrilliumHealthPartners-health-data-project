"""
Population Health Performance Analytics — THP Community Catchment
Author: Nicholas Steven
Repo: github.com/nicholasstevenr/TrilliumHealthPartners-health-data-project

ACSC hospitalization rates, ED utilization, age standardization,
ON-Marg deprivation overlay, and 3-year demand projection.
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

THP_FSAS = ["L4W","L4X","L4Y","L4Z","L5A","L5B","L5C","L5E","L5G","L5H",
            "L5J","L5K","L5L","L5M","L5N","L5R","L5S","L5T","L5V","L5W",
            "M8W","M8X","M8Y","M8Z","M9A","M9B","M9C"]

ACSC_ICD10 = {
    "diabetes_complications": ["E10","E11","E14"],
    "copd":                   ["J41","J42","J43","J44"],
    "chf":                    ["I50"],
    "hypertension":           ["I10","I11"],
    "asthma":                 ["J45","J46"],
}

STATCAN_AGE_BANDS = ["0-4","5-14","15-24","25-44","45-64","65-74","75-84","85+"]
STATCAN_STD_POP   = [5.4, 11.0, 13.5, 27.3, 24.8, 8.3, 6.8, 2.9]  # StatsCan 2016 %


# ── Load ──────────────────────────────────────────────────────────────────────

def load(hosp_path: str, pop_path: str, onmarg_path: str):
    hosp   = pd.read_csv(hosp_path, parse_dates=["admission_date"])
    pop    = pd.read_csv(pop_path)   # fsa, fiscal_year, age_band, population
    onmarg = pd.read_csv(onmarg_path)  # fsa, material_dep_q, res_instability_q
    hosp   = hosp[hosp["patient_fsa"].isin(THP_FSAS)]
    pop    = pop[pop["fsa"].isin(THP_FSAS)]
    print(f"Hospitalisations: {len(hosp):,}  |  Pop records: {len(pop):,}")
    return hosp, pop, onmarg


# ── 1. ACSC Hospitalization Rate ──────────────────────────────────────────────

def acsc_rate(hosp: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    all_acsc = [code for codes in ACSC_ICD10.values() for code in codes]
    hosp["acsc_category"] = None
    for cat, codes in ACSC_ICD10.items():
        mask = hosp["primary_dx_icd10"].str[:3].isin(codes)
        hosp.loc[mask, "acsc_category"] = cat

    hosp_acsc = hosp[hosp["acsc_category"].notna()]
    total_pop_by_fsa = (
        pop.groupby(["fsa","fiscal_year"])["population"].sum().reset_index()
    )
    acsc_counts = (
        hosp_acsc.groupby(["patient_fsa","fiscal_year","acsc_category"])
        .size().reset_index(name="n_acsc")
        .rename(columns={"patient_fsa":"fsa"})
        .merge(total_pop_by_fsa, on=["fsa","fiscal_year"], how="left")
    )
    acsc_counts["acsc_rate_per_1000"] = (
        acsc_counts["n_acsc"] / acsc_counts["population"].replace(0, np.nan) * 1000
    ).round(3)
    return acsc_counts


# ── 2. Direct Age Standardization ────────────────────────────────────────────

def age_standardized_rate(hosp: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    std_weights = dict(zip(STATCAN_AGE_BANDS, [w/100 for w in STATCAN_STD_POP]))
    hosp["age_band"] = pd.cut(
        hosp["patient_age"].fillna(-1),
        bins=[-1, 4, 14, 24, 44, 64, 74, 84, 200],
        labels=STATCAN_AGE_BANDS
    ).astype(str)

    results = []
    for fsa in THP_FSAS:
        fsa_hosp = hosp[hosp["patient_fsa"] == fsa]
        fsa_pop  = pop[pop["fsa"] == fsa]
        if len(fsa_hosp) == 0 or len(fsa_pop) == 0:
            continue
        asr_components = []
        for band in STATCAN_AGE_BANDS:
            band_n    = (fsa_hosp["age_band"] == band).sum()
            band_pop  = fsa_pop[fsa_pop["age_band"] == band]["population"].sum()
            if band_pop > 0:
                band_rate = band_n / band_pop
                asr_components.append(band_rate * std_weights.get(band, 0))
        asr = sum(asr_components) * 1000
        crude_rate = len(fsa_hosp) / max(fsa_pop["population"].sum(), 1) * 1000
        results.append({"fsa": fsa, "crude_rate_per_1000": round(crude_rate, 3),
                         "age_standardized_rate_per_1000": round(asr, 3)})
    return pd.DataFrame(results)


# ── 3. Deprivation Gradient ───────────────────────────────────────────────────

def deprivation_gradient(acsc_df: pd.DataFrame, onmarg: pd.DataFrame) -> pd.DataFrame:
    merged = (
        acsc_df.groupby("fsa")["acsc_rate_per_1000"].mean().reset_index()
        .merge(onmarg[["fsa","material_dep_q","res_instability_q"]], on="fsa", how="left")
    )
    gradient = (
        merged.groupby("material_dep_q")["acsc_rate_per_1000"]
        .agg(["mean","median","count"]).round(3).reset_index()
    )
    # Spearman correlation: deprivation vs. ACSC rate
    if merged["material_dep_q"].notna().sum() >= 5:
        r, p = stats.spearmanr(merged["material_dep_q"].dropna(),
                                merged.loc[merged["material_dep_q"].notna(), "acsc_rate_per_1000"])
        print(f"\n── Deprivation-ACSC Correlation: r={r:.3f}, p={p:.4f} ──")
    return gradient


# ── 4. 3-Year Demand Projection ───────────────────────────────────────────────

def demand_projection(acsc_df: pd.DataFrame, pop: pd.DataFrame,
                       growth_rate_pct: float = 2.5) -> pd.DataFrame:
    """Project ACSC demand 3 years forward using population growth × current rate."""
    current_rate = (
        acsc_df[acsc_df["fiscal_year"] == acsc_df["fiscal_year"].max()]
        .groupby("fsa")["acsc_rate_per_1000"].mean().reset_index()
    )
    current_pop = (
        pop[pop["fiscal_year"] == pop["fiscal_year"].max()]
        .groupby("fsa")["population"].sum().reset_index()
    )
    proj = current_rate.merge(current_pop, on="fsa", how="left")
    proj["current_acsc_n"] = proj["acsc_rate_per_1000"] / 1000 * proj["population"]
    for yr in [1, 2, 3]:
        multiplier = (1 + growth_rate_pct / 100) ** yr
        proj[f"projected_n_yr{yr}"] = (proj["current_acsc_n"] * multiplier).round(0)
    proj["pct_increase_3yr"] = (
        (proj["projected_n_yr3"] - proj["current_acsc_n"]) / proj["current_acsc_n"].replace(0, np.nan) * 100
    ).round(1)
    proj["flag_high_growth"] = proj["pct_increase_3yr"] > 15
    print(f"\n── Demand Projection — FSAs >15% growth in 3yr: {proj['flag_high_growth'].sum()} ──")
    return proj.sort_values("pct_increase_3yr", ascending=False)


# ── Export ────────────────────────────────────────────────────────────────────

def export_all(results: dict, outdir: str = "output") -> None:
    import os; os.makedirs(outdir, exist_ok=True)
    for name, df in results.items():
        if isinstance(df, pd.DataFrame) and len(df):
            df.to_csv(f"{outdir}/{name}.csv", index=False)
            print(f"  Exported → output/{name}.csv")


if __name__ == "__main__":
    hosp, pop, onmarg = load(
        "data/thp_hospitalizations_synthetic.csv",
        "data/thp_fsa_population.csv",
        "data/thp_onmarg_quintiles.csv",
    )
    acsc_df    = acsc_rate(hosp, pop)
    asr_df     = age_standardized_rate(hosp, pop)
    depriv_df  = deprivation_gradient(acsc_df, onmarg)
    proj_df    = demand_projection(acsc_df, pop)
    export_all({"acsc_rates": acsc_df, "age_standardized_rates": asr_df,
                "deprivation_gradient": depriv_df, "demand_projection": proj_df})
