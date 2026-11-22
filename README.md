# UAE ports inside and outside the Strait of Hormuz during the 2026 disruption

Did port traffic move from the UAE ports inside the strait (Jebel Ali, Khalifa) to ports outside it when Hormuz was closed in 2026, and if not, where did it go? This repo looks at that question using IMF PortWatch daily port data.

Status: third pass, 22 Nov 2026. Numbers will change as the method gets tightened.

## Headline

Since July, about a fifth of the container cargo lost at the UAE ports inside the strait (roughly 507 thousand tonnes a day) turns up at other ports in PortWatch:

- about 6% at Fujairah and Khor Fakkan,
- about 11% at Indian and Pakistani ports, consistent with transshipment moving east rather than to the UAE coast,
- about 5% in Oman, though Oman was already growing faster than the control ports before the war, so this part is weak evidence.

Colombo fell. The Saudi Red Sea ports picked up cargo during the closure but collapsed after the Houthi blockade of Saudi shipping in July.

The real shift to the UAE east coast is probably bigger than PortWatch shows: its numbers for Khor Fakkan look far too low (see below), and ships turning off AIS would hide some traffic. Capacity also limits how much could move there: Gulftainer is expanding Khor Fakkan from 3.5 to 5 million TEU a year.

## Data

IMF PortWatch daily port activity, pulled from the public ArcGIS service behind portwatch.imf.org. Daily port calls by vessel type (container, dry bulk, general cargo, ro-ro, tanker) and estimated import and export volumes in tonnes, built from AIS ship tracking.

51 ports, 1 Jan 2024 to 13 Nov 2026 (the latest day available when pulled), every port has all 1,048 days.

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

Qalhat LNG terminal is pulled but left out, since LNG exports are not a substitution route.

In the first version, the Indian, Pakistani and Sri Lankan ports were part of the control group. They may have received diverted transshipment, which would contaminate the control, so they are now their own groups and the control is only ports far from both chokepoints.

## Phases

Each 2026 phase is compared with the same calendar dates in 2025 (2024 for India, see below).

| Phase | Dates | What happened |
|---|---|---|
| Before the war | 1 Jan to 27 Feb | Normal traffic |
| Closure | 1 Mar to 14 Jun | US and Israeli strikes on Iran on 28 Feb, strait effectively closed |
| MoU window | 15 Jun to 7 Jul | US and Iran MoU agreed 15 Jun and signed 17 Jun, traffic partly returns |
| Renewed disruption | 8 Jul to 13 Nov | Tanker attacks and US strikes from 7 to 8 Jul, Houthi blockade of Saudi shipping from 20 Jul, MoU expired 17 Aug |

## Results 1: simple change vs 2025

| Group | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Jebel Ali + Khalifa, all calls | -90% | -77% | -81% |
| Other UAE Gulf ports, all calls | -54% | -36% | -40% |
| Fujairah + Khor Fakkan, all calls | -66% | -50% | -23% |
| Fujairah + Khor Fakkan, container calls | +253% | +550% | +1050% |
| Oman ports, all calls | -6% | +2% | +1% |
| Saudi Red Sea, all calls | +32% | +64% | -63% |
| Saudi Red Sea, volume | +84% | +140% | -64% |
| Pakistan, container cargo | +21% | +45% | +23% |
| Control ports, all calls | -2% | -3% | -5% |

Total calls at Fujairah and Khor Fakkan fell even as container calls rose, because Fujairah's tanker and bunkering traffic dropped sharply.

## Results 2: control-adjusted, with confidence intervals

For each port group and week, the expected 2026 value is the baseline value for the same ISO week scaled by the control ports' 2026/baseline ratio for that week. The effect is actual minus expected. Weekly effects are averaged within each phase, with Newey-West 95% intervals (3 lags). Weeks that straddle a phase boundary are left out, which leaves 7 pre-war weeks, 15 closure weeks, 3 MoU weeks and 17 renewed-disruption weeks. Code: `control_adjusted_effects()` in `src/analysis.py`.

Container cargo, thousand tonnes per day (95% CI in brackets):

| Group | Before the war (placebo) | Closure | Renewed disruption |
|---|---|---|---|
| Jebel Ali + Khalifa | +23 (-22 to +67) | -536 (-561 to -511) | -502 (-524 to -480) |
| Other UAE Gulf ports | 0 (-2 to +2) | -7 (-9 to -5) | -5 (-6 to -3) |
| Fujairah + Khor Fakkan | -3 (-3 to -2) | +16 (+8 to +24) | +32 (+28 to +35) |
| Oman ports | +24 (+8 to +41) | -9 (-27 to +10) | +26 (+3 to +49) |
| Saudi Red Sea | -17 (-33 to -2) | +16 (-10 to +43) | -94 (-128 to -59) |
| India (vs 2024) | +2 (-37 to +40) | +24 (-18 to +66) | +49 (+15 to +84) |
| Pakistan | 0 (-10 to +10) | +5 (-3 to +12) | +6 (+2 to +10) |
| Colombo | -5 (-13 to +3) | -3 (-10 to +4) | -9 (-13 to -5) |

Share of the UAE container cargo loss turning up elsewhere:

| | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Fujairah + Khor Fakkan | 3% | 5% | 6% |
| Fujairah + Khor Fakkan + Oman | 1% | -3% | 11% |
| India + Pakistan | 5% | 13% | 11% |
| All of the above plus Colombo | 6% | 9% | 20% |

Saudi Red Sea ports are left out of the shares because most of their change is crude oil, and they collapsed after July for a separate reason.

The pre-war column is a placebo test: before the war there should be no effect. Most groups pass. Oman does not (+24 before the war), so its later rise is hard to separate from a trend it already had.

Tables: `control_adjusted_effects_by_group.csv`, `control_adjusted_effects_by_group_vs2024.csv`, `control_adjusted_effects_by_port.csv`, `substitution_control_adjusted.csv`. Charts: `outputs/figures/control_adjusted_effects.png`, `outputs/figures/where_container_cargo_went.png`.

## Data gap at the Indian ports

PortWatch call counts at Mundra and Nhava Sheva drop sharply from about May 2025 to April 2026 (Nhava Sheva goes from about 27 calls a day to 7 or 8, then back to about 25 by May 2026), while Nhava Sheva's container tonnes stay steady. That looks like a data problem rather than real traffic, and it makes any comparison with 2025 overstate the 2026 rise. So India is compared with the same weeks of 2024 instead, and judged on container tonnes rather than calls. Its pre-war placebo against 2024 is close to zero. Monthly numbers are in `outputs/tables/south_asia_monthly_check.csv`.

## Khor Fakkan is probably undercounted

- PortWatch records about 0.2 container calls a day at Khor Fakkan in 2025 (about 77 a year), and no calls of any kind on 128 days.
- Lloyd's List puts Khorfakkan/Sharjah throughput at about 2.6 million TEU in 2025. Even if every one of those 77 calls matched the terminal's single-ship record of 19,561 TEU, that would only reach about 1.5 million TEU. So PortWatch is missing most of the container calls there.
- During the disruption Gulftainer, the operator, estimated it was handling 80 to 90% of UAE container demand, and reported weekly throughput rising from about 8 thousand to 65 thousand TEU. PortWatch shows only about 1 extra container call a day at Khor Fakkan.

The port boundary may be fine and the gap may come from vessels not transmitting AIS, so the Khor Fakkan numbers should not be relied on alone. Until this is resolved, the shares above are a lower bound for the UAE east coast.

## Caveats

- **AIS gaps.** PortWatch is built from AIS. Ships switching off transponders and GNSS jamming in the Gulf during the war would make the inside ports look emptier than they were.
- **Calls are not cargo.** Container tonnes help, but PortWatch estimates tonnes from ship type and draught, not from manifests.
- **Fujairah is mostly tankers and bunkering,** so its total calls say little about cargo moving there.
- **Land routes are invisible.** Cargo landed at Khor Fakkan, Fujairah or Sohar and trucked to Dubai shows up only at the port where it landed.
- **The control is small.** Three large ports far from the Gulf stand in for what would have happened without the war.
- **Some demand simply disappeared.** Not all lost cargo had to go somewhere else.
- **The MoU window is short** (3 full weeks), so its intervals are less reliable.

## Next steps

- Add more control ports (for example Shanghai, Antwerp, Los Angeles) and check the results hold.
- Check other transshipment hubs that could have taken Gulf cargo, such as Salalah's share by vessel size, Jeddah before July, and East African ports.
- Compare PortWatch with published monthly throughput for Jebel Ali, Khalifa and Khor Fakkan where available.

## How to run

```
py -m pip install -r requirements.txt
py src/fetch_portwatch.py      # optional, re-downloads the data
py src/analysis.py
```

## Sources for the phase dates

- War start and closure: Profit / Pakistan Today, 18 Apr 2026
- MoU and reopening: Majalla; S&P Global, 18 Jun 2026
- Renewed strikes: Al Jazeera, 8 Jul 2026
- Houthi blockade of Saudi shipping: Al Jazeera and AP, 20 Jul 2026
- MoU expiry: Al Jazeera, 17 Aug 2026
- Data: IMF PortWatch, portwatch.imf.org

## Sources for the Khor Fakkan check

- 2025 throughput: Lloyd's List One Hundred Ports, Khorfakkan/Sharjah entry
- Single-ship record of 19,561 TEU: Gulf News
- 80 to 90% of UAE container demand, and capacity expansion from 3.5 to 5 million TEU: AGBI, July 2026
- Weekly throughput 8 thousand to 65 thousand TEU: EnterpriseAM, Oct and Nov 2026
