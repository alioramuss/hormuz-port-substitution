"""
First pass: did port traffic move from UAE ports inside the Strait of Hormuz
to ports outside it during the 2026 disruption?

Data: IMF PortWatch daily port activity (AIS based), 51 ports, 1 Jan 2024 to
13 Nov 2026. Each 2026 phase is compared with the same calendar dates in 2025.

Run from the project root:
    python src/analysis.py
"""

from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "portwatch_gulf_ports_2024_2026.csv"
GROUPS = ROOT / "config" / "port_groups.csv"
OUT_T = ROOT / "outputs" / "tables"
OUT_F = ROOT / "outputs" / "figures"
OUT_T.mkdir(parents=True, exist_ok=True)
OUT_F.mkdir(parents=True, exist_ok=True)

# Phases of the 2026 disruption. Dates come from news reporting, see README.
PHASES = [
    ("pre_war", "2026-01-01", "2026-02-27", "Before the war"),
    ("closure", "2026-03-01", "2026-06-14", "Closure"),
    ("mou", "2026-06-15", "2026-07-07", "MoU window"),
    ("renewed", "2026-07-08", "2026-11-13", "Renewed disruption"),
]

GROUP_ORDER = [
    "uae_core_inside",
    "uae_other_inside",
    "gulf_other_inside",
    "uae_east_outside",
    "oman_outside",
    "saudi_red_sea",
    "india",
    "pakistan",
    "colombo",
    "control",
]
GROUP_LABEL = {
    "uae_core_inside": "Jebel Ali + Khalifa (inside)",
    "uae_other_inside": "Other UAE Gulf ports (inside)",
    "gulf_other_inside": "Other Gulf states (inside)",
    "uae_east_outside": "Fujairah + Khor Fakkan (outside)",
    "oman_outside": "Oman ports (outside)",
    "saudi_red_sea": "Saudi Red Sea ports",
    "india": "India: Mundra + Nhava Sheva",
    "pakistan": "Pakistan: Karachi + Port Qasim",
    "colombo": "Colombo",
    "control": "Control ports (Singapore, Busan, Rotterdam)",
}

METRICS = {
    "calls": "Port calls per day",
    "container_calls": "Container ship calls per day",
    "tanker_calls": "Tanker calls per day",
    "other_cargo_calls": "Dry bulk, general cargo and ro-ro calls per day",
    "volume_kt": "Imports plus exports, thousand tonnes per day",
    "container_kt": "Container cargo (imports plus exports), thousand tonnes per day",
}

KEY_PORTS = [
    "port744", "port2025", "port362", "port561", "port988",
    "port746", "port984", "port518", "port2031", "port570",
]


def load():
    df = pd.read_csv(DATA, parse_dates=["date"])
    groups = pd.read_csv(GROUPS)[["portid", "group"]]
    df = df.merge(groups, on="portid", how="left")
    missing = df.loc[df["group"].isna(), "portid"].unique()
    if len(missing):
        raise ValueError(f"Ports with no group in config: {missing}")
    df = df[df["group"] != "excluded"].copy()
    df["calls"] = df["portcalls"]
    df["container_calls"] = df["portcalls_container"]
    df["tanker_calls"] = df["portcalls_tanker"]
    df["other_cargo_calls"] = (
        df["portcalls_dry_bulk"] + df["portcalls_general_cargo"] + df["portcalls_roro"]
    )
    df["volume_kt"] = (df["import"] + df["export"]) / 1000.0
    df["container_kt"] = (df["import_container"] + df["export_container"]) / 1000.0
    return df


def daily_by(df, key):
    return df.groupby([key, "date"])[list(METRICS)].sum().reset_index()


def window_mean(daily, key, start, end):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    w = daily[(daily["date"] >= s) & (daily["date"] <= e)]
    n_days = (e - s).days + 1
    # Sum then divide by calendar days, so a port-day missing from the file
    # would count as zero rather than silently shrinking the window.
    return w.groupby(key)[list(METRICS)].sum() / n_days


def phase_table(daily, key):
    rows = []
    for phase, start, end, label in PHASES:
        cur = window_mean(daily, key, start, end)
        base = window_mean(
            daily, key,
            pd.Timestamp(start) - pd.DateOffset(years=1),
            pd.Timestamp(end) - pd.DateOffset(years=1),
        )
        for k in cur.index:
            for m in METRICS:
                b, c = base.loc[k, m], cur.loc[k, m]
                rows.append({
                    "phase": phase, "phase_label": label,
                    "start": start, "end": end, key: k, "metric": m,
                    "mean_2025": b, "mean_2026": c, "change": c - b,
                    "pct_change": 100 * (c - b) / b if b else np.nan,
                })
    return pd.DataFrame(rows)


def add_control_gap(tbl):
    ctrl = tbl[tbl["group"] == "control"].set_index(["phase", "metric"])["pct_change"]
    tbl["pct_change_minus_control"] = tbl.apply(
        lambda r: r["pct_change"] - ctrl.loc[(r["phase"], r["metric"])], axis=1
    )
    return tbl


def substitution_table(gtbl):
    """Net daily change at the outside ports set against the loss at UAE ports inside."""
    rows = []
    piv = gtbl.pivot_table(index=["phase", "metric"], columns="group", values="change")
    for (phase, metric), r in piv.iterrows():
        uae_inside = r["uae_core_inside"] + r["uae_other_inside"]
        outside_near = r["uae_east_outside"] + r["oman_outside"]
        rows.append({
            "phase": phase, "metric": metric,
            "change_uae_inside": uae_inside,
            "change_uae_east_outside": r["uae_east_outside"],
            "change_oman_outside": r["oman_outside"],
            "change_saudi_red_sea": r["saudi_red_sea"],
            "change_outside_uae_plus_oman": outside_near,
            "share_of_uae_loss_offset_by_uae_east_plus_oman":
                -outside_near / uae_inside if uae_inside < 0 else np.nan,
            "share_of_uae_loss_offset_incl_red_sea":
                -(outside_near + r["saudi_red_sea"]) / uae_inside if uae_inside < 0 else np.nan,
        })
    out = pd.DataFrame(rows)
    order = {p[0]: i for i, p in enumerate(PHASES)}
    return out.sort_values(["phase", "metric"], key=lambda s: s.map(order) if s.name == "phase" else s)


def weekly_series(gdaily, key="group"):
    """Mean daily value per ISO week, for 2025 and 2026, aligned by week number."""
    d = gdaily.copy()
    d["year"] = d["date"].dt.year
    d = d[d["year"].isin([2024, 2025, 2026])]
    d["week"] = d["date"].dt.isocalendar().week.astype(int)
    d["iso_year"] = d["date"].dt.isocalendar().year.astype(int)
    d = d[d["iso_year"] == d["year"]]
    wk = d.groupby([key, "year", "week"]).agg(
        days=("date", "nunique"), week_start=("date", "min"),
        **{m: (m, "sum") for m in METRICS},
    ).reset_index()
    for m in METRICS:
        wk[m] = wk[m] / wk["days"]
    # Drop part weeks at the ends of the file.
    return wk[wk["days"] == 7].drop(columns="days")


def data_checks(df):
    base = df[(df["date"] >= "2025-01-01") & (df["date"] <= "2025-12-31")]
    chk = base.groupby(["portid", "portname", "group"]).agg(
        mean_calls_2025=("calls", "mean"),
        zero_call_days_2025=("calls", lambda s: int((s == 0).sum())),
        mean_container_calls_2025=("container_calls", "mean"),
    ).reset_index()
    chk["days_in_file"] = df.groupby("portid").size().reindex(chk["portid"]).values
    return chk.sort_values(["group", "mean_calls_2025"], ascending=[True, False])


def week_phase(week):
    """Phase of a 2026 ISO week, or None if the week straddles a phase boundary."""
    from datetime import date
    days = [pd.Timestamp(date.fromisocalendar(2026, int(week), d)) for d in range(1, 8)]
    for phase, start, end, _ in PHASES:
        if all(pd.Timestamp(start) <= x <= pd.Timestamp(end) for x in days):
            return phase
    return None


def newey_west_se(x, lags=3):
    """Standard error of the mean of a weekly series, allowing for autocorrelation."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2:
        return np.nan
    e = x - x.mean()
    L = min(lags, n - 1)
    var = e @ e / n
    for lag in range(1, L + 1):
        w = 1 - lag / (L + 1)
        var += 2 * w * (e[lag:] @ e[:-lag]) / n
    return np.sqrt(max(var, 0) / n)


def control_adjusted_effects(wk_unit, wk_control, key, base=2025):
    """
    For each unit (port group or port), week and metric:
        expected_2026 = value_base * (control_2026 / control_base)
    where base is 2025 by default (2024 for ports with bad 2025 data).
        effect        = value_2026 - expected_2026
    i.e. the change beyond what the control ports' trend predicts for that
    week. Weeks are then averaged within each phase, with Newey-West 95% CIs.
    Weeks that straddle a phase boundary are left out.
    """
    c = wk_control.pivot_table(index="week", columns="year", values=list(METRICS))
    rows = []
    for unit, w in wk_unit.groupby(key):
        p = w.pivot_table(index="week", columns="year", values=list(METRICS))
        weeks = [x for x in p.index if x in c.index
                 and not p.loc[x, (slice(None), [base, 2026])].isna().any()
                 and not c.loc[x, (slice(None), [base, 2026])].isna().any()]
        for m in METRICS:
            v25, v26 = p.loc[weeks, (m, base)], p.loc[weeks, (m, 2026)]
            ratio = c.loc[weeks, (m, 2026)] / c.loc[weeks, (m, base)]
            exp26 = v25 * ratio
            eff = v26 - exp26
            ph = pd.Series([week_phase(x) for x in weeks], index=weeks)
            for phase, _, _, label in PHASES:
                sel = ph[ph == phase].index
                if len(sel) == 0:
                    continue
                mean = eff.loc[sel].mean()
                se = newey_west_se(eff.loc[sel].values)
                rows.append({
                    key: unit, "metric": m, "phase": phase, "phase_label": label,
                    "baseline_year": base,
                    "n_weeks": len(sel),
                    "actual_2026": v26.loc[sel].mean(),
                    "expected_2026": exp26.loc[sel].mean(),
                    "effect": mean,
                    "ci_low": mean - 1.96 * se, "ci_high": mean + 1.96 * se,
                    "effect_pct": 100 * eff.loc[sel].sum() / exp26.loc[sel].sum()
                    if exp26.loc[sel].sum() else np.nan,
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- figures

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
BLUE = "#2a78d6"
CAT = {"uae_inside": "#2a78d6", "uae_east_outside": "#eb6834",
       "oman_outside": "#1baf7a", "saudi_red_sea": "#eda100"}
PHASE_SHADE = {"closure": "#f0efec", "mou": "#ffffff", "renewed": "#f0efec"}


def style(ax):
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_small_multiples(wk, metric, fname, title):
    groups = [g for g in GROUP_ORDER if g != "control"] + ["control"]
    fig, axes = plt.subplots(6, 2, figsize=(11, 15), sharex=True)
    axes = axes.ravel()
    axes[-2].axis("off")
    for ax, g in zip(axes, groups):
        w = wk[wk["group"] == g]
        w25 = w[w["year"] == 2025].set_index("week")[metric]
        w26 = w[w["year"] == 2026].set_index("week")[metric]
        for ph, s, e, _ in PHASES[1:]:
            ws, we = pd.Timestamp(s).isocalendar().week, pd.Timestamp(e).isocalendar().week
            ax.axvspan(ws - 0.5, we + 0.5, color=PHASE_SHADE[ph], zorder=0, lw=0)
        ax.plot(w25.index, w25.values, color=MUTED, lw=1.5, label="2025")
        ax.plot(w26.index, w26.values, color=BLUE, lw=2, label="2026")
        ax.set_title(GROUP_LABEL[g], fontsize=9.5, color=INK, loc="left")
        ax.set_ylim(bottom=0)
        style(ax)
    axes[-1].axis("off")
    axes[-1].text(0.02, 0.75, "Grey: 2025   Blue: 2026", color=INK2, fontsize=9, transform=axes[-1].transAxes)
    axes[-1].text(0.02, 0.55, "Shaded: closure (1 Mar to 14 Jun)\nand renewed disruption (from 8 Jul)",
                  color=INK2, fontsize=9, transform=axes[-1].transAxes)
    axes[-1].text(0.02, 0.25, "Source: IMF PortWatch, weekly mean of daily values.\nIndia's 2025 line has a data gap from May 2025 to Apr 2026.",
                  color=MUTED, fontsize=8, transform=axes[-1].transAxes)
    # Month labels instead of ISO week numbers
    month_weeks = [pd.Timestamp(2026, m, 1).isocalendar().week for m in range(1, 13)]
    month_weeks[0] = 1
    for ax in axes[:len(groups)]:
        ax.set_xticks(month_weeks, ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
        ax.set_xlim(0.5, 52.5)
    axes[len(groups) - 1].tick_params(labelbottom=True)
    axes[len(groups) - 2].tick_params(labelbottom=True)
    fig.suptitle(title, x=0.06, ha="left", fontsize=12, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT_F / fname, dpi=160)
    plt.close(fig)


def fig_container_shift(gtbl):
    t = gtbl[gtbl["metric"] == "container_calls"].pivot_table(index="phase", columns="group", values="change")
    t["uae_inside"] = t["uae_core_inside"] + t["uae_other_inside"]
    phases = [p for p in PHASES if p[0] != "pre_war"]
    cols = ["uae_inside", "uae_east_outside", "oman_outside", "saudi_red_sea"]
    labels = {"uae_inside": "UAE ports inside", "uae_east_outside": "Fujairah + Khor Fakkan",
              "oman_outside": "Oman ports", "saudi_red_sea": "Saudi Red Sea ports"}
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(len(phases))
    bw = 0.19
    for i, c in enumerate(cols):
        vals = [t.loc[p[0], c] for p in phases]
        ax.bar(x + (i - 1.5) * (bw + 0.02), vals, bw, color=CAT[c], label=labels[c], zorder=2)
        for xi, v in zip(x, vals):
            ax.text(xi + (i - 1.5) * (bw + 0.02), v + (0.4 if v >= 0 else -0.4), f"{v:+.1f}",
                    ha="center", va="bottom" if v >= 0 else "top", fontsize=7.5, color=INK2)
    ax.axhline(0, color="#c3c2b7", lw=1)
    nice = lambda d: f"{pd.Timestamp(d).day} {pd.Timestamp(d).strftime('%b')}"  # %-d breaks on Windows
    ax.set_xticks(x, [f"{p[3]}\n{nice(p[1])} to {nice(p[2])}" for p in phases], fontsize=8.5, color=INK2)
    ax.set_ylabel("Change in container calls per day\nvs same dates in 2025", fontsize=8.5, color=INK2)
    style(ax)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.text(0.01, 0.01, "Source: IMF PortWatch daily port calls", fontsize=7.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(OUT_F / "container_shift_by_phase.png", dpi=160)
    plt.close(fig)


def fig_effects(eff):
    """Control-adjusted change by group and phase, container calls and container tonnes."""
    groups = ["uae_core_inside", "uae_other_inside", "uae_east_outside", "oman_outside", "saudi_red_sea"]
    short = {"uae_core_inside": "Jebel Ali + Khalifa", "uae_other_inside": "Other UAE Gulf",
             "uae_east_outside": "Fujairah + Khor Fakkan", "oman_outside": "Oman",
             "saudi_red_sea": "Saudi Red Sea"}
    phases = [("closure", "Closure", "#2a78d6"), ("mou", "MoU window", "#eb6834"),
              ("renewed", "Renewed disruption", "#1baf7a")]
    metrics = [("container_calls", "Container ship calls per day"),
               ("container_kt", "Container cargo, thousand tonnes per day")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, (m, mlabel) in zip(axes, metrics):
        for j, (ph, plabel, col) in enumerate(phases):
            for i, g in enumerate(groups):
                r = eff[(eff["group"] == g) & (eff["metric"] == m) & (eff["phase"] == ph)]
                if r.empty:
                    continue
                r = r.iloc[0]
                y = i + (j - 1) * 0.24
                ax.plot([r["ci_low"], r["ci_high"]], [y, y], color=col, lw=2, alpha=0.55)
                ax.plot(r["effect"], y, "o", color=col, ms=6, mec="#fcfcfb", mew=1.5,
                        label=plabel if i == 0 else None)
        ax.axvline(0, color="#c3c2b7", lw=1)
        ax.set_yticks(range(len(groups)), [short[g] for g in groups], fontsize=8.5, color=INK2)
        ax.set_title(mlabel, fontsize=9.5, color=INK, loc="left")
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.yaxis.grid(False)
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors=MUTED, labelsize=8, length=0)
    axes[0].invert_yaxis()  # shared y axis: invert once only
    axes[0].legend(frameon=False, fontsize=8, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.06))
    fig.suptitle("Change beyond the control-port trend, vs same weeks of 2025 (dots: mean, bars: 95% CI)",
                 x=0.01, ha="left", fontsize=10.5, color=INK)
    fig.text(0.01, 0.01, "Source: IMF PortWatch. Weekly effects averaged by phase, Newey-West intervals. "
             "MoU window has only 3 full weeks.", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(OUT_F / "control_adjusted_effects.png", dpi=160)
    plt.close(fig)


def fig_where_cargo_went(eff25, eff24, phase="renewed"):
    """Control-adjusted change in container cargo outside the strait, one phase."""
    rows = [
        ("Fujairah + Khor Fakkan", eff25, "uae_east_outside"),
        ("Oman ports", eff25, "oman_outside"),
        ("India (vs 2024)", eff24, "india"),
        ("Pakistan", eff25, "pakistan"),
        ("Colombo", eff25, "colombo"),
    ]
    sel = lambda e, g: e[(e["group"] == g) & (e["metric"] == "container_kt") & (e["phase"] == phase)].iloc[0]
    lost = sel(eff25, "uae_core_inside")["effect"] + sel(eff25, "uae_other_inside")["effect"]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for i, (label, e, g) in enumerate(rows):
        r = sel(e, g)
        ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=BLUE, lw=2.5, alpha=0.5)
        ax.plot(r["effect"], i, "o", color=BLUE, ms=8, mec="#fcfcfb", mew=1.5)
        ax.text(max(r["ci_high"], r["effect"]) + 4, i, f"{r['effect']:+.0f}", va="center", fontsize=8.5, color=INK2)
    ax.axvline(0, color="#c3c2b7", lw=1)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=9, color=INK2)
    ax.invert_yaxis()
    ax.set_xlabel("Change in container cargo beyond control-port trend, thousand tonnes per day", fontsize=8.5, color=INK2)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    label = dict((p[0], p[3]) for p in PHASES)[phase]
    ax.set_title(f"Where did the container cargo go? {label}, 8 Jul to 13 Nov 2026\n"
                 f"(UAE ports inside the strait lost about {-lost:.0f} thousand tonnes a day)",
                 fontsize=10.5, color=INK, loc="left")
    fig.text(0.01, 0.01, "Source: IMF PortWatch. Dots: mean weekly effect, bars: 95% CI. India compared with 2024 because of a "
             "PortWatch data gap in 2025. Saudi Red Sea left out: PortWatch shows a collapse\nbut official figures show record "
             "volumes at Jeddah (likely ships switching off AIS). Official figures also show more growth at Oman and Colombo "
             "than PortWatch does.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT_F / "where_container_cargo_went.png", dpi=160)
    plt.close(fig)


def south_asia_check(df):
    """Monthly calls and container tonnes at the South Asian ports, to show the 2025 data gap."""
    sa = df[df["group"].isin(["india", "pakistan", "colombo"])].copy()
    sa["month"] = sa["date"].dt.strftime("%Y-%m")
    return sa.groupby(["portname", "month"]).agg(
        calls_per_day=("calls", "mean"), container_kt_per_day=("container_kt", "mean")
    ).reset_index()


def main():
    df = load()
    gdaily = daily_by(df, "group")
    pdaily = daily_by(df, "portid")

    gtbl = add_control_gap(phase_table(gdaily, "group"))
    gtbl["group_label"] = gtbl["group"].map(GROUP_LABEL)
    gtbl.to_csv(OUT_T / "phase_change_by_group.csv", index=False)

    ptbl = phase_table(pdaily, "portid")
    names = df[["portid", "portname", "group"]].drop_duplicates()
    ptbl = ptbl.merge(names, on="portid")
    ptbl.to_csv(OUT_T / "phase_change_by_port.csv", index=False)

    sub = substitution_table(gtbl)
    sub.to_csv(OUT_T / "substitution_accounting.csv", index=False)

    wk = weekly_series(gdaily)
    wk.to_csv(OUT_T / "weekly_by_group.csv", index=False)

    chk = data_checks(df)
    chk.to_csv(OUT_T / "data_checks.csv", index=False)

    wk_control = wk[wk["group"] == "control"]
    eff = control_adjusted_effects(wk[wk["group"] != "control"], wk_control, "group")
    eff["group_label"] = eff["group"].map(GROUP_LABEL)
    eff.to_csv(OUT_T / "control_adjusted_effects_by_group.csv", index=False)

    eff24 = control_adjusted_effects(wk[wk["group"] != "control"], wk_control, "group", base=2024)
    eff24["group_label"] = eff24["group"].map(GROUP_LABEL)
    eff24.to_csv(OUT_T / "control_adjusted_effects_by_group_vs2024.csv", index=False)
    south_asia_check(df).to_csv(OUT_T / "south_asia_monthly_check.csv", index=False)
    fig_where_cargo_went(eff, eff24)

    pwk = weekly_series(pdaily[pdaily["portid"].isin(KEY_PORTS)], key="portid")
    peff = control_adjusted_effects(pwk, wk_control, "portid").merge(names, on="portid")
    peff.to_csv(OUT_T / "control_adjusted_effects_by_port.csv", index=False)
    fig_effects(eff)

    # Substitution shares from the control-adjusted effects
    pv = eff.pivot_table(index=["phase", "metric"], columns="group", values="effect")
    pv24 = eff24.pivot_table(index=["phase", "metric"], columns="group", values="effect")
    sc = pd.DataFrame({
        "uae_inside": pv["uae_core_inside"] + pv["uae_other_inside"],
        "uae_east_outside": pv["uae_east_outside"],
        "oman_outside": pv["oman_outside"],
        "saudi_red_sea": pv["saudi_red_sea"],
        "india_vs2024": pv24["india"],
        "pakistan": pv["pakistan"],
        "colombo": pv["colombo"],
    })
    lost = -sc["uae_inside"].where(sc["uae_inside"] < 0)
    sc["share_offset_uae_east"] = sc["uae_east_outside"] / lost
    sc["share_offset_uae_east_plus_oman"] = (sc["uae_east_outside"] + sc["oman_outside"]) / lost
    sc["share_offset_india_plus_pakistan"] = (sc["india_vs2024"] + sc["pakistan"]) / lost
    sc["share_offset_all_outside_ex_red_sea"] = (
        sc["uae_east_outside"] + sc["oman_outside"] + sc["india_vs2024"] + sc["pakistan"] + sc["colombo"]) / lost
    sc.reset_index().to_csv(OUT_T / "substitution_control_adjusted.csv", index=False)
    print()
    print(sc.loc[(slice(None), ["container_calls", "container_kt"]), :].round(3).to_string())

    fig_small_multiples(wk, "calls", "weekly_calls_by_group.png",
                        "Port calls per day by port group, 2025 vs 2026")
    fig_small_multiples(wk, "container_calls", "weekly_container_calls_by_group.png",
                        "Container ship calls per day by port group, 2025 vs 2026")
    fig_container_shift(gtbl)

    # Short console summary
    pd.set_option("display.width", 160)
    s = gtbl[gtbl["metric"].isin(["calls", "container_calls", "volume_kt"])]
    print(s.pivot_table(index=["group"], columns=["phase", "metric"], values="pct_change")
          .reindex(GROUP_ORDER).round(0).to_string())
    print()
    print(sub[sub["metric"].isin(["container_calls", "calls", "volume_kt"])].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
