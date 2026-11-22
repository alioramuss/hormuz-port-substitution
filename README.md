# UAE ports inside and outside the Strait of Hormuz during the 2026 disruption

Did port traffic move from the UAE ports inside the strait (Jebel Ali, Khalifa) to ports outside it when Hormuz was closed in 2026, and if not, where did it go? This repo looks at that question using IMF PortWatch daily port data, checked against official port statistics.

Status: fourth pass, 22 Nov 2026. Numbers will change as the method gets tightened.

## Headline

1. **The collapse inside the strait is real, and PortWatch measures it well.** Jebel Ali's container throughput fell 90.1% in Q2 2026 according to DP World; PortWatch shows -92% in container calls and -91% in container tonnes.
2. **In PortWatch, about a fifth of the lost UAE container cargo turns up at other ports since July:** about 6% at Fujairah and Khor Fakkan, about 11% at Indian and Pakistani ports, and about 5% in Oman.
3. **That fifth is a floor, not an estimate.** Checked against official figures, PortWatch misses growth at several of the ports that took the diverted cargo: it shows Jeddah collapsing after July when Jeddah actually set monthly records, it shows Salalah and Colombo roughly flat when they grew 12 to 23%, and it overstates the fall at AD Ports' UAE terminals, which include the rerouted east coast traffic. Operators' own figures point the same way: DP World moved more than a million TEU from UAE east coast ports to Jebel Ali by road and rail between March and October, and Gulftainer estimated Khor Fakkan was handling 80 to 90% of UAE container demand.

The main way PortWatch goes wrong here is AIS coverage (ships switching off transponders, and data gaps), not just its tonnage estimates.

## Data

IMF PortWatch daily port activity, pulled from the public ArcGIS service behind portwatch.imf.org. Daily port calls by vessel type (container, dry bulk, general cargo, ro-ro, tanker) and estimated import and export volumes in tonnes, built from AIS ship tracking.

51 ports, 1 Jan 2024 to 13 Nov 2026 (the latest day available when pulled), every port has all 1,048 days.

Official figures (TEU, year-on-year) are collected by hand in `data/official/official_port_stats.csv`, each with its source.

Port groups are in `config/port_groups.csv`:

| Group | Ports |
|---|---|
| UAE core, inside | Jebel Ali, Khalifa Port |
| Other UAE Gulf ports, inside | Mina Rashid, Mina Zayed, Sharjah, Ajman, Mina Saqr, Hamriyah, Ruwais, Umm al Qaiwain, Das Island, Jebel Dhanna, Zirku |
| Other Gulf states, inside | Saudi east coast, Qatar, Kuwait, Bahrain, Umm Qasr |
| UAE east coast, outside | Fujairah, Khor Fakkan |
| Oman, outside | Sohar, Salalah, Duqm, Sultan Qaboos |
| Saudi Red Sea | Jeddah, King Abdullah Port, Yanbu (two), Rabigh, Shoaiba, Duba (two) |
| India | Mundra, Nhava Sheva |
| Pakistan | Karachi, Port Qasim |
| Colombo | Colombo |
| Control | Singapore, Busan, Rotterdam |

Qalhat LNG terminal is pulled but left out, since LNG exports are not a substitution route. In the first version, the Indian, Pakistani and Sri Lankan ports were part of the control group; they may have received diverted cargo, so they are now their own groups.

## Phases

Each 2026 phase is compared with the same calendar dates in 2025 (2024 for India, see below).

| Phase | Dates | What happened |
|---|---|---|
| Before the war | 1 Jan to 27 Feb | Normal traffic |
| Closure | 1 Mar to 14 Jun | US and Israeli strikes on Iran on 28 Feb, strait effectively closed |
| MoU window | 15 Jun to 7 Jul | US and Iran MoU agreed 15 Jun and signed 17 Jun, traffic partly returns |
| Renewed disruption | 8 Jul to 13 Nov | Tanker attacks and US strikes from 7 to 8 Jul, Houthi blockade of Saudi shipping from 20 Jul, MoU expired 17 Aug |

## Validation against official port statistics

For each official figure, the same ports and dates are pulled from PortWatch and compared year on year. Code: `src/validate_official.py`. Table: `outputs/tables/validation_official_vs_portwatch.csv`. Chart: `outputs/figures/validation_official_vs_portwatch.png`.

| Port or operator | Period | Official TEU | PortWatch container calls | PortWatch container tonnes |
|---|---|---|---|---|
| Jebel Ali (DP World) | Q1 2026 | -30.5% | -38.7% | -28.6% |
| Jebel Ali (DP World) | Q2 2026 | -90.1% | -92.2% | -90.9% |
| AD Ports UAE terminals | Q2 2026 | -65% | -76.6% | -77.4% |
| AD Ports UAE terminals | Q3 2026 | -57% | -76.2% | -79.2% |
| Saudi ports (Mawani) | Jan 2026 | +2.0% | -1.5% | +1.6% |
| Saudi ports (Mawani) | Feb 2026 | +20.9% | +0.9% | +1.6% |
| Saudi ports (Mawani) | Apr 2026 | -18.6% | -16.2% | -7.1% |
| Saudi ports (Mawani) | Jul 2026 | -17.5% | -41.3% | -41.7% |
| Saudi ports (Mawani) | Oct 2026 | +14% | -83.7% | -89.2% |
| Nhava Sheva (JNPA) | Jan to Jun 2026 | +13.6% | -33.3% | +14.3% |
| Nhava Sheva (JNPA) | Sep 2026 | +28.6% | +112.5% | +22.6% |
| Nhava Sheva (JNPA) | Oct 2026 | +27.1% | +106.8% | +21.6% |
| Mundra (Adani Ports, company-wide) | Sep 2026 | +15% | +74.4% | +64.7% |
| Mundra (Adani Ports, company-wide) | Oct 2026 | +21% | +95.9% | +73.1% |
| Salalah | Jan to Jun 2026 | +15% | +2.3% | -1.6% |
| Salalah | Jul to Sep 2026 (derived) | +23% | +9.6% | +9.6% |
| Sohar | Jan to Jun 2026 | +40% | -10.9% | +31.1% |
| Colombo | Jan to Apr 2026 | +13.9% | 0.0% | +1.2% |
| Colombo | Jan to Jun 2026 | +11.9% | -0.2% | -2.7% |

What this shows:

- **Jebel Ali: PortWatch is right.** Both calls and tonnes are within a few points of DP World's figures in both quarters.
- **AD Ports' UAE terminals: PortWatch overstates the fall by 12 to 22 points.** AD Ports' UAE figure includes Fujairah Terminals, where it rerouted cargo; PortWatch records very little container traffic there.
- **Saudi Red Sea after July: PortWatch is badly wrong.** It shows Jeddah's container calls falling from 121 in October 2025 to 14 in October 2026, but Jeddah set monthly records of 540,107 TEU in July and 582,900 TEU in October, and Saudi container volumes overall were up 14% in October. The most likely reason is ships switching off AIS in the Red Sea after the Houthi blockade threat. So the "collapse" of the Saudi Red Sea ports in Results 1 and 2 below is not real.
- **India: tonnes work, calls do not.** At Nhava Sheva, PortWatch tonnes track the official growth (+14% vs +14% in H1, +23% vs +29% in September), while calls are distorted by a PortWatch gap in 2025 (see below). Mundra looks inflated against 2025 for the same reason, although Adani only reports company-wide growth, so that comparison is rougher.
- **Salalah, Colombo and Sohar: PortWatch understates growth.** Official figures grew 12 to 40%; PortWatch calls grew far less or fell.

This partly matches the general advice that port calls are more reliable than PortWatch's import and export estimates, but here the bigger problem is AIS coverage, which affects calls and tonnes alike.

## Khor Fakkan

- PortWatch's 2026 container call counts at Khor Fakkan (23 in April, 26 in May, 37 in June) are close to ship counts from Xeneta's eeSea liner database reported by The Loadstar (21, 23 and 26). So the calls look plausible.
- The cargo does not. Gulftainer reported weekly throughput rising from about 8 thousand to 65 thousand TEU during the disruption, and estimated it was handling 80 to 90% of UAE container demand. PortWatch credits Fujairah and Khor Fakkan together with only about 34 thousand tonnes of container cargo a day since July, far less than 65 thousand TEU a week would imply.
- The 2025 baseline is uncertain. PortWatch shows only about 0.2 container calls a day there in 2025. Lloyd's List puts Khorfakkan/Sharjah at about 2.6 million TEU in 2025, but Khor Fakkan's throughput figures have not been published since 2018, so that number may be an estimate.

The PortWatch numbers for Khor Fakkan should not be relied on alone.

## Results 1: simple change vs 2025 (PortWatch)

| Group | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Jebel Ali + Khalifa, all calls | -90% | -77% | -81% |
| Other UAE Gulf ports, all calls | -54% | -36% | -40% |
| Fujairah + Khor Fakkan, all calls | -66% | -50% | -23% |
| Fujairah + Khor Fakkan, container calls | +253% | +550% | +1050% |
| Oman ports, all calls | -6% | +2% | +1% |
| Saudi Red Sea, all calls (see validation) | +32% | +64% | -63% |
| Pakistan, container cargo | +21% | +45% | +23% |
| Control ports, all calls | -2% | -3% | -5% |

Total calls at Fujairah and Khor Fakkan fell even as container calls rose, because Fujairah's tanker and bunkering traffic dropped sharply.

## Results 2: control-adjusted, with confidence intervals (PortWatch)

For each port group and week, the expected 2026 value is the baseline value for the same ISO week scaled by the control ports' 2026/baseline ratio for that week. The effect is actual minus expected. Weekly effects are averaged within each phase, with Newey-West 95% intervals (3 lags). Weeks that straddle a phase boundary are left out, which leaves 7 pre-war weeks, 15 closure weeks, 3 MoU weeks and 17 renewed-disruption weeks. Code: `control_adjusted_effects()` in `src/analysis.py`.

Container cargo, thousand tonnes per day (95% CI in brackets):

| Group | Before the war (placebo) | Closure | Renewed disruption |
|---|---|---|---|
| Jebel Ali + Khalifa | +23 (-22 to +67) | -536 (-561 to -511) | -502 (-524 to -480) |
| Other UAE Gulf ports | 0 (-2 to +2) | -7 (-9 to -5) | -5 (-6 to -3) |
| Fujairah + Khor Fakkan | -3 (-3 to -2) | +16 (+8 to +24) | +32 (+28 to +35) |
| Oman ports | +24 (+8 to +41) | -9 (-27 to +10) | +26 (+3 to +49) |
| Saudi Red Sea (see validation) | -17 (-33 to -2) | +16 (-10 to +43) | -94 (-128 to -59) |
| India (vs 2024) | +2 (-37 to +40) | +24 (-18 to +66) | +49 (+15 to +84) |
| Pakistan | 0 (-10 to +10) | +5 (-3 to +12) | +6 (+2 to +10) |
| Colombo | -5 (-13 to +3) | -3 (-10 to +4) | -9 (-13 to -5) |

Share of the UAE container cargo loss turning up elsewhere in PortWatch:

| | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Fujairah + Khor Fakkan | 3% | 5% | 6% |
| Fujairah + Khor Fakkan + Oman | 1% | -3% | 11% |
| India + Pakistan | 5% | 13% | 11% |
| All of the above plus Colombo | 6% | 9% | 20% |

Saudi Red Sea ports are left out of the shares: before July most of their change is crude oil, and after July PortWatch misses most of their traffic. Given the validation above, these shares are a lower bound.

The pre-war column is a placebo test: before the war there should be no effect. Most groups pass. Oman does not (+24 before the war), so its later rise is hard to separate from a trend it already had.

## Data gap at the Indian ports

PortWatch call counts at Mundra and Nhava Sheva drop sharply from about May 2025 to April 2026 (Nhava Sheva goes from about 27 calls a day to 7 or 8, then back to about 25 by May 2026), while Nhava Sheva's container tonnes stay steady and match JNPA's official figures. So India is compared with the same weeks of 2024 instead, and judged on container tonnes. Monthly numbers: `outputs/tables/south_asia_monthly_check.csv`.

## Caveats

- **AIS coverage.** Ships switching off transponders (very likely in the Red Sea after July, and possibly in the Gulf) and GNSS jamming hide traffic from PortWatch.
- **Official figures are not like for like.** They are in TEU, while PortWatch gives calls and tonnes; some are company-wide (Adani) or cover several terminals (AD Ports); one Salalah figure is derived from a nine-month total.
- **TEU throughput double counts transshipment.** A box moved through a hub is counted when unloaded and again when loaded.
- **Land routes are invisible to port data.** Cargo landed at Khor Fakkan, Fujairah or Sohar and trucked to Dubai shows up only where it landed.
- **The control is small.** Three large ports far from the Gulf stand in for what would have happened without the war.
- **Some demand simply disappeared.** Not all lost cargo had to go somewhere else.

## Next steps

- Build a substitution estimate from official monthly TEU where it exists (Jebel Ali, AD Ports, Mawani by port, JNPA, Salalah, Colombo), adjusted for each port's pre-war trend, and use PortWatch only where official data is missing.
- Get monthly Jeddah figures for 2025 and 2026 to measure how much of the Red Sea traffic PortWatch misses.
- Add more control ports and check the results hold.

## How to run

```
py -m pip install -r requirements.txt
py src/fetch_portwatch.py      # optional, re-downloads the data
py src/analysis.py
py src/validate_official.py
```

## Sources

Phase dates: Profit / Pakistan Today (18 Apr 2026); Majalla and S&P Global (18 Jun 2026); Al Jazeera (8 Jul, 20 Jul and 17 Aug 2026); AP (20 Jul 2026).

Official port figures (details and links in `data/official/official_port_stats.csv`): DP World H1 2026 results (via Seatrade Maritime, Semafor); AD Ports Group Q2 and Q3 2026 results; Saudi Ports Authority (Mawani) monthly releases (via Port Technology International, TradeArabia, Saudi Gazette, Arab News); JNPA performance reports and Maritime Gateway; Adani Ports monthly updates; Salalah Port Services (via Zawya, Oman Observer); Oman Observer and The Maritime Standard (Sohar); Sri Lanka Ports Authority (via Ada Derana, Daily FT).

Khor Fakkan: Xeneta eeSea ship counts and throughput history via The Loadstar; Gulftainer weekly throughput via EnterpriseAM; Gulftainer share of UAE demand and capacity via AGBI; Lloyd's List One Hundred Ports. DP World east coast land corridor: WAM, 11 Nov 2026.

Data: IMF PortWatch, portwatch.imf.org.
