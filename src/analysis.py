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
    "control",
]
GROUP_LABEL = {
    "uae_core_inside": "Jebel Ali + Khalifa (inside)",
    "uae_other_inside": "Other UAE Gulf ports (inside)",
    "gulf_other_inside": "Other Gulf states (inside)",
    "uae_east_outside": "Fujairah + Khor Fakkan (outside)",
    "oman_outside": "Oman ports (outside)",
    "saudi_red_sea": "Saudi Red Sea ports",
    "control": "Control ports (India, Pakistan, Sri Lanka, Singapore, Busan, Rotterdam)",
}

METRICS = {
    "calls": "Port calls per day",
    "container_calls": "Container ship calls per day",
    "tanker_calls": "Tanker calls per day",
    "other_cargo_calls": "Dry bulk, general cargo and ro-ro calls per day",
    "volume_kt": "Imports plus exports, thousand tonnes per day",
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


def weekly_series(gdaily):
    """Mean daily value per ISO week, for 2025 and 2026, aligned by week number."""
    d = gdaily.copy()
    d["year"] = d["date"].dt.year
    d = d[d["year"].isin([2025, 2026])]
    d["week"] = d["date"].dt.isocalendar().week.astype(int)
    d["iso_year"] = d["date"].dt.isocalendar().year.astype(int)
    d = d[d["iso_year"] == d["year"]]
    wk = d.groupby(["group", "year", "week"]).agg(
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
    fig, axes = plt.subplots(4, 2, figsize=(11, 11), sharex=True)
    axes = axes.ravel()
    for ax, g in zip(axes, groups):
        w = wk[wk["group"] == g]
        w25 = w[w["year"] == 2025].set_index("week")[metric]
        w26 = w[w["year"] == 2026].set_index("week")[metric]
        for ph, s, e, _ in PHASES[1:]:
            ws, we = pd.Timestamp(s).isocalendar().week, pd.Timestamp(e).isocalendar().week
            ax.axvspan(ws - 0.5, we + 0.5, color=PHASE_SHADE[ph], zorder=0, lw=0)
        ax.plot(w25.index, w25.values, color=MUTED, lw=1.5, label="2025")
        ax.plot(w26.index, w26.values, color=BLUE, lw=2, label="2026")
        ax.set_title(GROUP_LABEL[g].split(" (India")[0], fontsize=9.5, color=INK, loc="left")
        ax.set_ylim(bottom=0)
        style(ax)
    axes[-1].axis("off")
    axes[-1].text(0.02, 0.75, "Grey: 2025   Blue: 2026", color=INK2, fontsize=9, transform=axes[-1].transAxes)
    axes[-1].text(0.02, 0.55, "Shaded: closure (1 Mar to 14 Jun)\nand renewed disruption (from 8 Jul)",
                  color=INK2, fontsize=9, transform=axes[-1].transAxes)
    axes[-1].text(0.02, 0.25, "Source: IMF PortWatch, weekly mean of daily values",
                  color=MUTED, fontsize=8, transform=axes[-1].transAxes)
    # Month labels instead of ISO week numbers
    month_weeks = [pd.Timestamp(2026, m, 1).isocalendar().week for m in range(1, 13)]
    month_weeks[0] = 1
    for ax in axes[:-1]:
        ax.set_xticks(month_weeks, ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
        ax.set_xlim(0.5, 52.5)
    axes[-2].tick_params(labelbottom=True)
    axes[-3].tick_params(labelbottom=True)
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
