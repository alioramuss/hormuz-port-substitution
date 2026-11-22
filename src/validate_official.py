"""
Check PortWatch against official port statistics.

For every official figure in data/official/official_port_stats.csv (a port or
operator, a period, and the official year-on-year change in TEU), this script
computes the year-on-year change PortWatch shows for the same ports and dates,
both in container ship calls and in container tonnes, and plots the two
against each other.

Run from the project root, after src/analysis.py:
    python src/validate_official.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "portwatch_gulf_ports_2024_2026.csv"
OFFICIAL = ROOT / "data" / "official" / "official_port_stats.csv"
OUT_T = ROOT / "outputs" / "tables"
OUT_F = ROOT / "outputs" / "figures"

# Ship counts at Khor Fakkan from Xeneta's eeSea liner database, as reported by
# The Loadstar (2026). Only March to June were reported.
KHOR_FAKKAN_EESEA = {"2026-03": 14, "2026-04": 21, "2026-05": 23, "2026-06": 26}


def portwatch_yoy(d, ids, start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    s0, e0 = s - pd.DateOffset(years=1), e - pd.DateOffset(years=1)
    cur = d[d["portid"].isin(ids) & (d["date"] >= s) & (d["date"] <= e)]
    base = d[d["portid"].isin(ids) & (d["date"] >= s0) & (d["date"] <= e0)]
    out = {}
    for col, name in [("portcalls_container", "calls"), ("container_kt", "tonnes")]:
        c, b = cur[col].sum(), base[col].sum()
        out[f"portwatch_{name}_2026"] = c
        out[f"portwatch_{name}_2025"] = b
        out[f"portwatch_{name}_yoy_pct"] = 100 * (c - b) / b if b else np.nan
    return out


def verdict(official, pw):
    gap = pw - official
    if abs(gap) <= 10:
        return "close"
    return "PortWatch too low" if gap < 0 else "PortWatch too high"


def main():
    d = pd.read_csv(DATA, parse_dates=["date"])
    d["container_kt"] = (d["import_container"] + d["export_container"]) / 1000.0
    off = pd.read_csv(OFFICIAL)

    rows = []
    for _, r in off.iterrows():
        res = portwatch_yoy(d, r["portwatch_ports"].split(";"), r["start"], r["end"])
        rows.append({
            "port_or_operator": r["port_or_operator"], "period": r["period_label"],
            "official_yoy_pct": r["official_yoy_pct"], **res,
            "calls_verdict": verdict(r["official_yoy_pct"], res["portwatch_calls_yoy_pct"]),
            "tonnes_verdict": verdict(r["official_yoy_pct"], res["portwatch_tonnes_yoy_pct"]),
            "source": r["source"], "note": r["note"] if isinstance(r["note"], str) else "",
        })
    v = pd.DataFrame(rows)
    v.to_csv(OUT_T / "validation_official_vs_portwatch.csv", index=False)

    # Khor Fakkan: PortWatch container calls per month vs eeSea ship counts
    kf = d[d["portid"] == "port561"].copy()
    kf["month"] = kf["date"].dt.strftime("%Y-%m")
    kfm = kf[kf["date"] >= "2026-01-01"].groupby("month")["portcalls_container"].sum().rename("portwatch_container_calls")
    kfm = kfm.to_frame()
    kfm["eesea_ship_calls"] = kfm.index.map(KHOR_FAKKAN_EESEA)
    kfm.reset_index().to_csv(OUT_T / "khor_fakkan_calls_check.csv", index=False)

    fig_validation(v)
    pd.set_option("display.width", 180)
    print(v[["port_or_operator", "period", "official_yoy_pct", "portwatch_calls_yoy_pct",
             "portwatch_tonnes_yoy_pct", "calls_verdict", "tonnes_verdict"]].round(1).to_string(index=False))
    print()
    print(kfm.to_string())


def fig_validation(v):
    INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
    lim = (-100, 120)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    for ax, col, title in [(axes[0], "portwatch_calls_yoy_pct", "PortWatch container ship calls"),
                           (axes[1], "portwatch_tonnes_yoy_pct", "PortWatch container tonnes")]:
        ax.fill_between(lim, [lim[0] - 10, lim[1] - 10], [lim[0] + 10, lim[1] + 10], color="#f0efec", lw=0, zorder=0)
        ax.plot(lim, lim, color="#c3c2b7", lw=1, zorder=1)
        x = v["official_yoy_pct"].values
        y = np.clip(v[col].values, lim[0], lim[1])
        clipped = v[col].values > lim[1]
        ax.scatter(x, y, s=46, color="#2a78d6", edgecolor="#fcfcfb", linewidth=1.5, zorder=3)
        short = {"Jebel Ali (DP World)": "Jebel Ali", "AD Ports UAE container ports": "AD Ports UAE",
                 "Saudi ports (Mawani)": "Saudi ports", "Nhava Sheva (JNPA)": "Nhava Sheva",
                 "Mundra (Adani Ports)": "Mundra", "Salalah": "Salalah", "Sohar": "Sohar", "Colombo": "Colombo"}
        per = lambda t: t.replace(" 2026", "").replace("Jan-Jun", "H1")
        labs = [short.get(a, a) + " " + per(b) for a, b in zip(v["port_or_operator"], v["period"])]
        placed = []
        order = np.argsort(-y)
        for i in order:
            xi, yi, lab, cl = x[i], y[i], labs[i], clipped[i]
            if abs(yi - xi) <= 10:
                continue
            ly = yi
            while any(abs(ly - py) < 6 and abs(xi - px) < 45 for px, py in placed):
                ly -= 6
            placed.append((xi, ly))
            ax.annotate(lab + (" (off scale)" if cl else ""), (xi, yi), xytext=(xi + 4, ly - 1.5),
                        textcoords="data", fontsize=7, color=INK2,
                        arrowprops=dict(arrowstyle="-", color="#c3c2b7", lw=0.6) if abs(ly - yi) > 1 else None)
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        ax.set_xlabel("Official year-on-year change in TEU (%)", fontsize=8.5, color=INK2)
        ax.grid(True, color=GRID, lw=0.8)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        ax.tick_params(colors=MUTED, labelsize=8, length=0)
    axes[0].set_ylabel("PortWatch year-on-year change (%)", fontsize=8.5, color=INK2)
    fig.suptitle("Does PortWatch match official port statistics? Points on the diagonal match; "
                 "the shaded band is within 10 points", x=0.01, ha="left", fontsize=10.5, color=INK)
    fig.text(0.01, 0.01, "Sources: DP World, AD Ports, Mawani, JNPA, Adani Ports, Salalah Port Services, "
             "Oman Observer, SLPA; IMF PortWatch. Labels only on points more than 10 points off.",
             fontsize=7.2, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(OUT_F / "validation_official_vs_portwatch.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
