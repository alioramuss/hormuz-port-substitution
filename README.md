# UAE ports inside and outside the Strait of Hormuz during the 2026 disruption

Did port traffic move from the UAE ports inside the strait (Jebel Ali, Khalifa) to ports outside it (Fujairah, Khor Fakkan, Oman, the Saudi Red Sea coast) when Hormuz was closed in 2026? This repo is a first pass at that question using IMF PortWatch daily port data.

Status: first pass, 21 Nov 2026. Numbers will change as the method gets tightened.

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

## First results

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

What this says so far:

1. **The inside ports collapsed and have not recovered.** Jebel Ali and Khalifa lost about 90% of their calls in the closure and are still about 80% down in the latest period.
2. **There is a container shift to the UAE east coast, but it is small.** Container calls at Fujairah and Khor Fakkan went from about 0.3 a day to about 2 a day. Against the roughly 20 container calls a day lost at UAE ports inside the strait, the east coast plus Oman made up about 2% of the loss in the closure, 6% in the MoU window and 10% since July. Total calls at the east coast still fell, because Fujairah's tanker and bunkering traffic dropped sharply.
3. **Oman barely moved.** Sohar fell, Salalah rose a little, and overall Oman stayed close to 2025.
4. **The Saudi Red Sea ports were the biggest outside winner until July.** Volume rose 84% in the closure, mostly crude loading at Yanbu (about 190 to 510 thousand tonnes a day), then collapsed after the Houthis declared a blockade of Saudi shipping on 20 July.
5. **The control ports are flat**, so none of this is a global shipping trend.

Tables are in `outputs/tables/`, charts in `outputs/figures/`.

## Caveats

- **AIS gaps.** PortWatch is built from AIS. Ships switching off transponders and GNSS jamming in the Gulf during the war would make the inside ports look emptier than they were. Reporting describes many "dark" transits.
- **Khor Fakkan looks undercounted.** PortWatch shows only about 1.1 calls a day there in 2025, with 128 days of zero calls, which seems low for a major container terminal. Worth checking how the port is defined in PortWatch before leaning on it.
- **Calls are not cargo.** A small feeder ship and a large mainline ship each count as one call, and feeder shuttles became more common during the disruption. Container tonnes would be a better measure of the shift.
- **Fujairah is mostly tankers and bunkering,** so its total calls say little about cargo moving there.
- **Land routes are invisible.** Cargo landed at Khor Fakkan, Fujairah or Sohar and trucked to Dubai shows up only at the port where it landed.
- **The baseline assumes 2025 was normal.**

## Next steps

- Check the Khor Fakkan definition in PortWatch.
- Use container tonnes (`import_container`, `export_container`) as well as calls.
- Weekly difference in differences against the control group, with confidence intervals.
- Check whether Indian west coast ports absorbed transshipment, since they are in the control group now.

## How to run

```
py -m pip install pandas matplotlib
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
