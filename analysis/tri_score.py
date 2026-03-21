#!/usr/bin/env python3
"""
tri_score.py — TAŞKIN Risk İndeksi (TRİ) Calculator

Reads all CSV files from data/samples/, computes the composite TRİ score
for each node using min-max normalization and equal weights, and prints
a ranked risk table.

Usage:
    python analysis/tri_score.py

Expected CSV format (per file):
    zaman_ms,node_id,doluluk,alarm
    12500,1,63.5,0
    ...

Output: TRİ scores per node (0–100), risk level classification.
"""

import os
import glob
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
ALARM_THRESHOLD = 80.0
HIGH_THRESHOLD = 60.0
RISE_FROM = 20.0
RISE_TO = 80.0

def load_all_csv(data_dir):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
    frames = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip()
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["node_id", "doluluk"])
    df["node_id"] = df["node_id"].astype(int)
    df["doluluk"] = df["doluluk"].astype(float).clip(0, 100)
    return df

def compute_metrics(df):
    results = {}
    for node_id, group in df.groupby("node_id"):
        fill = group["doluluk"].values
        n = len(fill)

        mean_fill = np.mean(fill)
        max_fill = np.max(fill)
        std_fill = np.std(fill)

        time_above_80 = np.sum(fill >= ALARM_THRESHOLD)   # seconds (1 Hz)
        time_above_60 = np.sum(fill >= HIGH_THRESHOLD)
        crossings_80 = int(np.sum(np.diff((fill >= ALARM_THRESHOLD).astype(int)) > 0))

        # Rise speed: first passage from RISE_FROM to RISE_TO
        above_from = np.where(fill >= RISE_FROM)[0]
        rise_duration = np.nan
        if len(above_from) > 0:
            start_idx = above_from[0]
            above_to = np.where(fill[start_idx:] >= RISE_TO)[0]
            if len(above_to) > 0:
                rise_duration = above_to[0]  # seconds

        results[node_id] = {
            "mean_fill": mean_fill,
            "max_fill": max_fill,
            "std_fill": std_fill,
            "time_above_80": time_above_80,
            "time_above_60": time_above_60,
            "crossings_80": crossings_80,
            "rise_duration": rise_duration,
            "n_samples": n,
        }
    return results

def normalize(values):
    """Min-max normalize a dict of {key: float} to 0–100. Returns same dict normalized."""
    vals = np.array([v if not np.isnan(v) else 0 for v in values.values()])
    vmin, vmax = vals.min(), vals.max()
    if vmax == vmin:
        return {k: 0.0 for k in values}
    norm = {k: ((v if not np.isnan(v) else 0) - vmin) / (vmax - vmin) * 100
            for k, v in values.items()}
    return norm

def compute_tri(metrics):
    keys = sorted(metrics.keys())

    mean_raw   = {k: metrics[k]["mean_fill"]     for k in keys}
    max_raw    = {k: metrics[k]["max_fill"]      for k in keys}
    e80_raw    = {k: metrics[k]["time_above_80"] for k in keys}
    freq_raw   = {k: metrics[k]["crossings_80"]  for k in keys}
    rise_raw   = {k: metrics[k]["rise_duration"] for k in keys}

    mean_n  = normalize(mean_raw)
    max_n   = normalize(max_raw)
    e80_n   = normalize(e80_raw)
    freq_n  = normalize(freq_raw)
    rise_n  = normalize(rise_raw)

    tri = {}
    for k in keys:
        tri[k] = 0.20 * mean_n[k] + 0.20 * max_n[k] + 0.20 * e80_n[k] + \
                 0.20 * freq_n[k] + 0.20 * rise_n[k]
    return tri

def risk_level(score):
    if score >= 76: return "🔴 CRITICAL"
    if score >= 51: return "🟠 HIGH"
    if score >= 26: return "🟡 MEDIUM"
    return "🟢 LOW"

def main():
    print("TAŞKIN Risk İndeksi (TRİ) Calculator")
    print("=" * 50)

    df = load_all_csv(DATA_DIR)
    print(f"Loaded {len(df):,} records from {df['node_id'].nunique()} nodes.\n")

    metrics = compute_metrics(df)

    print("Descriptive Statistics:")
    print(f"{'Node':<8} {'Mean%':>8} {'Max%':>8} {'StdDev':>8} {'>80s (s)':>10} {'>80 cross':>10} {'Rise (s)':>10} {'N':>8}")
    print("-" * 75)
    for node_id in sorted(metrics):
        m = metrics[node_id]
        rise = f"{m['rise_duration']:.0f}" if not np.isnan(m['rise_duration']) else "N/A"
        print(f"{node_id:<8} {m['mean_fill']:>8.1f} {m['max_fill']:>8.1f} {m['std_fill']:>8.2f} "
              f"{m['time_above_80']:>10} {m['crossings_80']:>10} {rise:>10} {m['n_samples']:>8}")

    tri = compute_tri(metrics)

    print("\nTRİ Scores:")
    print(f"{'Node':<8} {'TRİ Score':>12} {'Risk Level'}")
    print("-" * 40)
    for node_id in sorted(tri, key=lambda k: tri[k], reverse=True):
        score = tri[node_id]
        print(f"{node_id:<8} {score:>12.1f}   {risk_level(score)}")

if __name__ == "__main__":
    main()
