#!/usr/bin/env python3
"""
tri_score.py — TAŞKIN Risk İndeksi (TRİ) Calculator + Chart Generator

Computes a composite TAŞKIN Risk Index (TRİ, 0–100) per measurement node
from five field-derived risk parameters, using a transparent multi-criteria
decision-making (MCDM) scheme (Malczewski's weighted-combination framework).

Five risk parameters per node (all "higher = more risk"):
    O = mean fill (%)
    M = maximum fill (%)
    E = time spent above the 80% alarm threshold (seconds)
    F = number of upward 80%-threshold crossings
    A = peak fill-rise rate (fastest climb over a 60 s window, %/min)

Normalization — HYBRID (the design we converged on; see README §10):
    - O and M are already on a physical 0–100% scale and are meaningful in
      absolute terms, so they are used DIRECTLY (re-normalizing them across
      only three points would destroy that absolute meaning).
    - E, F and A have no natural upper bound, so they are MIN–MAX normalized
      across the measurement points:  X* = (X - Xmin) / (Xmax - Xmin) * 100
    - All five parameters carry equal weight (0.20). A sensitivity analysis
      (run with --method minmax to see the pure-min-max variant) shows the
      risk ranking is stable regardless of this choice.

    TRİ = 0.20 * (O + M + E* + F* + A*)

Usage:
    python analysis/tri_score.py                  # TRİ table (hybrid)
    python analysis/tri_score.py --method minmax  # initial pure min-max variant
    python analysis/tri_score.py --chart          # also save time-series PNG

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

DATA_DIR    = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "images", "field_timeseries.png")

ALARM_THRESHOLD = 80.0   # % — alarm/danger level
HIGH_THRESHOLD  = 60.0   # % — elevated level
RISE_WINDOW_S   = 60.0   # s — window over which the peak rise rate is measured
GAP_S           = 5.0    # s — a time gap above this splits a contiguous segment
WEIGHT          = 0.20   # equal weight per parameter (5 × 0.20 = 1.0)

NODE_LABELS = {
    1: "Node 1 — Barajyolu",
    2: "Node 2 — Turgut Özal",
    3: "Node 3 — Sinanpaşa (Ref.)",
}

# ── Data loading ──────────────────────────────────────────────────────────────

def load_all_csv(data_dir):
    files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in: {data_dir}")
    frames = []
    for filename in sorted(files):
        df = pd.read_csv(filename)
        df.columns = df.columns.str.strip()
        if "doluluk" not in df and "doluluk_pct" in df:
            df = df.rename(columns={"doluluk_pct": "doluluk"})
        if not {"node_id", "doluluk"}.issubset(df.columns):
            raise ValueError(f"Missing node_id/doluluk columns: {filename}")
        df["node_id"] = pd.to_numeric(df["node_id"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
        df["doluluk"] = pd.to_numeric(df["doluluk"], errors="coerce")
        if "timestamp" in df:
            ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
            df["zaman_ms"] = ts.map(lambda t: t.timestamp() * 1000 if pd.notna(t) else np.nan)
        elif "zaman_ms" in df:
            df["zaman_ms"] = pd.to_numeric(df["zaman_ms"], errors="coerce")
        else:
            raise ValueError(f"Missing timestamp/zaman_ms: {filename}")
        # Separate files and clock resets are separate acquisition sessions.
        resets = df.groupby("node_id")["zaman_ms"].diff().lt(0).cumsum()
        df["session"] = os.path.basename(filename) + ":" + resets.astype(str)
        if "durum" in df:
            df = df.loc[df["durum"].astype(str).str.upper() != "KAYIP"]
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["node_id", "doluluk", "zaman_ms"])
        df = df.loc[df["doluluk"].between(0, 100) & df["node_id"].between(1, 10)]
        df["node_id"] = df["node_id"].astype(int)
        df = df.drop_duplicates(["session", "node_id", "zaman_ms"], keep="last")
        frames.append(df)
    result = pd.concat(frames, ignore_index=True)
    if result.empty:
        raise ValueError("No valid measurements remain after validation")
    return result

# ── Metrics ───────────────────────────────────────────────────────────────────

def _peak_rise_rate(fill, t_s, window_s=RISE_WINDOW_S):
    """Peak fill-rise rate (percentage-points per minute).

    For each sample, measures how far the fill climbs over the next `window_s`
    seconds and returns the maximum. Time gaps > GAP_S split the series so a
    rise is never measured across a sensor dropout or across two sessions.
    Samples without a full window ahead (segment end) are skipped — a truncated
    window divides by a tiny dt and would blow the rate up.
    """
    if len(fill) < 2:
        return 0.0
    breaks = np.where(np.diff(t_s) > GAP_S)[0] + 1
    best = 0.0
    for seg in np.split(np.arange(len(fill)), breaks):
        if len(seg) < 2:
            continue
        f, ts = fill[seg], t_s[seg]
        j_idx = np.searchsorted(ts, ts + window_s, side="left")
        for i in range(len(f)):
            j = j_idx[i]
            if j >= len(f):
                continue
            dt_min = (ts[j] - ts[i]) / 60.0
            if dt_min > 0:
                best = max(best, (f[j] - f[i]) / dt_min)
    return best


def compute_metrics(df):
    results = {}
    for node_id, group in df.groupby("node_id"):
        fill = group["doluluk"].to_numpy()
        n = len(fill)
        exposure = 0.0
        crossings = 0
        peak = 0.0
        sessions = group.groupby("session") if "session" in group else [("single", group)]
        for _, session in sessions:
            session = session.sort_values("zaman_ms")
            values = session["doluluk"].to_numpy()
            times = session["zaman_ms"].to_numpy() / 1000.0
            dt = np.diff(times)
            contiguous = (dt > 0) & (dt <= GAP_S)
            high = values >= ALARM_THRESHOLD
            # Left-sample hold only over observed contiguous intervals.
            exposure += float(np.sum(dt[contiguous & high[:-1]]))
            crossings += int(np.sum(contiguous & ~high[:-1] & high[1:]))
            peak = max(peak, _peak_rise_rate(values, times))
        results[node_id] = {
            "O": float(np.mean(fill)),                                            # mean fill
            "M": float(np.max(fill)),                                             # max fill
            "E": exposure,                            # seconds >= 80%
            "F": crossings, # 80% up-crossings
            "A": peak,                                      # peak rise %/min
            "std": float(np.std(fill)),
            "pct_above_60": 100.0 * np.sum(fill >= HIGH_THRESHOLD) / n,
            "n": n,
        }
    return results

# ── TRİ computation ─────────────────────────────────────────────────────────────

def minmax(values):
    """Min-max normalize {node: value} to 0–100."""
    lo, hi = min(values.values()), max(values.values())
    if hi == lo:
        return {k: 0.0 for k in values}
    return {k: (v - lo) / (hi - lo) * 100.0 for k, v in values.items()}


def compute_tri(metrics, method="hybrid"):
    if not metrics:
        raise ValueError("No node metrics to score")
    keys = sorted(metrics)
    raw = {p: {k: metrics[k][p] for k in keys} for p in ("O", "M", "E", "F", "A")}

    if method == "hybrid":
        # O, M used directly (already 0–100%); E, F, A min-max normalized.
        sub = {"O": raw["O"], "M": raw["M"],
               "E": minmax(raw["E"]), "F": minmax(raw["F"]), "A": minmax(raw["A"])}
    elif method == "minmax":
        # Initial approach: every parameter min-max normalized (sensitivity check).
        sub = {p: minmax(raw[p]) for p in raw}
    else:
        raise ValueError(f"Unknown method: {method}")

    return {k: WEIGHT * sum(sub[p][k] for p in sub) for k in keys}


def risk_level(score):
    if score > 75: return "🔴 CRITICAL"
    if score > 50: return "🟠 HIGH"
    if score > 25: return "🟡 MEDIUM"
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

    NODE_COLORS = {1: "#FF4444", 2: "#FF8800", 3: "#00CC66"}
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor("#0a0c0f")
    ax.set_facecolor("#0f1217")

    for node_id, group in df.groupby("node_id"):
        sessions = group.groupby("session") if "session" in group else [("single", group)]
        for session_name, session in sessions:
            session = session.sort_values("zaman_ms")
            t = (session["zaman_ms"].to_numpy() - session["zaman_ms"].iloc[0]) / 1000.0
            values = session["doluluk"].to_numpy(dtype=float).copy()
            # NaN separators prevent the plot from implying data in missing intervals.
            breaks = np.where(np.diff(t) > GAP_S)[0] + 1
            plot_t = np.insert(t, breaks, np.nan)
            plot_values = np.insert(values, breaks, np.nan)
            ax.plot(plot_t, plot_values, color=NODE_COLORS.get(node_id, "#aaaaaa"),
                    linewidth=1.2, alpha=0.85,
                    label=f"{NODE_LABELS.get(node_id, f'Node {node_id}')} / {session_name}")

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

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()
    print(f"[Chart] Saved → {out_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="TAŞKIN TRİ Score Calculator")
    parser.add_argument("--method", choices=["hybrid", "minmax"], default="hybrid",
                        help="Normalization scheme (default: hybrid)")
    parser.add_argument("--chart", action="store_true", help="Generate fill-rate chart")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Chart output path (PNG)")
    parser.add_argument("--data-dir", default=DATA_DIR, help="Directory containing session CSV files")
    args = parser.parse_args()

    print("TAŞKIN Risk İndeksi (TRİ) Calculator")
    print("=" * 64)

    df = load_all_csv(args.data_dir)
    print(f"Loaded {len(df):,} records from {df['node_id'].nunique()} node(s).\n")

    metrics = compute_metrics(df)

    print("Field parameters per node:")
    hdr = f"{'Node':<26} {'O mean%':>8} {'M max%':>7} {'E >80s':>7} {'F x80':>6} {'A %/min':>8}"
    print(hdr); print("-" * len(hdr))
    for nid in sorted(metrics):
        m = metrics[nid]
        print(f"{NODE_LABELS.get(nid, 'Node '+str(nid)):<26} "
              f"{m['O']:>8.1f} {m['M']:>7.1f} {m['E']:>7.1f} {m['F']:>6d} {m['A']:>8.1f}")

    tri = compute_tri(metrics, method=args.method)
    print(f"\nTRİ Scores — {args.method} normalization, equal weights:")
    print(f"{'Node':<26} {'TRİ':>7}   Risk")
    print("-" * 48)
    for nid in sorted(tri, key=lambda k: tri[k], reverse=True):
        print(f"{NODE_LABELS.get(nid, 'Node '+str(nid)):<26} {tri[nid]:>7.1f}   {risk_level(tri[nid])}")

    if args.chart:
        generate_chart(df, args.out)

if __name__ == "__main__":
    main()
