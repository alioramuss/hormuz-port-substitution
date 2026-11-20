# UAE ports inside and outside the Strait of Hormuz during the 2026 disruption

Did port traffic move from the UAE ports inside the strait (Jebel Ali, Khalifa) to ports outside it (Fujairah, Khor Fakkan, Oman, the Saudi Red Sea coast) when Hormuz was closed in 2026? This repo looks at that question using IMF PortWatch daily port data.

Status: second pass, 21 Nov 2026. Numbers will change as the method gets tightened.

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
| Control | Mundra, Nhava Sheva, Colombo, Karachi, Port Qasim, Singapore, Busan, Rotterdam |

Qalhat LNG terminal is pulled but left out, since LNG exports are not a substitution route.

## Phases

Each 2026 phase is compared with the same calendar dates in 2025.

| Phase | Dates | What happened |
|---|---|---|
| Before the war | 1 Jan to 27 Feb | Normal traffic |
| Closure | 1 Mar to 14 Jun | US and Israeli strikes on Iran on 28 Feb, strait effectively closed |
| MoU window | 15 Jun to 7 Jul | US and Iran MoU agreed 15 Jun and signed 17 Jun, traffic partly returns |
| Renewed disruption | 8 Jul to 13 Nov | Tanker attacks and US strikes from 7 to 8 Jul, Houthi blockade of Saudi shipping from 20 Jul, MoU expired 17 Aug |

## Headline

PortWatch shows a small but clear container shift from the UAE ports inside the strait to the east coast: since July, about 2 extra container calls and about 32 thousand tonnes of container cargo a day at Fujairah and Khor Fakkan, against roughly 520 thousand tonnes a day lost at UAE ports inside. That is about 6% of the lost container cargo (10% counting Oman).

But PortWatch looks to be missing most of Khor Fakkan's traffic (see below), and the terminal operator says it handled 80 to 90% of UAE container demand during the disruption. So the real shift is probably much bigger than PortWatch shows, and sorting out that gap is now the main question.

## Results 1: simple change vs 2025

Change versus the same dates in 2025:

| Group | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Jebel Ali + Khalifa, all calls | -90% | -77% | -81% |
| Other UAE Gulf ports, all calls | -54% | -36% | -40% |
| Fujairah + Khor Fakkan, all calls | -66% | -50% | -23% |
| Fujairah + Khor Fakkan, container calls | +253% | +550% | +1050% |
| Oman ports, all calls | -6% | +2% | +1% |
| Saudi Red Sea, all calls | +32% | +64% | -63% |
| Saudi Red Sea, volume | +84% | +140% | -64% |
| Control ports, all calls | -4% | +1% | +2% |

1. **The inside ports collapsed and have not recovered.** Jebel Ali and Khalifa lost about 90% of their calls in the closure and are still about 80% down in the latest period.
2. **Container traffic grew at the UAE east coast**, from about 0.3 to about 2 container calls a day. Total calls there still fell, because Fujairah's tanker and bunkering traffic dropped sharply.
3. **Oman barely moved.** Sohar fell, Salalah rose a little.
4. **The Saudi Red Sea ports were the biggest outside winner until July.** Volume rose 84% in the closure, mostly crude loading at Yanbu (about 190 to 510 thousand tonnes a day), then collapsed after the Houthis declared a blockade of Saudi shipping on 20 July.
5. **The control ports are flat**, so none of this is a global shipping trend.

## Results 2: control-adjusted, with confidence intervals

For each port group and week, the expected 2026 value is the 2025 value for the same ISO week scaled by the control ports' 2026/2025 ratio for that week. The effect is actual minus expected. Weekly effects are averaged within each phase, with Newey-West 95% intervals (3 lags). Weeks that straddle a phase boundary are left out, which leaves 7 pre-war weeks, 15 closure weeks, 3 MoU weeks and 17 renewed-disruption weeks. Code: `control_adjusted_effects()` in `src/analysis.py`.

Container cargo, thousand tonnes per day (95% CI in brackets):

| Group | Closure | Renewed disruption |
|---|---|---|
| Jebel Ali + Khalifa | -541 (-566 to -515) | -516 (-543 to -490) |
| Other UAE Gulf ports | -7 (-9 to -5) | -5 (-7 to -3) |
| Fujairah + Khor Fakkan | +16 (+8 to +24) | +32 (+28 to +35) |
| Oman ports | -10 (-27 to +7) | +22 (0 to +45) |
| Saudi Red Sea | +15 (-10 to +40) | -97 (-132 to -61) |

Share of the UAE container loss turning up outside the strait:

| | Closure | MoU window | Renewed disruption |
|---|---|---|---|
| Fujairah + Khor Fakkan, by container calls | 4% | 7% | 9% |
| Fujairah + Khor Fakkan, by container tonnes | 3% | 5% | 6% |
| Plus Oman, by container tonnes | 1% | -4% | 10% |

The pre-war weeks act as a placebo test. Effects there are small next to the war effects (for example +8% for Jebel Ali and Khalifa calls against -90% in the closure), though a few are statistically different from zero, so the 2025 baseline is not perfect.

Tables: `control_adjusted_effects_by_group.csv`, `control_adjusted_effects_by_port.csv`, `substitution_control_adjusted.csv`. Chart: `outputs/figures/control_adjusted_effects.png`.

## Khor Fakkan is probably undercounted

- PortWatch records about 0.2 container calls a day at Khor Fakkan in 2025 (about 77 a year), and no calls of any kind on 128 days.
- Lloyd's List puts Khorfakkan/Sharjah throughput at about 2.6 million TEU in 2025. Even if every one of those 77 calls matched the terminal's single-ship record of 19,561 TEU, that would only reach about 1.5 million TEU. So PortWatch is missing most of the container calls there.
- During the disruption Gulftainer, the operator, estimated it was handling 80 to 90% of UAE container demand, and reported weekly throughput rising from about 8 thousand to 65 thousand TEU. PortWatch shows only about 1 extra container call a day at Khor Fakkan.

Possible reasons: the port boundary in PortWatch may not cover the container berths, or calls there may be assigned to another port or dropped. This needs checking with the PortWatch team before the Khor Fakkan numbers can be trusted. Until then, the substitution shares above are a lower bound.

## Caveats

- **AIS gaps.** PortWatch is built from AIS. Ships switching off transponders and GNSS jamming in the Gulf during the war would make the inside ports look emptier than they were. Reporting describes many "dark" transits.
- **Calls are not cargo.** Container tonnes help, but PortWatch estimates tonnes from ship type and draught, not from manifests.
- **Fujairah is mostly tankers and bunkering,** so its total calls say little about cargo moving there.
- **Land routes are invisible.** Cargo landed at Khor Fakkan, Fujairah or Sohar and trucked to Dubai shows up only at the port where it landed.
- **The baseline assumes 2025 was normal,** and the control ports are only a rough stand-in for what would have happened without the war.
- **The MoU window is short** (3 full weeks), so its intervals are less reliable.

## Next steps

- Ask the PortWatch team how Khor Fakkan is defined, and whether calls there are being missed.
- Compare PortWatch with published monthly throughput for Jebel Ali, Khalifa and Khor Fakkan where available.
- Check whether Indian west coast ports absorbed transshipment, since they are in the control group now.

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
- 80 to 90% of UAE container demand: AGBI, July 2026
- Weekly throughput 8 thousand to 65 thousand TEU: EnterpriseAM, Oct and Nov 2026
