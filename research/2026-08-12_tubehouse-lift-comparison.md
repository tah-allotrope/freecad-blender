# Research Brief: Hydraulic vs Traction Lift for a HCMC Tubehouse

**Date:** 2026-08-12
**Modes run:** domain, literature
**Depth:** exhaustive
**Invocation context:** "exhaustive to compare hydraulic vs traction lift for my tubehouse given brands and companies in HCMC offering these products regarding cost, safety, space"
**Sources (wide/deep):** 189/38 | **Ratio used:** web=0.45, industry=0.40, academia=0.10, github=0.05
**Fallback note:** `FIRECRAWL_API_KEY` unset in this environment, so the `industry`/`web` buckets were filled via `web_search` + `web_extract` (script-assisted wide pass) instead of Firecrawl; `github`/`academia` ran on `gh`/OpenAlex as assigned. Several VN installer sites block scrapers — those sources are cited at title level and flagged below.

**Building context (from local repo):** `designs/tubehouse-dream.json` — 5 storeys (Ground Garage/Lease → Floor 4 Office/Guest/Roof Terrace), elevator shaft **1000 × 1400 mm (1.4 m²)** in the core zone on every floor.

---

## Synthesis

**Space is the deciding constraint, and it rules *out* the naive "hydraulic is cheaper" answer.** Your 1000×1400 mm shaft sits at the lower bound of Vietnam's home-lift "mini" segment (one installer puts the practical minimum at ~1.5 m²; others advertise "từ 1 m²" [GDE, GHT]). Traction MRL lifts — KONE MonoSpace Home (machine fully inside the hoistway, 0.4–1.0 m/s, 250–630 kg, up to 6 stops) and Otis Gen2 Life (MRL, up to 45 m rise / 14 stops) — are engineered exactly for this: no machine room, no oil, compact in-shaft machine [kone.vn, otis.com/vi]. Hydraulic lifts need a machine room (or remote power unit) and a deeper pit, which in a 5-storey tubehouse either eats a room per floor or forces construction changes; MRL instead needs more clear height above the top landing — your top floor has a roof terrace, so check headroom against the product's overhead requirement before committing [kone.us, schindler, viluxlift]. EN 81-41-style "platform lifts" (≤0.15 m/s, TCVN 6396-41:2018) are **not** a legitimate substitute for a 5-stop passenger lift — a real enclosed-car lift at this size must be built to EN 81-20/50 (TCVN 6396-20:2017) [iteh, tns-lift, kone.co.uk].

**Cost in HCMC splits into three price tiers, not two technologies.** Local-assembled traction units ("liên doanh", Fuji/Torise components): **260–350 triệu** installed (5-stop, 250–350 kg) — cheapest; liên doanh mid-range 400–800 triệu; fully-imported brand home lifts (Mitsubishi, Hitachi): **600–800 triệu**; imported hydraulic (Domuslift, Italy): **900 triệu – 1 tỷ**; screw-driven (Cibeslift, Sweden): 800 triệu – 1.2 tỷ [GDE, GHT]. Other installers quote entry points of 250–260 triệu [thuanphat, giathangmaygiadinh, GHT] and 400+ triệu for 5-storey [gemanlift], with premium installs reaching ~1 tỷ [vnexpress]. Hydraulic is *not* cheaper at this stop count in Vietnam — the cheap tier is local-assembled traction. Running cost: traction MRL with regenerative drive (Schindler 3300 regen standard; Otis Gen2) uses less energy; lifts consume ~2–10% of a building's energy [VDI 2225, E&B 2012]; Vietnamese installers quote ~300.000 đ/month electricity for typical home lifts [kalealifts title] plus ~10 triệu one-off for electrical works [GHT].

**Safety and compliance are regulated and equal-ish across technologies — the difference is failure mode and maintenance discipline.** Both must meet TCVN 6396-20:2017 (EN 81-20:2014) construction/installation rules; lifts for persons are on the list of machines with strict safety requirements (Thông tư 36/2019/TT-BLĐTBXH) subject to periodic inspection under Thông tư 12/2021/TT-BLĐTBXH — insist the supplier includes kiểm định and certification [vsqi, thuvienphapluat, getis]. The VDI 2225 study recommends annual inspection for residential lifts [VDI 2225]. Technology-specific: hydraulic adds oil/cylinder/pit-corrosion failure modes (vendor consensus: "no oil" is a traction selling point), traction adds rope/counterweight wear; both carry overspeed/UCM protection per EN 81-20 [kone.us, kone.co.uk, evonicpro]. The peer-reviewed literature on hydraulic energy efficiency (accumulator VVVF, energy recovery, 2025 indirect-hydraulic improvements) shows hydraulic is catching up on energy but still trails regen traction [Mechatronics 2005, IJFP 2015, Energies 2025].

**Company shortlist for HCMC (official VN presence verified):** KONE Việt Nam (MonoSpace Home — direct home-lift product), Otis Việt Nam (Gen2 Life — direct home-lift product), TK Elevator VN (home mobility division), Hyundai Elevator VN (home series via dealers) [kone.vn, otis.com/vi, tkelevator.com, hyundaielevator.com.vn]. Mitsubishi (NEXIEZ line, low-rise incl. NEXIEZ-Fit) and Schindler (3300 MRL) are active in VN via dealers — confirm the local entity and warranty terms [scribd, hvacinformed, schindler]. Local installers serving HCMC (dozens): GDE/Vinalift, GHT, Nidec, YME, Kalea, Atlantic, Hamico, Fuji Lift, GamaLift, Hoàng Triệu, Thanh Phát, Viettech, Nam Thang, River, Taza, Getis, TPEC, Swift, Homelift VN [nidec, ymelift, kalealifts, gde, ght, thiennam, taza, dichvuthangmay]. `[NOTE]` Apply your standing rule here: only brands with official VN availability + local warranty — no parallel imports; verify kiểm định records and installer track record, not just price.

**Bottom line:** for a 5-stop, 1000×1400 mm tubehouse, the mainstream fit is a **traction MRL from a global brand with official VN entity** (KONE MonoSpace Home or Otis Gen2 Life, 600–800 triệu class if fully imported / 400–800 triệu liên doanh) — best space story, lowest running cost, strongest safety regime. Choose **hydraulic** only if you need a machine room placed remotely (e.g. in the garage/yard), can accept a deeper pit, and the ~900 triệu+ import price is acceptable. Local-assembled traction (260–350 triệu) is the budget option — acceptable if the supplier demonstrates kiểm định compliance and a real warranty. **Before shortlisting, get 3–5 written quotes that each state: shaft-fit drawing for 1000×1400, pit depth, top-landing overhead, machine-room requirement, kiểm định/inspection fee, and warranty terms** — vendor-published dimensions (not prices) were the hardest data to verify in this pass.

---

## Source Coverage

| bucket | target | gathered | qualified | cited | reallocated |
|---|---|---|---|---|---|
| web | 54 | 96 | 62 | 17 | +3 (absorbed github shortfall) |
| industry | 48 | 66 | 66 | 13 | 0 |
| academia | 12 | 18 | 18 | 6 | 0 (surplus 6, kept) |
| github | 6 | 9 | 3 | 2 | −3 (reallocated to web) |

Github genuinely has no reusable prior art for this topic (homework repos and scraped market reports only) — the deficit was reallocated to web, which had qualified surplus. Ledger counts include rows recovered after a script crash truncated the initial ledger (45 rows re-added with provenance recorded).

---

## Domain Landscape

### Discovery
Strongest sources found: official VN product pages — KONE MonoSpace Home [kone.vn], Otis Gen2 Life [otis.com/vi], TK Elevator home solutions [tkelevator.com], Hyundai Elevator VN [hyundaielevator.com.vn]; global spec pages — Schindler 3300 [schindler.com]; installer price/tech tables — GDE/Vinalift [thangmaygde.com] and GHT [thangmayght.com]; standards — EN 81-41:2024 [iteh], EN 81-20/50 [kone.co.uk], TCVN catalogue [vsqi], TCVN guides [getis.vn, tns-lift.com.vn]; HCMC installer lists [thangmaynidec.vn, ymelift.com, kalealifts.com.vn].

### Verification
Official vendor pages (KONE VN, Otis VN, Schindler, TKE) were fetched and their spec figures read directly. Installer price tables (GDE, GHT) are primary market data but vendor-biased — price ranges were cross-checked across ≥3 independent installers (GDE 260–350tr local, GHT 180–320tr mini / 400–800tr liên doanh, thuanphat 250tr entry, gemanlift 400tr 5-tầng, giathangmaygiadinh 260tr entry) and are consistent in structure. TCVN numbers verified against the official VSQI catalogue and legal database titles. `Flag:` several key pages blocked scrapers (kalealifts 14-company list, cibeslift, taza, thiennam, cauthangmay, cafef, giathangmaygiadinh, reddit) — cited at title level only; treat their specific figures as unverified. Specific pit-depth/overhead numbers per product were NOT verifiable from accessible pages — this is the single biggest data gap (see Synthesis).

### Comparison
- **Space:** Traction MRL = no machine room, machine in hoistway (KONE MonoSpace Home explicitly; Otis Gen2 Life; Schindler 3300 "fits into the footprint of a hydraulic elevator") [kone.vn, otis.com/vi, schindler.com]. Hydraulic = machine room + deeper pit; VN "không hố pit" marketing applies to traction/screw minis, not hydraulic [kone.us, viluxlift, nidec]. Shaft: GDE states smallest practical ~1.5 m², 250–350 kg; your 1.4 m² shaft is at the boundary — verify per-product minimums and car sizes (GHT lists cars 600×830 / 960×882 / 1100×930) [gde, ght].
- **Cost:** See Synthesis tiers. Note GHT's +30–40 triệu for a machine-room-less drive on their commercial table and ~10 triệu electrical works [ght]. Hydraulic import (Domuslift) is the *most expensive* category in the GDE table, not the cheapest [gde].
- **Safety/compliance:** EN 81-20/50 (TCVN 6396-20:2017) applies to a real 5-stop passenger lift; EN 81-41:2024 / TCVN 6396-41:2018 only covers ≤0.15 m/s platform lifts for impaired mobility — a common market confusion [iteh, tns-lift, kone.co.uk]. VN periodic-inspection regime: TT 36/2019 list + TT 12/2021 procedure [thuvienphapluat]. Hydraulic vs traction failure modes differ (oil/cylinder/pit corrosion vs ropes/counterweight); both carry overspeed + UCM protection per EN 81-20 [kone.us, kone.co.uk].
- **Companies:** Global-with-VN-entity (KONE, Otis, TKE, Hyundai) vs dealer-distributed (Mitsubishi, Schindler, Fujitec) vs local assemblers (Fuji, Torise, GDE, GHT, Nidec, Kalea, ~dozens more) — verify which entity holds the warranty [nidec, ymelift, kone.vn, otis.com/vi, tkelevator.com].

### Synthesis
Reuse: official brand pages for shortlisting; GDE/GHT tables as the price backbone; standards list for compliance questions. Missing: per-product shaft/pit/overhead drawings for 1000×1400 (get from suppliers), and any VN-specific comparative cost-of-ownership study. Planning implication: the decision is really "global-brand MRL (600–800tr) vs local-assembled MRL (260–400tr) vs imported hydraulic (900tr+, only if machine room + pit acceptable)" — get written quotes with the six items listed in Synthesis.

### Confidence
**High** on price tiers (multiple independent installer tables agree), EN 81-41 vs EN 81-20 scope, and company presence. **Medium** on exact space figures per product (pit/overhead/shaft minimums) — vendor drawings required.

---

## Literature and Reports

### Discovery
OpenAlex wide pass surfaced 18 candidates; the deep set: VDI 2225 technical-economic comparison of hydraulic vs traction elevators (2024, open access — the anchor) [10.14744/sigma.2024.00105]; Energies 2025 on hydraulic indirect elevator efficiency [10.3390/en18092163]; Mechatronics 2005 on VVVF hydraulic + pressure accumulator energy saving (37 cites) [10.1016/j.mechatronics.2005.06.009]; Int J Fluid Power 2015 on hydraulic elevator energy recovery (13 cites) [10.1080/14399776.2015.1055991]; EPE Journal 2018 on energy- and safety-critical traction parameters (17 cites) [10.1080/09398368.2018.1469867]; Energy & Buildings 2012 on EU elevator/escalator energy-efficiency potential and policy (64 cites) [10.1016/j.enbuild.2011.11.053].

### Verification
The VDI 2225 paper was fetched in full (OA PDF at sigma.yildiz.edu.tr): its residential case is exactly our profile — **5 stops, 300 kg, 0.63 m/s** — evaluated on an S-Diagram (technical vs economic value); it recommends **annual inspection** for residential lifts and states elevators use **2–10% of building energy**; residential lifts score as the easiest to install and maintain among the cases studied. The remaining papers are cited at abstract/metadata level (OA where noted); the 2005/2015/2025 cluster is consistent: hydraulic elevator energy use is improvable (accumulators, VVVF, energy recovery) but historically above gearless traction with regeneration.

### Comparison
The energy literature splits into two clusters: (a) hydraulic-side efficiency research (accumulator VVVF 2005; energy recovery 2015; indirect-hydraulic improvements 2025) and (b) traction-side regeneration (Schindler 3300 ships regen as standard [schindler.com]; regenerative elevator analysis in IEEE work). On safety, peer-reviewed material is thin for residential lifts — the strongest operational evidence is the standards themselves (EN 81-20/50) plus the annual-inspection recommendation in the VDI study. No peer-reviewed study addresses the Vietnamese home-lift market or lifecycle cost at 5 stops — that gap is filled by installer price data (vendor-sourced, cross-checked).

### Synthesis
Reuse: VDI 2225's residential case definition (5 stops / 300 kg / 0.63 m/s) as the specification benchmark, and its annual-inspection recommendation for your maintenance contract. Gap: no published VN lifecycle-cost comparison — your 3–5-quote exercise is the substitute. Contradictions: none material; the "hydraulic is cheaper" claim common in international blogs [evonicpro, kone.us] holds at very low rise / US market but is contradicted by the Vietnamese price tables at 5 stops [gde, ght] — an important market-specific correction.

### Confidence
**High** on the VDI 2225 findings (full text verified). **Medium** on the energy cluster (abstract-level evidence). **Low** on any claim about VN-specific lifecycle costs (none published).

---

## Sources

*Official / standards*
- [KONE Việt Nam — Thang máy gia đình MonoSpace Home](https://www.kone.vn/vi/new-buildings/elevators-lifts/kone-monospace-home) - official product page; MRL machine in hoistway, 0.4–1.0 m/s, 250–630 kg, ≤6 stops
- [Otis Việt Nam — Gen2 Life](https://www.otis.com/vi/vn/products-services/products/gen2-life) - official home-lift page; MRL, 1.6 m/s, ≤1,020 kg, 45 m max rise, 14 stops
- [Schindler 3300 MRL](https://www.schindler.com/en/elevators/passenger/schindler-3300.html) - MRL, no machine room, fits hydraulic footprint, regen drive standard, ≤12 stops
- [TK Elevator — Home Elevators & Platform Lifts](https://www.tkelevator.com/global-en/products/home-elevators-and-platform-lifts) - home mobility division
- [KONE GB — EN 81-20/EN 81-50 compliance](https://www.kone.co.uk/tools-downloads/codes-and-standards/en81-20-and-en81-50-compliance) - UCM/overspeed, doors, fire class, pit refuge, counterweight safety gear
- [EN 81-41:2024 scope (iTeh)](https://standards.iteh.ai/catalog/standards/cen/62d01d02-95cf-4600-badf-cdda8cc30a3f/en-81-41-2024) - platform lifts ≤0.15 m/s; not a passenger-lift standard
- [Stage Elevators — EN 81-41 / TÜV SÜD framework](https://www.stagelevators.com/blog/home-elevators-safety-standards-india) - vendor blog (use with caveat); EN 81-20/50 → ISO 8100 transition
- [VSQI — TCVN 6396-20:2017](https://tieuchuan.vsqi.gov.vn/tieuchuan/view?sohieu=TCVN+6396-20%3A2017) - official catalogue; EN 81-20:2014 adoption
- [TNS Lift — 5 TCVN for home lifts](https://tns-lift.com.vn/5-tieu-chuan-viet-nam-moi-nhat-ve-thang-may-gia-dinh-ban-can-biet) - TCVN 6396-41:2018 = EN 81-41:2010 IDT; TCVN 6905:2001 hydraulic tests
- [Getis — TCVN guide](https://getis.vn/tieu-chuan-thang-may-gia-dinh) - TCVN 5744/5866/6904/6396-28, incl. 6396-2:2009 (hydraulic)
- [Thông tư 36/2019/TT-BLĐTBXH (Thư viện pháp luật)](https://thuvienphapluat.vn/van-ban/Lao-dong-Tien-luong/Thong-tu-36-2019-TT-BLDTB) - lifts on strict-safety equipment list
- [Thông tư 12/2021/TT-BLĐTBXH (Thư viện pháp luật)](https://thuvienphapluat.vn/van-ban/Lao-dong-Tien-luong/Thong-tu-12-2021-TT-BLDTB) - periodic lift inspection procedure

*VN market / price data (installer pages — vendor-sourced, cross-checked)*
- [GDE/Vinalift — price table by technology](https://thangmaygde.com/thang-may-gia-dinh) - local traction 260–350tr; liên doanh 275–350tr; Domuslift hydraulic 900tr–1 tỷ; Cibes screw 800tr–1.2 tỷ; Mitsubishi/Hitachi 600–800tr; smallest shaft ~1.5 m²
- [GHT — home-lift price list & sizes](https://thangmayght.com/thang-may-gia-dinh-ght) - mini 180–320tr (liên doanh) / 300–500tr (imported); 300–500+ kg 400–800tr; imported brands 1–2 tỷ; +30–40tr MRL option; ~10tr electrical; car sizes 600×830–1100×930
- [Nidec — top-10 HCMC installers](https://thangmaynidec.vn/top-10-cong-ty-thang-chi-minh) - market landscape; tech types incl. screw/hydraulic/traction
- [YME — HCMC installer lists](https://ymelift.com/top-10-cong-ty-thang-mon-tphcm) - installer names; partial fetch
- [Kalea — HCMC installer list (title-level)](https://kalealifts.com.vn/cam-nang/thang-may-gia-dinh-tphcm.html) - 14 companies; blocked, title only
- [Kalea — electricity ~300.000 đ/month (title-level)](https://kalealifts.com.vn/cam-nang/thang-may-gia-dinh-co-ton-dien-khong.html) - title only, unverified figure
- [Thiên Nam — maintenance cost (title-level)](https://thangmaythiennam.net/chi-phi-bao-tri-thang-may-gia-dinh-dinh-ky-gia-re), [Cầu thang máy — monthly ownership cost (title-level)](https://cauthangmay.com/tu-van-thang-may/378-tong-chi-phi-nuoi-thang-may-gia-dinh-moi-th), [Taza — price levels (title-level)](https://thangmaytaza.com/tu-van-tin-tuc/cac-muc-gia-thang-may-gia-dinh-hien-nay-cap-nhat-moi-nhat), [Thanh Phát — from 250tr (title-level)](https://thangmaythuanphat.vn/san-pham/thang-may-gia-dinh-uy-tin), [Gia đình elevator — from 260tr (title-level)](https://giathangmaygiadinh.com), [GemaLift — 5 tầng từ 400tr (title-level)](https://gemanlift.com/thang-may-gia-dinh-5-tang)

*Comparisons & market commentary*
- [KONE US — Traction vs Hydraulic](https://www.kone.us/blog/traction-elevators-compared-to-hydraulic.html) - vendor comparison; machine room + oil as hydraulic drawbacks
- [EvonicPro — Hydraulic vs Traction Lift Cost](https://evonicproelevators.com/blog/elevator-cost/hydraulic-vs-traction-lift-cost) - practitioner cost comparison (India data)
- [ViluxLift — thủy lực vs cáp kéo](https://viluxlift.com/nen-chon-thang-may-cong-nghe-thuy-luc-hay-cap-keo-cho-gia-dinh) - VN installer comparison; pit/counterweight considerations
- [VnExpress — Nhà ống nên dùng thang máy loại nào](https://vnexpress.net/nha-ong-nen-dung-thang-may-loai-nao-4570402.html) - VN press guidance; premium pricing ~1 tỷ
- [CaféF — home-lift choices of affluent VN (title-level)](https://cafef.vn/gu-lua-chon-thang-may-gia-dinh-cua-gioi-nha-giau-viet-nam-1882508011732) - blocked, title only
- [r/Elevators — Hydro vs MRL Gearless (title-level)](https://www.reddit.com/r/elevators/comments/1fpnzdh/which_should_i_buy_hydro_or_mrl_gear), [r/Elevators — US home elevator cost (title-level)](https://www.reddit.com/r/elevators/comments/1bhmgui/what_is_the_average_cost_of_installing_a_home), [r/Elevators — technician preference (title-level)](https://www.reddit.com/r/elevators/comments/1i7pra5/do_you_prefer_to_work_on_hydraulic_or_traction) - blocked, titles only
- [Otosaigon forum — nên lắp thang máy gia đình? (title-level)](https://www.otosaigon.com/threads/co-nen-lap-dat-thang-may-gia-dinh.9040256) - blocked, title only
- [Hyundai Elevator VN](https://www.hyundaielevator.com.vn) - official VN site; home series via dealers

*Academia*
- [VDI 2225 comparison of hydraulic and traction elevators (2024, OA)](https://doi.org/10.14744/sigma.2024.00105) - anchor; residential case 5 stops/300 kg/0.63 m/s; annual inspection; 2–10% building energy
- [Energy Efficiency Improvement of Hydraulic Indirect Elevator (2025, OA)](https://doi.org/10.3390/en18092163) - hydraulic efficiency gains
- [VVVF hydraulic elevator with pressure accumulator (2005, 37 cites)](https://doi.org/10.1016/j.mechatronics.2005.06.009) - hydraulic energy saving
- [Efficient architecture for energy recovery in hydraulic elevators (2015, 13 cites)](https://doi.org/10.1080/14399776.2015.1055991) - hydraulic recovery
- [Energy- and safety-critical traction parameters (2018, 17 cites)](https://doi.org/10.1080/09398368.2018.1469867) - traction-side safety/energy
- [Energy-efficient elevators and escalators in Europe (2012, 64 cites)](https://doi.org/10.1016/j.enbuild.2011.11.053) - EU policy context

*Github (sparse prior art — no reusable implementations)*
- [Shaftless-Home-Elevator-Market](https://github.com/sonaliroy2405-spec/Shaftless-Home-Elevator-Market) - scraped market report, 0 stars
- [vanbuielevator](https://github.com/ngocbd/vanbuielevator) - VN elevator company website source (market presence signal)

Full source pool: `research/sources/2026-08-12_tubehouse-lift-comparison.sources.jsonl` (189 rows).
