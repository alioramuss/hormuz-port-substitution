"""
Compare PortWatch levels (not just changes) with official port statistics.

For each row in data/official/official_absolute_stats.csv the matching
PortWatch number is summed over the same ports and dates:

  vessels_total        PortWatch port calls, all five cargo ship types
  vessels_container    PortWatch container ship calls
  tonnes_total         PortWatch imports plus exports, tonnes
  tonnes_noncontainer  same, minus container tonnes (Mawani reports cargo
                       tonnes without containers)
  tonnes_liquid_bulk   PortWatch tanker imports plus exports
  teu                  PortWatch container tonnes, giving the implied
                       tonnes per official TEU

Then the control adjusted container effects from analysis.py are converted
from tonnes to TEU using each group's own tonnes per TEU, to see whether
level differences between ports change the substitution shares.

Run from the project root, after analysis.py:
    py src/validate_absolute.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "portwatch_gulf_ports_2024_2026.csv"
OFFICIAL = ROOT / "data" / "official" / "official_absolute_stats.csv"
OUT_T = ROOT / "outputs" / "tables"
OUT_F = ROOT / "outputs" / "figures"

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, GREY = "#2a78d6", "#a8a69e"

PW_COLUMN = {
    "vessels_total": "portcalls",
    "vessels_container": "portcalls_container",
    "tonnes_total": "tonnes_total",
    "tonnes_noncontainer": "tonnes_noncontainer",
    "tonnes_liquid_bulk": "tonnes_tanker",
    "teu": "container_tonnes",
}


def load():
    d = pd.read_csv(DATA, parse_dates=["date"])
    d["tonnes_total"] = d["import"] + d["export"]
    d["container_tonnes"] = d["import_container"] + d["export_container"]
    d["tonnes_noncontainer"] = d["tonnes_total"] - d["container_tonnes"]
    d["tonnes_tanker"] = d["import_tanker"] + d["export_tanker"]
    return d


def period_label(start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    if s.month == 1 and e.month == 12 and s.year == e.year:
        return str(s.year)
    if s.month == 4 and e.month == 3 and e.year == s.year + 1:
        return f"FY{str(s.year)[2:]}-{str(e.year)[2:]}"
    if s.month == 7 and e.month == 6 and e.year == s.year + 1:
        return f"FY{str(s.year)[2:]}-{str(e.year)[2:]}"
    if s.month == 7 and e.year == s.year + 1:
        return f"Jul {s.year} to mid Jun {e.year}"
    if s.month == 1 and e.month == 6:
        return f"H1 {s.year}"
    if s.month == 1 and e.month == 10:
        return f"Jan to Oct {s.year}"
    if s.month == 4 and e.month == 6 and s.year == e.year:
        return f"Q2 {s.year}"
    if s.month == e.month and s.year == e.year:
        return s.strftime("%b %Y")
    return f"{s.strftime('%b %Y')} to {e.strftime('%b %Y')}"


def compare_levels(d, off):
    rows = []
    for _, r in off.iterrows():
        ids = r["portwatch_ports"].split(";")
        w = d[d["portid"].isin(ids) & (d["date"] >= r["start"]) & (d["date"] <= r["end"])]
        pw = w[PW_COLUMN[r["measure"]]].sum()
        rec = {
            "entity": r["entity"],
            "measure": r["measure"],
            "period": period_label(r["start"], r["end"]),
            "start": r["start"],
            "end": r["end"],
            "official": r["official_value"],
            "portwatch": round(pw, 1),
            "portwatch_to_official": np.nan,
            "tonnes_per_teu": np.nan,
            "teu_per_container_call": np.nan,
        }
        if r["measure"] == "teu":
            calls = w["portcalls_container"].sum()
            rec["tonnes_per_teu"] = pw / r["official_value"]
            rec["teu_per_container_call"] = r["official_value"] / calls if calls else np.nan
        else:
            rec["portwatch_to_official"] = pw / r["official_value"]
        rec["note"] = r["note"] if isinstance(r["note"], str) else ""
        rows.append(rec)
    return pd.DataFrame(rows)


def ratio_for(v, entity, period):
    m = v[(v["entity"] == entity) & (v["measure"] == "teu") & (v["period"] == period)]
    return float(m["tonnes_per_teu"].iloc[0])


def teu_equivalent_shares(v):
    """Re-express the control adjusted container tonne effects in TEU."""
    eff = pd.read_csv(OUT_T / "substitution_control_adjusted.csv")
    eff = eff[eff["metric"] == "container_kt"]
    ja = ratio_for(v, "Jebel Ali (DP World)", "Q2 2025")
    groups = {
        "uae_inside": (ja, "Jebel Ali, Q2 2025"),
        "uae_east_outside": (ja, "no official TEU found, Jebel Ali ratio used (no adjustment)"),
        "oman_outside": (ratio_for(v, "Salalah", "H1 2025"), "Salalah, H1 2025"),
        "india_vs2024": (ratio_for(v, "Nhava Sheva (JNPA)", "FY24-25"), "Nhava Sheva, FY24-25"),
        "pakistan": (ratio_for(v, "Karachi (KPT)", "FY24-25"), "Karachi, FY24-25"),
        "colombo": (ratio_for(v, "Colombo (SLPA)", "H1 2025"), "Colombo, H1 2025"),
    }
    out = []
    for _, r in eff.iterrows():
        if r["phase"] == "pre_war":
            continue
        loss_kt = r["uae_inside"]
        loss_teu = loss_kt * 1000 / groups["uae_inside"][0]
        for g, (tpt, basis) in groups.items():
            if g == "uae_inside":
                continue
            teu = r[g] * 1000 / tpt
            out.append({
                "phase": r["phase"],
                "group": g,
                "effect_container_kt_per_day": round(r[g], 2),
                "tonnes_per_teu_used": round(tpt, 2),
                "ratio_basis": basis,
                "effect_teu_per_day": round(teu),
                "share_of_uae_loss_tonnes": -r[g] / loss_kt,
                "share_of_uae_loss_teu_equivalent": -teu / loss_teu,
            })
    t = pd.DataFrame(out)
    share_cols = ["share_of_uae_loss_tonnes", "share_of_uae_loss_teu_equivalent"]
    tot = (t.groupby("phase")[share_cols].sum()
           .reset_index().assign(group="all_outside_ex_red_sea", ratio_basis="sum"))
    t = pd.concat([t, tot], ignore_index=True)
    t[share_cols] = t[share_cols].round(3)
    order = {"closure": 0, "mou": 1, "renewed": 2}
    t["o"] = t["phase"].map(order)
    return t.sort_values(["o", "group"]).drop(columns="o")


def style(ax):
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def fig_visits(v):
    s = v[v["measure"].isin(["vessels_total", "vessels_container"])].copy()
    s["short"] = s["entity"].str.replace(r" \(.*\)", "", regex=True)
    kind = {"vessels_container": "container ships", "vessels_total": "all ships"}
    s["label"] = s["short"] + ", " + s["measure"].map(kind) + ", " + s["period"]
    s = s.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 0.3 * len(s) + 1.7))
    y = np.arange(len(s))
    cols = np.where(s["measure"] == "vessels_container", BLUE, GREY)
    ax.axvline(1, color=BASE, lw=1)
    ax.barh(y, s["portwatch_to_official"], height=0.6, color=cols)
    for yi, val in zip(y, s["portwatch_to_official"]):
        ax.text(val + 0.015, yi, f"{val:.2f}", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(y, s["label"], fontsize=7.5, color=INK2)
    ax.set_xlim(0, 1.25)
    ax.set_xlabel("PortWatch port calls as a share of the official vessel count (1.0 = same)", fontsize=8.5,
                  color=INK2)
    style(ax)
    ax.set_title("Ship visits: PortWatch against official counts", fontsize=10.5, color=INK, loc="left", pad=22)
    ax.text(0.0, 1.015, "Blue: container ships only   Grey: all ships (official counts usually include "
            "passenger, livestock and service vessels)", transform=ax.transAxes, fontsize=7.5, color=MUTED)
    fig.text(0.01, 0.01, "Nhava Sheva FY25-26 falls inside the PortWatch call count gap at the Indian ports.",
             fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    fig.savefig(OUT_F / "validation_absolute_ship_visits.png", dpi=160)
    plt.close(fig)


def fig_tonnes_per_teu(v):
    s = v[v["measure"] == "teu"].copy()
    s["short"] = s["entity"].str.replace(r" \(.*\)", "", regex=True)
    mid = pd.to_datetime(s["start"]) + (pd.to_datetime(s["end"]) - pd.to_datetime(s["start"])) / 2
    s["after"] = mid >= pd.Timestamp("2026-03-01")
    order = s.groupby("short")["tonnes_per_teu"].median().sort_values().index.tolist()
    offsets = [0.24, -0.30, 0.44, -0.50]
    fig, ax = plt.subplots(figsize=(9, 0.85 * len(order) + 1.5))
    for i, port in enumerate(order):
        p = s[s["short"] == port].sort_values("tonnes_per_teu").reset_index(drop=True)
        x = p["tonnes_per_teu"].values
        ax.plot([x.min(), x.max()], [i, i], color=BASE, lw=2, zorder=1)
        for j, r in p.iterrows():
            col = BLUE if r["after"] else GREY
            ax.plot(r["tonnes_per_teu"], i, "o", color=col, ms=7, mec="#fcfcfb", mew=1.5, zorder=3)
            ax.text(r["tonnes_per_teu"], i + offsets[j % 4], r["period"], ha="center", va="center",
                    fontsize=6.5, color=INK2)
    ax.set_yticks(range(len(order)), order, fontsize=8.5, color=INK2)
    ax.set_ylim(-0.75, len(order) - 0.35)
    ax.set_xlim(0, 13.5)
    ax.set_xlabel("PortWatch container tonnes per official TEU", fontsize=8.5, color=INK2)
    style(ax)
    ax.set_title("Container volumes: PortWatch tonnes per official TEU", fontsize=10.5, color=INK, loc="left",
                 pad=22)
    ax.text(0.0, 1.015, "Grey: period mostly before the war   Blue: mostly after 1 March 2026. A steady ratio "
            "within a port means PortWatch changes can be trusted there.", transform=ax.transAxes,
            fontsize=7.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(OUT_F / "validation_tonnes_per_teu.png", dpi=160)
    plt.close(fig)


def main():
    d = load()
    off = pd.read_csv(OFFICIAL)
    v = compare_levels(d, off)
    v.to_csv(OUT_T / "validation_absolute_levels.csv", index=False)
    t = teu_equivalent_shares(v)
    t.to_csv(OUT_T / "substitution_teu_equivalent.csv", index=False)
    fig_visits(v)
    fig_tonnes_per_teu(v)

    pd.set_option("display.width", 220)
    cols = ["entity", "measure", "period", "official", "portwatch", "portwatch_to_official", "tonnes_per_teu",
            "teu_per_container_call"]
    print(v[cols].round(2).to_string(index=False))
    print()
    print(t.drop(columns="ratio_basis").to_string(index=False))


if __name__ == "__main__":
    main()
