# JURY REVIEW — TAŞKIN Repository
## TÜBİTAK 2204 Technical Credibility Assessment

> This document is a structured adversarial review. It lists every gap that reduces jury confidence, with a ranked action plan.

---

## VERDICT SUMMARY

| Category | Status |
|---|---|
| System architecture documentation | ✅ Adequate |
| Component selection rationale | ⚠️ Partial — "why not alternatives" missing |
| Physical deployment evidence | ❌ No photos |
| Data visualization | ❌ No charts from field CSV |
| Code reproducibility | ✅ Adequate |
| TRİ score implementation | ✅ Script exists (`analysis/tri_score.py`) |
| Battery characterization | ✅ Added |
| Lab validation | ⚠️ Described, not photographed |
| Node naming consistency | ✅ Fixed |
| LICENSE | ✅ Present |

---

## 1. ENGINEERING WEAKNESSES

These are why this looks like a school project rather than an engineering submission.

### W-1 — No evidence of physical build beyond code
The repository contains firmware and a Python bridge. There is **zero photographic or measurement evidence** that any hardware was assembled, soldered, or deployed. A jury cannot distinguish this from a project that only ran in simulation.

**What it looks like:** A GitHub repo with Arduino code and some CSV files.
**What it should look like:** A repo where images prove the device exists, works, and was deployed at the claimed locations.

### W-2 — HC-SR04 in a flood monitoring system is the wrong sensor, and this is not acknowledged
HC-SR04 is an **indoor** ultrasonic sensor rated for dry environments. It has no IP rating. Mounting it in a drainage environment without waterproofing is an engineering error. The current README notes this as a "limitation" but does not explain what was done to mitigate it during field testing.

**What a jury asks:** "Did the sensor fail during rain? What readings did you get when rain drops hit the sensor face? Did you filter that noise?" These questions have no answers in the repo.

**Fix:** Add a section in README Section 11 explicitly describing: what physical protection (if any) was applied to the HC-SR04 face during field testing, and what the noise profile looked like in the CSV data.

### W-3 — "10–12 hours battery life" claim is not reproducible
The battery runtime is stated as "measured" but:
- No methodology is described (how was end-of-life defined? Voltage threshold? First dropout?)
- No raw discharge data is in the repo
- The current consumption per component is estimated, not measured with an ammeter

**What a jury sees:** A number with no methodology = unverifiable claim.
**Fix:** Document test method. Even a single sentence: "Runtime measured from full charge to first failed packet transmission. Test performed at room temperature."

### W-4 — ESP-NOW broadcast reliability in field is uncharacterized
In urban environments with concrete walls and RF interference, ESP-NOW packet delivery is not guaranteed. The README states "zero packet loss in lab" but:
- Lab test was in an open room, not in a concrete underpass
- No field packet loss rate is reported
- There is no packet sequence number in the transmitted struct, so loss cannot be detected post-hoc from the CSV

**What a jury asks:** "How do you know no data was lost in the field?" There is no answer.

### W-5 — TRİ weights are unjustified equal weights
The TRİ model uses `w = 0.20` for all five parameters with no justification. Equal weighting is a placeholder, not an engineering decision. A jury will ask why "max fill" and "mean fill" are equal weight when max fill is more directly correlated with infrastructure failure.

**Fix:** Add one paragraph in README Section 10 explicitly stating: "Equal weights were chosen as a baseline in the absence of domain-specific weighting data. Future work should apply AHP (Analytic Hierarchy Process) or expert elicitation to derive defensible weights."

### W-6 — CSV timestamps cannot be verified against claimed test windows
The report claims tests ran "11:00–14:00" and "16:00–19:00" on specific dates. The CSV `zaman_ms` column is milliseconds since boot — not wall clock time. There is no way a third party can verify the session times from the data alone.

**Fix:** Add a `session_log.csv` or `session_notes.md` file documenting: date, approximate start time, node ID active, and weather conditions per session. This costs 10 minutes to write and dramatically increases credibility.

---

## 2. MISSING PROOF

These are the specific gaps that make the system's operation unverifiable.

| # | Missing Item | What It Fails to Prove |
|---|---|---|
| P-1 | Field photos of any node | That hardware was deployed at Barajyolu, Turgut Özal, or Sinanpaşa |
| P-2 | Photo of sensor aimed at water surface | That the measurement geometry is correct |
| P-3 | Time-series chart from field CSV | That fill rates actually differed between locations |
| P-4 | Serial monitor screenshot during operation | That the software pipeline runs end-to-end |
| P-5 | Lab PVC pipe setup photo | That the ±4 cm accuracy claim was tested, not estimated |
| P-6 | Dashboard screenshot with live data | That `index.html` displays correctly with real data |
| P-7 | Session start/end log | That "9 Feb 11:00–14:00" is verifiable, not invented |
| P-8 | Packet loss report from field | That ESP-NOW worked reliably outside lab conditions |

---

## 3. QUICK FIX PRIORITY LIST

Ordered by impact-per-effort. Do these in order.

### Priority 1 — Generate and commit a time-series chart from field CSV
**Effort:** 30 minutes (Python matplotlib)
**Impact:** Single highest-credibility action. Turns "we got data" into "here is what the data shows."
**How:** Extend `analysis/tri_score.py` to output a 3-node fill rate line chart. Save to `images/field_timeseries.png`. Reference in README Section 10.

### Priority 2 — Add `data/session_log.md` with test session metadata
**Effort:** 10 minutes
**Impact:** Makes CSV timestamps verifiable. Turns unverifiable time claims into documented sessions.
**Content:** Date, start time, node ID, location, weather, approximate rainfall, session duration.

### Priority 3 — Photograph the lab PVC pipe setup
**Effort:** 10 minutes (if hardware is still accessible)
**Impact:** Validates the ±4 cm accuracy claim. Without this, the lab results section is unverifiable.
**Requirement:** Sensor mounted above pipe, ruler visible, water level visible.

### Priority 4 — Take a screenshot of `server.py` terminal output during operation
**Effort:** 5 minutes
**Impact:** Proves the software pipeline is functional end-to-end.
**Requirement:** Terminal showing `[Data] Node 1 → 63.5% alarm=0 @ 14:32:10` style lines.

### Priority 5 — Photograph at least one node in its enclosure (exterior)
**Effort:** 10 minutes
**Impact:** Proves hardware exists. Even a closed IP67 box on a table is more credible than no photo.

### Priority 6 — Add a paragraph to README Section 11 on HC-SR04 noise mitigation
**Effort:** 5 minutes
**Impact:** Turns an unacknowledged engineering flaw into a documented and addressed limitation.

### Priority 7 — Add methodology note to battery runtime claim
**Effort:** 2 minutes
**Impact:** Turns an unverifiable number into a documented measurement.

---

## 4. WHAT WOULD CHANGE THE JURY'S DECISION

In order of importance:

1. **A field photo of any node near water** — proves real deployment
2. **A fill rate chart from the CSV** — proves data is meaningful, not just rows
3. **A serial monitor screenshot** — proves software works
4. **`data/session_log.md`** — makes timeline verifiable

Without items 1–3, the jury has only claims and code. With them, it becomes an engineering project.
