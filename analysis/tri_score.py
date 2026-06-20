#!/usr/bin/env python3
"""
tri_score.py — TAŞKIN Risk İndeksi (TRİ) Calculator + Chart Generator

Reads all CSV files from data/samples/, computes a composite TRİ score
(0–100) per measurement node from five risk parameters, prints a ranked
risk table, and optionally saves a time-series fill-rate chart.

Two scoring methods are provided and BOTH are printed by default:

  • min-max : each parameter is min-max normalized ACROSS nodes (relative
              ranking). Useful to compare nodes within one dataset.
  • hybrid  : each parameter blends an ABSOLUTE anchored score (fixed 0–100
              scale, dataset-independent) with the relative min-max score.
              Scores stay interpretable and the lowest node is not forced
              to 0 the way pure min-max does.

Risk parameters (all "higher = more risk" AFTER direction correction):
    1. mean fill (%)
    2. max fill (%)
    3. time spent above 80% (as % of samples — fair across session lengths)
    4. 80% upward-crossing frequency (per hour)
    5. peak fill-rise rate (fastest filling over any 60 s window; faster = more risk)

Usage:
    python analysis/tri_score.py                      # both score tables
    python analysis/tri_score.py --method hybrid      # one method only
    python analysis/tri_score.py --chart              # also save chart PNG
    python analysis/tri_score.py --chart --out docs/images/field_timeseries.png

CSV format accepted (column names auto-detected):
    timestamp,node_id,konum,mesafe_cm,doluluk_pct,durum   (field logs)
    zaman_ms,node_id,doluluk,alarm                        (hub SD logs)
Rows with a non-numeric fill (e.g. durum=KAYIP sensor dropouts) are dropped.
"""

import os
import glob
import argparse
import pandas as pd
import numpy as np

DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
DEFAULT_OUT  = os.path.join(os.path.dirname(__file__), "..", "docs", "images", "field_timeseries.png")

ALARM_THRESHOLD = 80.0   # % — "danger" level
HIGH_THRESHOLD  = 60.0   # % — "elevated" level
RISE_WINDOW_S   = 60.0   # s — window over which peak rise rate is measured
GAP_S           = 5.0    # s — time gap above this splits a contiguous segment

# Equal weights across the five parameters (sum = 1.0)
WEIGHTS = {"mean": 0.20, "max": 0.20, "e80": 0.20, "freq": 0.20, "rise": 0.20}

# Absolute anchors for the hybrid method (tunable, dataset-independent).
ANCHOR_E80_PCT       = 10.0   # spending 10% of time above 80% → full marks
ANCHOR_FREQ_PER_HR   = 5.0    # 5 upward 80%-crossings per hour → full marks
ANCHOR_RISE_PCT_MIN  = 30.0   # filling ≥30 percentage-points per minute → full marks

# ── Data loading ──────────────────────────────────────────────────────────────

def load_all_csv(data_dir):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")
    frames = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip()
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    # Normalise the fill column name to internal standard "doluluk"
    if "doluluk_pct" in df.columns and "doluluk" not in df.columns:
        df = df.rename(columns={"doluluk_pct": "doluluk"})

    # Extract numeric ID from strings like 'NODE_1'
    if "node_id" in df.columns:
        df["node_id"] = df["node_id"].astype(str).str.extract(r"(\d+)")

    # Coerce types; non-numeric fills (durum=KAYIP dropouts) become NaN and drop
    df["node_id"] = pd.to_numeric(df["node_id"], errors="coerce")
    df["doluluk"] = pd.to_numeric(df["doluluk"], errors="coerce")
    df = df.dropna(subset=["node_id", "doluluk"])
    df["node_id"] = df["node_id"].astype(int)
    df["doluluk"] = df["doluluk"].astype(float).clip(0, 100)

    # Time axis: prefer the real wall-clock timestamp; fall back to 1 Hz index.
    # Cast explicitly to ms resolution — pandas may parse to s/us/ns depending
    # on version, so astype("int64") units are not portable without this.
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.loc[ts.notna()].copy()
        ts = ts.loc[ts.notna()]
        df["zaman_ms"] = ts.astype("datetime64[ms]").astype("int64").astype(float).values
    elif "zaman_ms" in df.columns:
        df["zaman_ms"] = pd.to_numeric(df["zaman_ms"], errors="coerce")
        df = df.dropna(subset=["zaman_ms"])
    else:
        df["zaman_ms"] = df.groupby("node_id").cumcount() * 1000.0
    return df

# ── Metrics ───────────────────────────────────────────────────────────────────

def _peak_rise_rate(fill, t_s, window_s=RISE_WINDOW_S):
    """Peak fill-rise rate in percentage-points per minute.

    For every sample, measures how much the fill climbs over the next
    `window_s` seconds and returns the maximum such rate. This is robust for
    field data (always defined, no dependence on the channel ever emptying)
    and directionally correct for risk: a faster climb yields a larger value.

    Time gaps > GAP_S split the series so a rise is never measured across a
    sensor dropout or a separate session. Returns 0.0 for flat/short series.
    """
    if len(fill) < 2:
        return 0.0
    breaks = np.where(np.diff(t_s) > GAP_S)[0] + 1
    segments = np.split(np.arange(len(fill)), breaks)

    best = 0.0
    for seg in segments:
        if len(seg) < 2:
            continue
        f = fill[seg]
        ts = t_s[seg]
        # For each i, the first index whose time reaches ts[i] + window_s.
        # Skip samples where a full window is unavailable (segment end): a
        # truncated window divides by a tiny dt and blows the rate up.
        j_idx = np.searchsorted(ts, ts + window_s, side="left")
        for i in range(len(f)):
            j = j_idx[i]
            if j >= len(f):
                continue
            dt_min = (ts[j] - ts[i]) / 60.0
            if dt_min > 0:
                rate = (f[j] - f[i]) / dt_min
                if rate > best:
                    best = rate
    return best


def compute_metrics(df):
    results = {}
    for node_id, group in df.groupby("node_id"):
        group = group.sort_values("zaman_ms")
        fill = group["doluluk"].values
        t_s  = group["zaman_ms"].values / 1000.0   # seconds

        n = len(fill)
        # Active duration in hours from the ~1 Hz sample count — gap-independent
        # (timestamp span would be inflated by session/dropout gaps).
        hours = n / 3600.0

        above_80 = int(np.sum(fill >= ALARM_THRESHOLD))
        above_60 = int(np.sum(fill >= HIGH_THRESHOLD))
        # Upward crossings INTO the >=80% region
        crossings_80 = int(np.sum(np.diff((fill >= ALARM_THRESHOLD).astype(int)) > 0))

        results[node_id] = {
            "mean_fill":     float(np.mean(fill)),
            "max_fill":      float(np.max(fill)),
            "std_fill":      float(np.std(fill)),
            "pct_above_80":  100.0 * above_80 / n,
            "pct_above_60":  100.0 * above_60 / n,
            "time_above_80": above_80,
            "crossings_80":  crossings_80,
            "freq_per_hour": (crossings_80 / hours) if hours > 0 else 0.0,
            "rise_rate":     _peak_rise_rate(fill, t_s),
            "n_samples":     n,
        }
    return results

# ── Scoring helpers ─────────────────────────────────────────────────────────────

def minmax(values: dict) -> dict:
    """Min-max normalize a {node: value} mapping to 0–100. NaN treated as 0."""
    arr = {k: (0.0 if (v is None or np.isnan(v)) else float(v)) for k, v in values.items()}
    vmin = min(arr.values())
    vmax = max(arr.values())
    if vmax == vmin:
        return {k: 0.0 for k in arr}
    return {k: (v - vmin) / (vmax - vmin) * 100.0 for k, v in arr.items()}


def abs_e80(pct):       return float(np.clip(pct / ANCHOR_E80_PCT * 100.0, 0, 100))
def abs_freq(per_hr):   return float(np.clip(per_hr / ANCHOR_FREQ_PER_HR * 100.0, 0, 100))
def abs_rise(pct_min):  return float(np.clip(pct_min / ANCHOR_RISE_PCT_MIN * 100.0, 0, 100))

# ── TRİ computation ─────────────────────────────────────────────────────────────

def compute_tri(metrics, method="hybrid"):
    keys = sorted(metrics.keys())

    raw = {
        "mean": {k: metrics[k]["mean_fill"]     for k in keys},
        "max":  {k: metrics[k]["max_fill"]      for k in keys},
        "e80":  {k: metrics[k]["pct_above_80"]  for k in keys},
        "freq": {k: metrics[k]["freq_per_hour"] for k in keys},
        "rise": {k: metrics[k]["rise_rate"]     for k in keys},
    }

    # Relative (min-max) sub-scores. Every parameter is already oriented so
    # that "higher = more risk" (rise is a rate: a faster climb is larger).
    rel = {p: minmax(raw[p]) for p in WEIGHTS}

    # Absolute, dataset-independent sub-scores (fixed 0–100 anchors).
    absolute = {
        "mean": {k: raw["mean"][k] for k in keys},   # already 0–100
        "max":  {k: raw["max"][k]  for k in keys},   # already 0–100
        "e80":  {k: abs_e80(raw["e80"][k])  for k in keys},
        "freq": {k: abs_freq(raw["freq"][k]) for k in keys},
        "rise": {k: abs_rise(raw["rise"][k]) for k in keys},
    }

    if method == "minmax":
        sub = rel
    elif method == "hybrid":
        # Blend absolute and relative 50/50 per parameter.
        sub = {p: {k: 0.5 * absolute[p][k] + 0.5 * rel[p][k] for k in keys}
               for p in WEIGHTS}
    else:
        raise ValueError(f"Unknown method: {method}")

    tri = {k: sum(WEIGHTS[p] * sub[p][k] for p in WEIGHTS) for k in keys}
    return tri


def risk_level(score):
    if score >= 76: return "🔴 CRITICAL"
    if score >= 51: return "🟠 HIGH"
    if score >= 26: return "🟡 MEDIUM"
    return "🟢 LOW"

# ── Chart ─────────────────────────────────────────────────────────────────────

def generate_chart(df, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        print("[Chart] matplotlib not installed. Run: pip install matplotlib")
        return

    NODE_LABELS = {
        1: "Node 1 — Barajyolu",
        2: "Node 2 — Turgut Özal",
        3: "Node 3 — Sinanpaşa (Ref.)",
    }
    NODE_COLORS = {1: "#FF4444", 2: "#FF8800", 3: "#00CC66"}

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor("#0a0c0f")
    ax.set_facecolor("#0f1217")

    for node_id, group in df.sort_values("zaman_ms").groupby("node_id"):
        # Normalize time to seconds from session start per node
        t = (group["zaman_ms"].values - group["zaman_ms"].values[0]) / 1000.0
        fill = group["doluluk"].values
        label = NODE_LABELS.get(node_id, f"Node {node_id}")
        color = NODE_COLORS.get(node_id, "#aaaaaa")
        ax.plot(t, fill, color=color, linewidth=1.2, alpha=0.85, label=label)

    # Threshold reference lines
    ax.axhline(80, color="#ff2244", linewidth=0.8, linestyle="--", alpha=0.7, label="80% Alarm threshold")
    ax.axhline(60, color="#ff8800", linewidth=0.8, linestyle=":",  alpha=0.5, label="60% High threshold")

    ax.set_ylim(0, 105)
    ax.set_xlabel("Time from session start (seconds)", color="#c8d4e0", fontsize=10)
    ax.set_ylabel("Fill level (%)", color="#c8d4e0", fontsize=10)
    ax.set_title("TAŞKIN — Field Test Fill Rate by Node", color="#00d4ff", fontsize=13, pad=12)

    ax.tick_params(colors="#4a5a6a")
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2530")

    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
    ax.legend(facecolor="#0f1217", edgecolor="#1e2530", labelcolor="#c8d4e0", fontsize=9)
    ax.grid(axis="y", color="#1e2530", linewidth=0.5)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Chart] Saved → {out_path}")

# ── Reporting ───────────────────────────────────────────────────────────────────

def print_descriptive(metrics):
    print("Descriptive Statistics:")
    header = (f"{'Node':<6} {'Mean%':>7} {'Max%':>7} {'StdDev':>8} "
              f"{'>60%':>7} {'>80%':>7} {'80x/h':>7} {'Rise%/m':>8} {'N':>8}")
    print(header)
    print("-" * len(header))
    for nid in sorted(metrics):
        m = metrics[nid]
        print(f"{nid:<6} {m['mean_fill']:>7.1f} {m['max_fill']:>7.1f} "
              f"{m['std_fill']:>8.2f} {m['pct_above_60']:>6.1f}% {m['pct_above_80']:>6.1f}% "
              f"{m['freq_per_hour']:>7.2f} {m['rise_rate']:>8.1f} {m['n_samples']:>8}")


def print_tri(metrics, method, title):
    tri = compute_tri(metrics, method=method)
    print(f"\n{title}")
    print(f"{'Node':<6} {'TRİ Score':>10}   {'Risk Level'}")
    print("-" * 40)
    for nid in sorted(tri, key=lambda k: tri[k], reverse=True):
        print(f"{nid:<6} {tri[nid]:>10.1f}   {risk_level(tri[nid])}")
    return tri

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TAŞKIN TRİ Score Calculator")
    parser.add_argument("--method", choices=["minmax", "hybrid", "both"],
                        default="both", help="Scoring method (default: both)")
    parser.add_argument("--chart", action="store_true", help="Generate fill rate chart")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Chart output path (PNG)")
    args = parser.parse_args()

    print("TAŞKIN Risk İndeksi (TRİ) Calculator")
    print("=" * 60)

    df = load_all_csv(DATA_DIR)
    print(f"Loaded {len(df):,} records from {df['node_id'].nunique()} node(s).\n")

    metrics = compute_metrics(df)
    print_descriptive(metrics)

    if args.method in ("minmax", "both"):
        print_tri(metrics, "minmax",
                  "TRİ Scores — min-max (relative ranking across nodes):")
    if args.method in ("hybrid", "both"):
        print_tri(metrics, "hybrid",
                  "TRİ Scores — hybrid (absolute anchors + relative, 50/50):")

    if args.chart:
        generate_chart(df, args.out)

if __name__ == "__main__":
    main()
