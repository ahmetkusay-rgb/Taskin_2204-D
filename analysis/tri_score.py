#!/usr/bin/env python3
"""
tri_score.py — TAŞKIN Risk İndeksi (TRİ) Calculator + Chart Generator

Reads all CSV files from data/samples/, computes the composite TRİ score
for each node using min-max normalization and equal weights, prints a
ranked risk table, and saves a time-series fill rate chart.

Usage:
    python analysis/tri_score.py               # print table only
    python analysis/tri_score.py --chart       # also save chart PNG
    python analysis/tri_score.py --chart --out images/field_timeseries.png

CSV format expected:
    zaman_ms,node_id,doluluk,alarm
"""

import os
import glob
import argparse
import pandas as pd
import numpy as np

DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
DEFAULT_OUT  = os.path.join(os.path.dirname(__file__), "..", "images", "field_timeseries.png")
ALARM_THRESHOLD = 80.0
HIGH_THRESHOLD  = 60.0

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
    # Normalise column names to internal standard
    if "doluluk_pct" in df.columns and "doluluk" not in df.columns:
        df = df.rename(columns={"doluluk_pct": "doluluk"})
    if "node_id" in df.columns:
        # Extract numeric ID from strings like 'NODE_1'
        df["node_id"] = df["node_id"].astype(str).str.extract(r'(\d+)').astype(int)
    df = df.dropna(subset=["node_id", "doluluk"])
    df["doluluk"] = df["doluluk"].astype(float).clip(0, 100)
    # Use row index as proxy time if no zaman_ms column
    if "zaman_ms" not in df.columns:
        df["zaman_ms"] = df.groupby("node_id").cumcount() * 1000
    else:
        df["zaman_ms"] = pd.to_numeric(df["zaman_ms"], errors="coerce")
    return df

# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(df):
    results = {}
    for node_id, group in df.groupby("node_id"):
        fill = group["doluluk"].values

        mean_fill    = np.mean(fill)
        max_fill     = np.max(fill)
        std_fill     = np.std(fill)
        time_above_80 = int(np.sum(fill >= ALARM_THRESHOLD))
        time_above_60 = int(np.sum(fill >= HIGH_THRESHOLD))
        crossings_80  = int(np.sum(np.diff((fill >= ALARM_THRESHOLD).astype(int)) > 0))

        above_from = np.where(fill >= 20.0)[0]
        rise_duration = np.nan
        if len(above_from) > 0:
            start_idx = above_from[0]
            above_to = np.where(fill[start_idx:] >= 80.0)[0]
            if len(above_to) > 0:
                rise_duration = float(above_to[0])

        results[node_id] = {
            "mean_fill":     mean_fill,
            "max_fill":      max_fill,
            "std_fill":      std_fill,
            "time_above_80": time_above_80,
            "time_above_60": time_above_60,
            "crossings_80":  crossings_80,
            "rise_duration": rise_duration,
            "n_samples":     len(fill),
        }
    return results

# ── TRİ computation ───────────────────────────────────────────────────────────

def minmax_norm(values: dict) -> dict:
    raw = np.array([v if not np.isnan(v) else 0.0 for v in values.values()])
    vmin, vmax = raw.min(), raw.max()
    if vmax == vmin:
        return {k: 0.0 for k in values}
    return {
        k: ((v if not np.isnan(v) else 0.0) - vmin) / (vmax - vmin) * 100
        for k, v in values.items()
    }

def compute_tri(metrics):
    keys = sorted(metrics.keys())
    params = {
        "mean":   {k: metrics[k]["mean_fill"]     for k in keys},
        "max":    {k: metrics[k]["max_fill"]       for k in keys},
        "e80":    {k: metrics[k]["time_above_80"]  for k in keys},
        "freq":   {k: metrics[k]["crossings_80"]   for k in keys},
        "rise":   {k: metrics[k]["rise_duration"]  for k in keys},
    }
    normed = {p: minmax_norm(v) for p, v in params.items()}
    tri = {k: 0.20 * sum(normed[p][k] for p in normed) for k in keys}
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

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TAŞKIN TRİ Score Calculator")
    parser.add_argument("--chart", action="store_true", help="Generate fill rate chart")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Chart output path (PNG)")
    args = parser.parse_args()

    print("TAŞKIN Risk İndeksi (TRİ) Calculator")
    print("=" * 60)

    df = load_all_csv(DATA_DIR)
    print(f"Loaded {len(df):,} records from {df['node_id'].nunique()} node(s).\n")

    metrics = compute_metrics(df)

    # ── Descriptive table ──
    print("Descriptive Statistics:")
    header = f"{'Node':<6} {'Mean%':>7} {'Max%':>7} {'StdDev':>8} {'>60s':>6} {'>80s':>6} {'>80×':>6} {'Rise(s)':>8} {'N':>7}"
    print(header)
    print("-" * len(header))
    for nid in sorted(metrics):
        m = metrics[nid]
        rise = f"{m['rise_duration']:.0f}" if not np.isnan(m['rise_duration']) else "N/A"
        print(f"{nid:<6} {m['mean_fill']:>7.1f} {m['max_fill']:>7.1f} "
              f"{m['std_fill']:>8.2f} {m['time_above_60']:>6} {m['time_above_80']:>6} "
              f"{m['crossings_80']:>6} {rise:>8} {m['n_samples']:>7}")

    # ── TRİ table ──
    tri = compute_tri(metrics)
    print("\nTRİ Scores (equal-weight composite, min-max normalized):")
    print(f"{'Node':<6} {'TRİ Score':>10}   {'Risk Level'}")
    print("-" * 40)
    for nid in sorted(tri, key=lambda k: tri[k], reverse=True):
        print(f"{nid:<6} {tri[nid]:>10.1f}   {risk_level(tri[nid])}")

    if args.chart:
        generate_chart(df, args.out)

if __name__ == "__main__":
    main()
