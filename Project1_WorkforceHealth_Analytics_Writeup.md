# Project: Workforce Health Analytics Dashboard — Occupational Health & Safe Return-to-Work

**Prepared by:** Nicholas Steven
**Target Role:** Data Specialist / Population Health Analytics Lead — Trillium Health Partners
**GitHub Repo:** https://github.com/nicholasstevenr/TrilliumHealthPartners-health-data-project
**Looker Studio Link:** [Pending publish — THP Workforce Health Dashboard]

---

## Problem Statement

People Health & Wellbeing teams at large multi-site hospital systems like Trillium Health Partners must track workforce occupational health outcomes across hundreds of staff: sick leave rates, workplace injury claims, return-to-work (RTW) program success rates, and accommodation timelines. Without automated reporting, People Health teams spend significant time manually extracting and formatting data from HRIS, WSIB claim logs, and accommodation tracking spreadsheets — leaving little time for actual analysis or program improvement. This project built a workforce health analytics dashboard automating these data flows and surfacing actionable workforce health KPIs by department, site, and employee type.

---

## Approach

1. **Data integration:** Merged three data streams: HRIS attendance records (sick leave events by employee/department), WSIB claim log (injury type, days lost, claim status, RTW date), and accommodation tracking register (accommodation type, start date, resolved/ongoing status).
2. **Sick leave rate KPIs:** Computed sick leave rate (days lost / days available × 100) by department, site, and full-time vs. part-time status; trended monthly over 24 months; benchmarked against Ontario Health sector average (8.5 days/FTE/year).
3. **WSIB claims analysis:** Categorized claims by mechanism of injury (musculoskeletal, needlestick, patient handling, slip/fall) and department; computed claim frequency rate per 200,000 hours worked (WSIB standard); tracked average days-to-RTW by injury type.
4. **Return-to-work program outcomes:** Computed RTW success rate (returned within modified duties timeline) vs. prolonged absence (>60 days); logistic regression identifying claim characteristics associated with prolonged absence.
5. **Accommodation load analysis:** Tracked open vs. resolved accommodations by department; flagged departments with disproportionately high open accommodation backlogs relative to department size.
6. **SPC monitoring:** Applied XmR control charts to monthly sick leave rates per department to distinguish signal (program-worthy trend) from noise.

---

## Tools Used

- **Python (pandas, numpy, scipy, statsmodels):** KPI computation, claim frequency rates, RTW logistic regression, SPC XmR
- **Excel:** Formatted People Health quarterly report for Trillium Health Partners leadership and JHSCs
- **Looker Studio:** Sick leave trend dashboard, WSIB claims heat map, accommodation load tracker, SPC chart per department

---

## Measurable Outcome / Impact

- Sick leave analysis identified 3 departments with rates >2 SD above the hospital average, prompting targeted ergonomic and workload review — the earliest such signal in 18 months of manual reporting
- WSIB frequency rate showed patient handling injuries accounted for 44% of all claims but were concentrated in 2 wards, focusing safe patient handling intervention resources efficiently
- RTW logistic regression identified claims with >14 days initial absence as strongest predictor of prolonged RTW (OR 3.8, 95% CI 2.1–6.9), supporting early intervention protocol design
- Dashboard reduced People Health quarterly reporting prep time from 2 days to 3 hours
