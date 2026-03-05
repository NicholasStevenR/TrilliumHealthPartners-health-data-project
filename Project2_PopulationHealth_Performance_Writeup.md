# Project: Population Health Performance Analytics — THP Community Catchment Dashboard

**Prepared by:** Nicholas Steven
**Target Role:** Data Specialist / Population Health Analytics Lead — Trillium Health Partners
**GitHub Repo:** https://github.com/nicholasstevenr/TrilliumHealthPartners-health-data-project
**Looker Studio Link:** [Pending publish — THP Population Health Performance Dashboard]

---

## Problem Statement

Trillium Health Partners serves Mississauga, Brampton, and West Toronto — one of the fastest-growing, most diverse urban catchment areas in Canada. Performance Analytics teams need to track population-level health indicators for THP's served communities: chronic disease hospitalization rates, ACSC avoidable admissions, and ED utilization — stratified by neighbourhood and social determinants — to align hospital capacity planning with population health trends and to support community benefit reporting to Mississauga Halton LHIN. This project built a catchment-level population health performance dashboard for THP's three sites.

---

## Approach

1. **Catchment mapping:** Identified FSAs corresponding to THP's primary catchment (Credit Valley Hospital, Mississauga Hospital, Queensway Health Centre) using 80%-catchment rule from patient postal code data.
2. **Chronic disease hospitalization (ACSC rate):** Computed ambulatory care sensitive condition (ACSC) hospitalization rates per 1,000 catchment population by FSA for 5 ACSC categories: diabetes complications, COPD, CHF, hypertension, asthma.
3. **ED utilization by acuity:** Computed CTAS 4-5 (non-urgent) visit rates per 1,000 population by FSA as a primary care access proxy; trended over 3 years.
4. **Population demographics:** Projected catchment population growth by FSA using Statistics Canada growth rates; computed age-adjusted hospitalization rates to control for the catchment's aging population.
5. **Social determinants overlay:** Joined ON-Marg deprivation index quintiles (material deprivation, residential instability) to each FSA; computed ACSC rate gradient across deprivation quintiles.
6. **Scenario planning:** Modelled projected ACSC demand 3 years forward based on population growth × current age-adjusted rates; flagged FSAs expected to generate >15% increase in hospitalizations.

---

## Tools Used

- **Python (pandas, numpy, scipy, geopandas):** ACSC rate computation, direct age standardization, ON-Marg quintile merge, growth projection
- **Statistics Canada / ON-Marg:** Population projections and deprivation index data (public datasets)
- **Looker Studio:** FSA-level choropleth map, ACSC rate trend, deprivation gradient chart, demand projection
- **Excel:** Formatted population health summary for Mississauga Halton LHIN community benefit reporting

---

## Measurable Outcome / Impact

- ACSC analysis identified 4 FSAs with CHF hospitalization rates >40% above the THP catchment average, all in the highest material deprivation quintile — pointing to targeted chronic disease management program investment
- Avoidable ED visit rate was 2.3× higher in the bottom deprivation quintile vs. top quintile, quantifying the primary care access gap in THP's most vulnerable communities
- 3-year demand projection flagged 2 high-growth FSAs expected to generate 18–22% more ACSC hospitalizations, informing THP's capital planning cycle
- Age standardization revealed that Brampton's apparently higher crude ACSC rate was fully explained by younger age structure; Mississauga's age-adjusted rate was the true outlier
