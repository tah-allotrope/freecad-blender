---
title: "Apartment Sale Execution Pack — Fund the Tubehouse Build"
date: "2026-08-29"
status: "draft"
request: "Turn the SSR apartment-sale brainstorm into an executable plan, with the unit confirmed as river-view and the tubehouse finish confirmed as medium; produce an HTML report and commit/push at the end."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-29_sell-apartment-fund-tubehouse-brainstorm.md"
  - "research/2026-07-06_tubehouse-dream-home-brainstorm.md"
---

# Plan: Apartment Sale Execution Pack — Fund the Tubehouse Build

## Objective

Produce a complete, self-contained **sale execution pack** that lets the owner sell a
72 m2 river-view 2-bedroom apartment at Saigon South Residences (Nguyen Huu Tho, Phuoc Kien,
Nha Be, Ho Chi Minh City) within 60–90 days at or above a defined price floor, and reconcile
the net proceeds against the cost of building the already-designed 4 m x 25 m, 5-storey
tubehouse to a medium finish standard. The tubehouse design is complete and the land is already
owned; capital release is the only remaining blocker.

All monetary amounts in this plan are **Vietnamese Dong (VND)**. The abbreviation `ty` means
10^9 VND (one billion). The abbreviation `tr` means 10^6 VND (one million). `tr/m2` means
millions of VND per square metre. Never mix these units; every number written into a
deliverable must carry its unit explicitly.

## Context Snapshot

- **Current state:** The repository contains a finished tubehouse design (JSON spec, 2D plans,
  elevations, sections, Blender renders, GLB viewers, architect-brief PDF, contractor drawing
  set). It contains **no** financial, disposal, or sale material of any kind. The apartment is
  unlisted, empty, fully furnished, held with a So hong (freehold pink book) and carries no
  mortgage. The tubehouse land is already owned. No contractor is engaged.
- **Desired state:** A new directory `deliverables/apartment-sale/` holds nine documents that
  together constitute a runnable sale process: a dated comparable-price fact base, an
  agent-vetting scorecard and call script, a broker mandate terms sheet, Vietnamese and English
  listing copy, a photography shot list, a negotiation ladder, a closing and tax checklist, and
  a proceeds-to-build reconciliation. A tested Python module computes the sale waterfall. A
  styled HTML report summarises the pack. All of it is committed and pushed to `origin/master`.
- **Key repo surfaces:** `deliverables/` (existing directory holding published design outputs;
  this plan adds a sibling subdirectory), `reports/` (existing directory of dated HTML reports —
  match their house style), `scripts/` (existing utility scripts), `tests/` (pytest suite),
  `research/2026-08-29_sell-apartment-fund-tubehouse-brainstorm.md` (the source brief),
  `pyproject.toml`, `ruff.toml`, `AGENTS.md`.
- **Out of scope:** Any change to the tubehouse design, spec files under `designs/` or `spec/`,
  the rendering pipeline, or anything under `src/homedesign/`. Contractor selection and
  construction management. Mortgage or bridge-financing structures. Any scheme involving
  under-declaring the contract value to reduce transfer tax. Actually contacting agents,
  publishing listings, or transacting — this plan produces the pack; a human executes the sale.

## Environment & Conventions

- **Stack:** Python >= 3.11, packaged with setuptools, source layout under `src/`. Package name
  `homedesign`. Test framework pytest >= 8.0. Linter/formatter ruff, pinned at `0.15.7`, with
  `line-length = 120` configured in `ruff.toml`.
- **Setup:** `python -m pip install -e ".[dev]"`
- **Build / Run:** This plan adds no build step. The one new executable module is run with
  `python scripts/sale_waterfall.py --help`.
- **Test:** Full suite — `python -m pytest`. Single test file — `python -m pytest tests/test_sale_waterfall.py -v`.
  Single test case — `python -m pytest tests/test_sale_waterfall.py::test_net_proceeds_at_floor_price -v`.
  `pyproject.toml` sets `testpaths = ["tests"]` and `pythonpath = ["src"]`, so tests run from the
  repository root without extra path configuration. The suite currently contains 226 passing
  tests; this plan must leave all of them passing and add new ones.
- **Lint:** `python -m ruff check .` and `python -m ruff format --check .` must both pass.
- **Conventions & traps:**
  - Test files live in `tests/` and are named `test_<subject>.py`. Test functions are named
    `test_<behaviour_being_asserted>`. Follow the existing style in `tests/test_compiler.py`.
  - Currency: all VND. Write amounts in deliverables as e.g. `5.95 ty` or `110 tr`, never bare
    numbers. In Python code, represent all amounts as **integers in plain VND** (so 5.95 ty is
    `5_950_000_000`) to avoid floating-point drift on tax and commission arithmetic; convert to
    `ty` only at the presentation layer.
  - Dates: ISO `YYYY-MM-DD`. Timezone for any "as of" stamp is `Asia/Ho_Chi_Minh` (UTC+7).
  - Markdown deliverables use ASCII only for Vietnamese proper nouns in filenames and headings
    (e.g. `Nha Be`, not `Nhà Bè`) to match the repo's existing filename conventions. Vietnamese
    diacritics ARE required inside the body of the Vietnamese listing copy — that document is
    customer-facing.
  - Do not hand-edit anything under `output/`; those are reproducible artifacts.
- **Repo map:**
  ```
  deliverables/          published design outputs (contractor-as-drawn/, tubehouse-dream/); ADD apartment-sale/ here
  reports/               dated HTML reports, e.g. 2026-08-15-final-drawing-truth-and-construction-set.html
  research/              markdown research briefs and brainstorms
  plans/                 markdown plans (this file)
  scripts/               standalone utilities (regen_viewer.py, sync_skill.py); ADD sale_waterfall.py here
  tests/                 pytest suite, 226 tests
  src/homedesign/        the design pipeline — DO NOT TOUCH in this plan
  designs/, spec/        home specs and schema — DO NOT TOUCH in this plan
  ```

## Research Inputs

- From `research/2026-08-29_sell-apartment-fund-tubehouse-brainstorm.md`:
  - Comparable asking prices at Saigon South Residences split into two tiers as of August 2026.
    Aggregator "reference" tables (angialand.com.vn, phuloiland.vn) show 71 m2 at 5.0–5.1 ty,
    75 m2 at 5.2–5.5 ty, 76 m2 at 5.6 ty. **Live dated listings** (housenow.com.vn, posted
    06–27 August 2026) show 71 m2 at 5.65–5.95 ty (79–84 tr/m2), 75 m2 at 5.70–6.00 ty
    (76–80 tr/m2), 76 m2 at 5.50 ty (72 tr/m2). The aggregator tables lag the live market by
    roughly 0.5 ty and must not be used as the pricing anchor.
  - The single highest live asking price observed, 5.95 ty for a 71 m2 unit at 83.8 tr/m2, is
    explicitly a **river-view** unit. The subject apartment is confirmed river-view, so it
    prices against that comparable rather than the standard-outlook band.
  - Several portals (notably nhadat.cafeland.vn) list 71–75 m2 units at 2.3–3.6 ty. These are
    bait listings or quotes of the remaining balance on an unfinished purchase contract (HDMB),
    not full freehold transfer prices. The subject unit has an issued So hong and transfers
    freehold, so those entries are not comparables.
  - Transfer tax is **2% of gross contract value, final** — assessed on the sale price, not on
    the gain, and not reducible by documenting the original purchase price.
  - Broker commission has **no legal cap in Vietnam**. Primary/developer sales run 2–3%;
    secondary resale apartments run 1–2%, seller-paid. A mandate priced at 1% is shown after
    the 2% listings on the same agent's book.
  - Market conditions in Q3 2026 are divergent: asking prices are firm to rising while
    transaction liquidity is falling (one source reports secondary prices +2% quarter-on-quarter,
    another reports secondary down 2–6% quarter-on-quarter with liquidity notably reduced,
    driven by leveraged sellers exiting). The practical consequence is a wider-than-normal
    discount from asking price to closing price: assume 7–12%, not the usual 3–5%.
  - Days on market: well-priced HCMC resale clears in 60–100 days; overpriced or legally
    uncertain stock sits 120–180+ days.
  - District 7 condominium median list price is approximately 59.8 tr/m2; Saigon South
    Residences trades above that on Phu My Hung developer branding despite its Nha Be address.
  - Rental band at the project is 12–22 tr/month, usable as a yield cross-check when pitching
    investor buyers.
  - The agent-selection candidate pool, derived from search visibility and therefore
    **unverified on actual closing performance**: on-site Saigon South Residences / Phu My Hung
    resident brokers; NasaLand (0909.777.500); Loc Phat Hung (0933.098.890); Phu Loi Land
    (Ms Phuong, 0902 894 889); Rever; Hoozing and Realtique for English-language reach; and the
    highest-listing-count individual brokers on the project pages of batdongsan.com.vn and
    nhatot.com.
- From `research/2026-07-06_tubehouse-dream-home-brainstorm.md`:
  - The tubehouse footprint is fixed at 4 m x 25 m = 100 m2, over 5 storeys, giving 500 m2 gross
    floor area. Programme is mixed-use: ground floor lease space plus car park, first floor
    lease, floors 2–4 family accommodation with 3 bedrooms and 3 bathrooms.
  - That brief recorded "no budget stated" and deferred all cost discussion. This plan closes
    that gap and is the first budget artifact in the repository.
  - Ho Chi Minh City turnkey townhouse (nha pho) construction in 2026 runs 5.0–9.5 tr/m2 across
    the market, with 5.0–7.5 tr/m2 the common band for a 5-storey build. Structural cost rises
    10–15% per storey above ground level. Premium material specification adds 20–40% over
    standard.

## Assumptions and Constraints

- **DEC-001:** The apartment is **river-view**, and prices against the 83.8 tr/m2 river-view
  comparable rather than the 72–80 tr/m2 standard-outlook band.
- **DEC-002:** The tubehouse is built to a **medium (mid-range) finish standard**, costed at
  **6.5 tr/m2**, giving 6.5 tr/m2 x 500 m2 = **3.25 ty** for construction.
- **DEC-003:** Listing price is **5.95 ty**. Target settlement band is **5.45–5.60 ty**.
  Published walk-away floor is **5.35 ty**.
- **DEC-004:** A **hard floor of 5.15 ty** exists below which no offer may be accepted without
  explicit written approval from the owner. The hard floor is never disclosed to any agent or
  buyer; only the 5.35 ty floor is communicated.
- **DEC-005:** Sale is run as an **open panel of exactly three agents from day one**, not an
  exclusive mandate.
- **DEC-006:** Panel discipline rules, all three mandatory and all three stated in the mandate
  terms sheet: (a) one fixed listing price identical across all three agents; (b) a
  seller-owned photo, video and floorplan asset pack issued identically to each agent, with no
  agent permitted to shoot or publish their own images; (c) a first-registration attribution
  rule under which the agent who first registers a named buyer in writing owns that buyer for
  30 calendar days.
- **DEC-007:** Commission is **1.5% of gross contract value, winner-takes-all**, plus a **0.3%
  bonus** if the notarised sale-purchase agreement is signed within 45 calendar days of the
  listing going live. Losing panel agents receive nothing.
- **DEC-008:** Deal terms are cash-buyer-preferred, with a **5% dat coc deposit** subject to
  forfeiture on buyer default, and a **30-calendar-day close**. Mortgage-financed buyers are
  accepted only on presentation of a bank pre-approval letter, and their close is capped at 45
  calendar days.
- **DEC-009:** The apartment is sold **before** any contractor is engaged for the tubehouse.
- **DEC-010:** There is **no hard deadline** for the sale. The build starts when the sale closes.
  Therefore no automatic time-based price reduction is scheduled; the price is held to day 90
  and then reassessed against fresh comparables.
- **DEC-011:** Under-declaring the contract value to reduce the 2% transfer tax is excluded.
  All documents assume the full contract value is declared.
- **ASM-001:** The unit's exact block, floor number and internal condition are not recorded in
  the repository. — **BINDING DEFAULT:** the executor treats the unit as a mid-to-high floor
  (floor 10 or above) 2-bedroom / 2-bathroom of 72.0 m2 with a river outlook and full existing
  furniture in good order. Every deliverable that states floor or block must use the literal
  placeholder token `[[BLOCK]]` and `[[FLOOR]]` so the owner can fill them in without editing
  prose.
- **ASM-002:** Foreign-ownership-quota eligibility for the unit is unknown and can only be
  confirmed by the building management board. — **BINDING DEFAULT:** the executor produces
  **both** Vietnamese and English listing copy, but marks the English copy
  `HOLD — DO NOT PUBLISH UNTIL QUOTA ELIGIBILITY IS CONFIRMED` in a banner at the top of the
  file, and the pricing model treats the unit as domestic-buyer-only (no foreign premium
  applied to the 5.95 ty list price).
- **ASM-003:** Live listing prices will have moved since the brief was written. — **BINDING
  DEFAULT:** the executor re-pulls comparables in PHASE-01 and, if the median live asking price
  per square metre for 70–76 m2 units at the project has moved by more than 5% from 80.0 tr/m2,
  records the delta and a recommended revised list price in the fact base **without** changing
  DEC-003; the owner decides whether to adopt it.
- **ASM-004:** Design, permit and connection fees for the tubehouse are not itemised anywhere in
  the repository. — **BINDING DEFAULT:** budget **200 tr** in total for architect fees,
  construction permit, and utility connections.
- **ASM-005:** Furniture, fittings and equipment (FF&E) for the tubehouse are not specified. —
  **BINDING DEFAULT:** budget **300 tr** for a medium finish standard across 500 m2.
- **ASM-006:** Build duration is not scheduled anywhere in the repository. — **BINDING
  DEFAULT:** assume **15 months** from contractor engagement to handover.
- **ASM-007:** The owner's current rent is 12 tr/month and is being paid whether or not the
  apartment sells. — **BINDING DEFAULT:** treat rent as an **information-only** line in the
  reconciliation (15 months x 12 tr = 180 tr) and exclude it from the funding gap calculation,
  because it is not incremental to the sale decision. Show it in the report as a separate,
  clearly labelled non-incremental line.
- **ASM-008:** Pre-listing presentation spend is unquantified. — **BINDING DEFAULT:** budget
  **20 tr** for paint touch-up, deep clean and professional photography.
- **CON-001:** The open-panel structure means no agent holds exclusivity leverage. The three
  discipline rules in DEC-006 are load-bearing, not optional; the mandate terms sheet must make
  all three non-negotiable conditions of the panel appointment.
- **CON-002:** Falling liquidity means time-on-market, not price erosion, is the dominant risk.
  DEC-010 (no deadline) is the mitigation and must not be quietly weakened.
- **CON-003:** No deliverable in this pack may fabricate a specific agent's transaction history,
  closing record, or performance statistic. The candidate pool is search-visibility-derived and
  every document that names a firm must repeat that caveat verbatim.
- **CON-004:** No deliverable may include legal or tax advice presented as authoritative. Every
  document touching tax or contract law carries the line: "Verify with a licensed Vietnamese
  notary (phong cong chung) and tax advisor before signing."

## Specification

All amounts are integers in plain VND unless stated otherwise.

### S1. Net proceeds from the sale

Let:

- `P` = gross contract value, in VND — the price written on the notarised sale-purchase agreement.
- `t` = transfer tax rate = `0.02` (2%, final, on gross contract value; not on gain).
- `c` = base commission rate = `0.015` (1.5%, winner-takes-all).
- `b` = speed bonus rate = `0.003` (0.3%), applied only when the notarised agreement is signed
  within 45 calendar days of the listing going live.
- `s` = 1 if the speed bonus is earned, otherwise 0.
- `E` = pre-listing presentation spend = `20_000_000` VND (ASM-008).

Then:

```
tax(P)        = round(P * t)
commission(P) = round(P * (c + b * s))
net(P, s)     = P - tax(P) - commission(P) - E
```

`round` is Python's built-in banker's rounding to the nearest whole VND. Because `P` is an
integer number of VND and the rates are exact decimals, compute with
`round(P * 2 // 100)`-style integer arithmetic where possible; the reference implementation must
use `int(round(P * rate))` and be asserted against the worked examples in S4.

### S2. Total build cost

Let:

- `A` = gross floor area = `500` m2 (100 m2 footprint x 5 storeys).
- `u` = unit construction cost = `6_500_000` VND/m2 (medium finish, DEC-002).
- `D` = design, permit and connection fees = `200_000_000` VND (ASM-004).
- `F` = furniture, fittings and equipment = `300_000_000` VND (ASM-005).
- `k` = construction contingency rate = `0.10` (10% of construction only, not of D or F).

Then:

```
construction   = A * u                      = 3_250_000_000
contingency    = round(construction * k)    =   325_000_000
build_total    = construction + D + F       = 3_750_000_000
build_with_ctg = build_total + contingency  = 4_075_000_000
```

### S3. Reconciliation and release gates

Let `R` = hard reserve held back and not released to the build = `750_000_000` VND.

```
surplus(P, s) = net(P, s) - build_with_ctg - R
```

Release gate logic, applied in this exact order:

1. If `P < 5_150_000_000` (the hard floor, DEC-004): **REJECT** the offer. Do not proceed.
   Escalate to the owner for explicit written approval.
2. Else if `P < 5_350_000_000` (the published floor, DEC-003): **ESCALATE**. The offer is above
   the hard floor but below the published floor; the owner decides.
3. Else if `surplus(P, s) < 0`: **PROCEED WITH REDUCED SCOPE.** Funds cover the build plus
   contingency but not the full 750 tr reserve. Record the shortfall and reduce `R` accordingly
   before engaging a contractor.
4. Else: **PROCEED.** Release `build_with_ctg` to the build in stages against contractor
   milestones, hold `R` untouched, and report `surplus` as free capital.

### S4. Worked examples (these are the required test fixtures)

| Scenario | `P` (VND) | `s` | `tax` | `commission` | `net` | `surplus` | Gate |
|---|---|---|---|---|---|---|---|
| List price, no bonus | 5_950_000_000 | 0 | 119_000_000 | 89_250_000 | 5_721_750_000 | 896_750_000 | PROCEED |
| Target mid, bonus earned | 5_500_000_000 | 1 | 110_000_000 | 99_000_000 | 5_271_000_000 | 446_000_000 | PROCEED |
| Published floor, no bonus | 5_350_000_000 | 0 | 107_000_000 | 80_250_000 | 5_142_750_000 | 317_750_000 | PROCEED |
| Below published floor | 5_300_000_000 | 0 | 106_000_000 | 79_500_000 | 5_094_500_000 | 269_500_000 | ESCALATE |
| At hard floor | 5_150_000_000 | 0 | 103_000_000 | 77_250_000 | 4_949_750_000 | 124_750_000 | ESCALATE |
| Below hard floor | 5_000_000_000 | 0 | 100_000_000 | 75_000_000 | 4_805_000_000 | -20_000_000 | REJECT |

Every figure in this table is authoritative. The implementation in PHASE-05 must reproduce all
of them exactly; any discrepancy is an implementation bug, not a table error.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Refresh and lock the comparable-price fact base | None | `deliverables/apartment-sale/01-price-fact-base.md` |
| PHASE-02 | Build the agent vetting and mandate pack | PHASE-01 | `02-agent-scorecard.md`, `03-agent-call-script.md`, `04-mandate-terms-sheet.md` |
| PHASE-03 | Build the listing asset pack | PHASE-01 | `05-listing-copy-vi.md`, `06-listing-copy-en.md`, `07-photo-shot-list.md` |
| PHASE-04 | Build the negotiation and closing playbook | PHASE-01, PHASE-03 | `08-negotiation-ladder.md`, `09-closing-tax-checklist.md` |
| PHASE-05 | Implement and test the proceeds-to-build waterfall | PHASE-01 | `scripts/sale_waterfall.py`, `tests/test_sale_waterfall.py`, `10-build-reconciliation.md` |
| PHASE-06 | Publish the HTML report, then commit and push | PHASE-01..05 | `reports/2026-08-29-apartment-sale-execution-pack.html`, one pushed commit |

## Detailed Phases

### PHASE-01 - Price Fact Base

**Goal**
Establish one dated, sourced, defensible pricing document that every later phase cites, and
verify whether the August 2026 comparables still hold.

**Tasks**
- [ ] TASK-01-01: Create the directory `deliverables/apartment-sale/`.
- [ ] TASK-01-02: Re-pull current asking prices for 70–76 m2 two-bedroom units at Saigon South
      Residences from at least three of these sources: `https://www.housenow.com.vn/can-ho-chung-cu/saigon-south-residences`,
      `https://angialand.com.vn/saigon-south-residence.html`,
      `https://nasaland.vn/saigon-south-residence.html`,
      `https://nhadat.cafeland.vn/ban-du-an/saigon-south-residences-1325/`,
      `https://www.nhatot.com/mua-ban-can-ho-chung-cu--saigon-south-residences-huyen-nha-be-pj2033453473`.
      Note that `https://batdongsan.com.vn/ban-can-ho-chung-cu-saigon-south-residences` returns
      HTTP 403 to automated fetching; if it cannot be read, record that fact rather than omitting it.
- [ ] TASK-01-03: For every listing captured, record: area in m2, bedroom count, asking price in
      ty, computed price per m2 in tr/m2 (asking price in VND divided by area, divided by 10^6,
      rounded to one decimal), the posting date, the source URL, and whether the listing states a
      river view or full furniture.
- [ ] TASK-01-04: Compute the median asking price per m2 across all captured 70–76 m2 listings.
      Compare it to the 80.0 tr/m2 baseline recorded in ASM-003. If the deviation exceeds 5%,
      add a clearly headed subsection `## Price Movement Alert` stating the new median, the
      percentage change, and a recommended revised list price computed as
      `median_tr_per_m2 * 72.0` rounded to the nearest 0.05 ty. Do **not** change DEC-003.
- [ ] TASK-01-05: Add an explicit `## Excluded Listings` subsection recording every listing below
      4.0 ty for a 70–76 m2 unit, with the reason for exclusion (bait listing, or a quote of the
      remaining balance on an unfinished purchase contract rather than a freehold transfer price).
- [ ] TASK-01-06: Add a `## River View Premium` subsection documenting that the highest live
      comparable, 71 m2 at 5.95 ty (83.8 tr/m2), is a river-view unit, and that the subject unit
      prices against it under DEC-001.
- [ ] TASK-01-07: Stamp the document with `As of: <YYYY-MM-DD> (Asia/Ho_Chi_Minh)` using the
      actual execution date.

**File Changes**
- `deliverables/apartment-sale/01-price-fact-base.md` (create): The full fact base as specified
  in the tasks above. Structure: `# Price Fact Base — Saigon South Residences 72 m2 River View`,
  then `## As Of`, `## Subject Unit`, `## Live Comparables` (a markdown table),
  `## Median and Movement`, `## Price Movement Alert` (omit entirely if deviation is under 5%),
  `## Excluded Listings`, `## River View Premium`, `## Pricing Decision` (restating DEC-003 and
  DEC-004 with the hard floor marked `CONFIDENTIAL — NOT FOR DISCLOSURE TO AGENTS OR BUYERS`),
  `## Sources` (a numbered list of every URL consulted with its access date).
- Leave every existing file in the repository unmodified in this phase.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase. Verification is by the shell checks in
`## Verification Strategy` (TEST-001, TEST-002).

**Dependencies**
- Network access to the listed property portals. If a portal is unreachable, record the failure
  in `## Sources` with the HTTP status and continue with the remaining sources; a minimum of
  three successfully read sources is required.

**Exit Criteria**
- [ ] `deliverables/apartment-sale/01-price-fact-base.md` exists and is non-empty.
- [ ] The `## Live Comparables` table contains at least 8 rows.
- [ ] At least 3 distinct source domains appear in `## Sources`.
- [ ] Every price in the document carries an explicit `ty` or `tr/m2` unit.
- [ ] The hard floor of 5.15 ty appears exactly once, under the CONFIDENTIAL marking.

**Phase Risks**
- **RISK-01-01:** Property portals aggressively rate-limit or block automated reads, producing a
  thin comparable set. Mitigation: the minimum bar is 3 sources and 8 listings; if that cannot
  be met, write the document anyway using the August 2026 figures inlined in `## Research Inputs`
  above, and add a prominent `## Data Freshness Warning` at the top stating exactly which
  sources failed and that the pricing rests on August 2026 data.
- **RISK-01-02:** Bait listings drag the computed median down and trigger a spurious Price
  Movement Alert. Mitigation: TASK-01-05 excludes sub-4.0 ty listings from the dataset **before**
  the median in TASK-01-04 is computed. Order matters.

### PHASE-02 - Agent Vetting and Mandate Pack

**Goal**
Give the owner everything needed to call 6–8 brokers, score them objectively, and appoint three
on identical written terms.

**Tasks**
- [ ] TASK-02-01: Write the weighted scorecard with these exact criteria and weights, totalling
      100: Verified project closings in the last 12 months (30); Written comparative market
      analysis quality (25); Response latency (15); Marketing commitment (15); Live buyer queue
      (10); Terms acceptance (5).
- [ ] TASK-02-02: For each criterion, write a concrete 0/partial/full scoring rubric. The CMA
      criterion must state that an agent who submits portal **asking** prices instead of
      **signed transaction** prices scores 0 on that criterion regardless of presentation quality
      — this is the primary filter given the current wide bid-ask spread.
- [ ] TASK-02-03: Render the candidate pool as a table with columns: candidate, contact if known,
      channel type (on-site broker / project-specialist agency / national platform /
      English-language platform / individual portal broker), why they are on the list, and a
      blank `Score` column. Reproduce the CON-003 caveat verbatim immediately above the table:
      "This pool is derived from public search visibility, which measures marketing spend rather
      than closing ability. No claim is made about any firm's transaction history. Score them
      yourself using the rubric below."
- [ ] TASK-02-04: Write the call script as a numbered sequence of questions mapping one-to-one
      onto the scorecard criteria, with a note after each on what a strong versus weak answer
      sounds like. Include an explicit instruction to ask for two unit numbers and closing months
      that can be cross-checked with the building management board.
- [ ] TASK-02-05: Write the mandate terms sheet as a document the owner can send to all three
      appointed agents unchanged. It must state: the fixed listing price of 5.95 ty; commission
      of 1.5% winner-takes-all plus a 0.3% bonus for a notarised agreement within 45 calendar
      days; the three panel discipline rules from DEC-006 as non-negotiable conditions; the
      published floor of 5.35 ty as the lowest price the agent may present; the requirement that
      all offers be submitted in writing; and the 30-day first-registration buyer attribution
      rule with a worked example of how a disputed buyer is resolved.
- [ ] TASK-02-06: Add the CON-004 verification line to the mandate terms sheet.

**File Changes**
- `deliverables/apartment-sale/02-agent-scorecard.md` (create): scoring rubric, weights, candidate
  pool table, and a blank scoring grid for 8 candidates.
- `deliverables/apartment-sale/03-agent-call-script.md` (create): the numbered call script.
- `deliverables/apartment-sale/04-mandate-terms-sheet.md` (create): the send-as-is terms sheet.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase.

**Dependencies**
- PHASE-01, for the listing price and floor figures cited in the mandate terms sheet.

**Exit Criteria**
- [ ] All three files exist and are non-empty.
- [ ] The scorecard weights sum to exactly 100.
- [ ] The CON-003 caveat appears verbatim in `02-agent-scorecard.md`.
- [ ] The hard floor of 5.15 ty appears **nowhere** in any of the three files — it is
      owner-confidential and these documents are sent to agents.
- [ ] `04-mandate-terms-sheet.md` states all three DEC-006 discipline rules.

**Phase Risks**
- **RISK-02-01:** The hard floor leaks into an agent-facing document, destroying negotiating
  position. Mitigation: the exit criteria include an explicit absence check, enforced by TEST-003.

### PHASE-03 - Listing Asset Pack

**Goal**
Produce the marketing material the owner hands identically to all three panel agents, satisfying
the seller-owned-assets discipline rule.

**Tasks**
- [ ] TASK-03-01: Write Vietnamese listing copy with full diacritics, structured as: a headline
      under 70 characters; a 3-sentence lead; a bulleted specification block (area 72 m2, 2
      bedrooms, 2 bathrooms, block `[[BLOCK]]`, floor `[[FLOOR]]`, river view, fully furnished,
      So hong issued, no mortgage); an amenities paragraph; a location paragraph naming Nguyen
      Huu Tho, Phu My Hung adjacency, and RMIT University; and a price and contact block quoting
      5.95 ty.
- [ ] TASK-03-02: Lead the Vietnamese copy on the two strongest differentiators in the current
      market: **So hong issued with no mortgage** (fastest legal transfer, a genuine scarcity
      signal while liquidity is tight) and **river view**.
- [ ] TASK-03-03: Write the English listing copy as an equivalent, not a literal translation,
      pitched at expatriate and foreign buyers, and include the rental yield cross-check using
      the 12–22 tr/month project band.
- [ ] TASK-03-04: Place a banner as the very first line of the English file, in bold:
      `HOLD — DO NOT PUBLISH UNTIL FOREIGN-OWNERSHIP QUOTA ELIGIBILITY IS CONFIRMED WITH THE SSR MANAGEMENT BOARD.`
- [ ] TASK-03-05: Write the photography shot list as a numbered sequence of at least 18 specific
      shots, each with room, angle, time of day, and purpose. Include at least three shots that
      specifically establish the river view, and a note that the pack must include a floorplan
      graphic and a short vertical video walkthrough for portal and social distribution.
- [ ] TASK-03-06: Add a `## Portal Placement` section to the shot list file naming
      batdongsan.com.vn and nhatot.com as the primary Vietnamese portals, with a note that
      boosted placement on batdongsan.com.vn is the marketing-commitment item agents are scored
      on in PHASE-02.
- [ ] TASK-03-07: Add a `## Pre-Listing Presentation` section budgeting the 20 tr from ASM-008
      across paint touch-up, deep clean, and professional photography.

**File Changes**
- `deliverables/apartment-sale/05-listing-copy-vi.md` (create): Vietnamese copy, diacritics required.
- `deliverables/apartment-sale/06-listing-copy-en.md` (create): English copy, with the HOLD banner.
- `deliverables/apartment-sale/07-photo-shot-list.md` (create): shot list, portal placement,
  presentation budget.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase.

**Dependencies**
- PHASE-01, for the 5.95 ty listing price quoted in both copy files.

**Exit Criteria**
- [ ] All three files exist and are non-empty.
- [ ] `06-listing-copy-en.md` begins with the HOLD banner on its first non-empty line.
- [ ] `07-photo-shot-list.md` contains at least 18 numbered shots.
- [ ] Both copy files quote 5.95 ty and neither mentions any floor price.
- [ ] `05-listing-copy-vi.md` contains Vietnamese diacritical characters.

**Phase Risks**
- **RISK-03-01:** English copy is published before quota eligibility is confirmed, attracting
  buyers who legally cannot complete and wasting weeks of market time. Mitigation: the HOLD
  banner, enforced by TEST-004.

### PHASE-04 - Negotiation and Closing Playbook

**Goal**
Convert the pricing decision into a scripted response for every offer the owner is likely to
receive, and enumerate the legal and tax steps from accepted offer to registered transfer.

**Tasks**
- [ ] TASK-04-01: Write the negotiation ladder as a table with columns: offer band, what it means,
      scripted response, and concession available. Cover these bands: at or above 5.75 ty;
      5.60–5.74 ty; 5.45–5.59 ty (the target band); 5.35–5.44 ty; 5.15–5.34 ty; below 5.15 ty.
- [ ] TASK-04-02: Encode the gate logic from `## Specification` S3 into the ladder, so that the
      band below 5.35 ty reads ESCALATE and the band below 5.15 ty reads REJECT.
- [ ] TASK-04-03: Document the non-price concessions available in preference order, cheapest
      first: leaving the existing furniture in place; flexible handover date; the seller paying
      the notary fee; a longer deposit-to-close window. State explicitly that price is the last
      concession, not the first.
- [ ] TASK-04-04: Add a `## Expected Discount` section stating that the market currently clears
      7–12% below asking price, so an offer at 5.35 ty against a 5.95 ty list is a 10.1%
      discount and therefore **a normal market outcome, not a lowball**. Include the arithmetic.
- [ ] TASK-04-05: Write the closing checklist as an ordered sequence covering: accepted offer in
      writing; deposit contract (hop dong dat coc) with the 5% deposit and forfeiture clause;
      document assembly (So hong original, identity documents, marriage or single-status
      certificate, household registration); notarisation of the sale-purchase agreement at a
      licensed notary office; 2% transfer tax payment; registration fee; and transfer of the So
      hong to the buyer's name.
- [ ] TASK-04-06: Add a worked tax calculation to the closing checklist for three prices —
      5.95 ty, 5.50 ty and 5.35 ty — showing the 2% tax in tr for each (119 tr, 110 tr, 107 tr).
      State plainly that the tax is charged on gross contract value and is unaffected by what
      the apartment originally cost.
- [ ] TASK-04-07: Add a `## Mortgage-Financed Buyers` section stating the DEC-008 conditions and
      warning that a bank valuation coming in below the contract price can reopen the
      negotiation around week 4, which is the specific reason cash buyers are preferred.
- [ ] TASK-04-08: Add the CON-004 verification line to the closing checklist.

**File Changes**
- `deliverables/apartment-sale/08-negotiation-ladder.md` (create): the offer-band ladder,
  concession order, and expected-discount arithmetic.
- `deliverables/apartment-sale/09-closing-tax-checklist.md` (create): the ordered closing
  sequence, worked tax figures, mortgage-buyer conditions, and the verification line.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase.

**Dependencies**
- PHASE-01 for the price bands; PHASE-03 because the concession list references leaving the
  existing furniture, which the listing copy advertises as included.

**Exit Criteria**
- [ ] Both files exist and are non-empty.
- [ ] The negotiation ladder covers all six offer bands named in TASK-04-01.
- [ ] The three worked tax figures 119 tr, 110 tr and 107 tr all appear in
      `09-closing-tax-checklist.md`.
- [ ] The CON-004 verification line appears in `09-closing-tax-checklist.md`.

**Phase Risks**
- **RISK-04-01:** The owner reads a normal 10% market discount as an insult and rejects a sound
  offer, then sits on the market for another 90 days in falling liquidity. Mitigation: TASK-04-04
  states the arithmetic explicitly and labels that outcome normal.

### PHASE-05 - Proceeds-to-Build Waterfall

**Goal**
Implement the reconciliation arithmetic as tested code so the release decision on any offer is
computed, not estimated, and write the narrative reconciliation document.

**Tasks**
- [ ] TASK-05-01: Create `scripts/sale_waterfall.py` implementing the formulas in
      `## Specification` S1, S2 and S3 exactly. All monetary values are Python `int` in plain VND.
      Module-level constants must carry the identifiers used in the specification.
- [ ] TASK-05-02: Give the module a command-line interface using `argparse` accepting
      `--price` (integer VND, required), `--speed-bonus` (a flag, default off), and
      `--format` (`text` or `json`, default `text`). Text output prints one labelled line per
      waterfall step with amounts formatted in `ty` to three decimal places; JSON output emits a
      single object with the keys `price_vnd`, `tax_vnd`, `commission_vnd`, `presentation_vnd`,
      `net_vnd`, `build_total_vnd`, `contingency_vnd`, `reserve_vnd`, `surplus_vnd`, `gate`.
- [ ] TASK-05-03: Create `tests/test_sale_waterfall.py` with one test per row of the S4 worked
      examples table, asserting the exact `tax`, `commission`, `net`, `surplus` and `gate` values.
      Name them `test_net_proceeds_at_list_price`, `test_net_proceeds_at_target_with_bonus`,
      `test_net_proceeds_at_floor_price`, `test_gate_escalates_below_published_floor`,
      `test_gate_escalates_at_hard_floor`, `test_gate_rejects_below_hard_floor`.
- [ ] TASK-05-04: Add three further tests: `test_build_total_is_medium_finish` asserting
      `construction == 3_250_000_000` and `build_with_contingency == 4_075_000_000`;
      `test_all_amounts_are_integers` asserting every returned monetary value is `int` and never
      `float`; and `test_json_output_keys` asserting the JSON object carries exactly the ten keys
      listed in TASK-05-02.
- [ ] TASK-05-05: Write the narrative reconciliation document presenting the S4 table in `ty`
      units for a human reader, the four release gates in plain language, and the 15-month rent
      line of 180 tr clearly labelled `NON-INCREMENTAL — paid whether or not the apartment sells`
      per ASM-007.
- [ ] TASK-05-06: In the reconciliation document, state the headline conclusion explicitly: at
      the published floor of 5.35 ty the sale nets 5.143 ty against a build-plus-contingency cost
      of 4.075 ty, leaving 1.068 ty, of which 750 tr is held as hard reserve and 318 tr is free
      surplus. The build is funded with margin at every price down to the hard floor.
- [ ] TASK-05-07: Run `python -m ruff check .` and `python -m ruff format .` and fix all findings.

**File Changes**
- `scripts/sale_waterfall.py` (create): the waterfall implementation and CLI. Keep it dependency-
  free — standard library only, no imports from `src/homedesign/`. Respect `line-length = 120`.
- `tests/test_sale_waterfall.py` (create): the nine tests above. Import the module by path-
  independent means: add `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))`
  at the top of the test file, because `pyproject.toml` puts only `src` on `pythonpath` and
  `scripts/` is not an installed package.
- `deliverables/apartment-sale/10-build-reconciliation.md` (create): the narrative reconciliation.
- Do not modify `pyproject.toml`, `ruff.toml`, or any existing file under `src/`, `tests/`,
  `designs/` or `spec/`.

**Function Signatures**
- `transfer_tax(price_vnd: int) -> int` — the 2% transfer tax on gross contract value, in whole VND.
- `commission(price_vnd: int, speed_bonus: bool) -> int` — total agent commission in whole VND;
  1.5% of price, plus a further 0.3% when `speed_bonus` is True.
- `net_proceeds(price_vnd: int, speed_bonus: bool) -> int` — price less transfer tax, less
  commission, less the 20 tr presentation spend, in whole VND.
- `build_cost() -> dict[str, int]` — a mapping with keys `construction`, `design_permits`,
  `ffe`, `contingency`, `total`, `total_with_contingency`, all in whole VND.
- `surplus(price_vnd: int, speed_bonus: bool) -> int` — net proceeds less build-with-contingency
  less the 750 tr hard reserve, in whole VND; may be negative.
- `release_gate(price_vnd: int, speed_bonus: bool) -> str` — one of the exact strings
  `"REJECT"`, `"ESCALATE"`, `"PROCEED WITH REDUCED SCOPE"`, `"PROCEED"`, applying the S3 rules
  in the stated order.
- `waterfall(price_vnd: int, speed_bonus: bool) -> dict[str, int | str]` — the full breakdown
  carrying exactly the ten keys named in TASK-05-02.
- `main(argv: list[str] | None = None) -> int` — CLI entry point; returns process exit code 0
  on success.

**Test Specs**
- `waterfall(5_950_000_000, speed_bonus=False)` → `tax_vnd == 119_000_000`,
  `commission_vnd == 89_250_000`, `net_vnd == 5_721_750_000`, `surplus_vnd == 896_750_000`,
  `gate == "PROCEED"`.
- `waterfall(5_500_000_000, speed_bonus=True)` → `tax_vnd == 110_000_000`,
  `commission_vnd == 99_000_000`, `net_vnd == 5_271_000_000`, `surplus_vnd == 446_000_000`,
  `gate == "PROCEED"`.
- `waterfall(5_350_000_000, speed_bonus=False)` → `tax_vnd == 107_000_000`,
  `commission_vnd == 80_250_000`, `net_vnd == 5_142_750_000`, `surplus_vnd == 317_750_000`,
  `gate == "PROCEED"`.
- `release_gate(5_300_000_000, speed_bonus=False)` → `"ESCALATE"` (above the 5.15 ty hard floor,
  below the 5.35 ty published floor).
- `release_gate(5_150_000_000, speed_bonus=False)` → `"ESCALATE"` — boundary case: the hard floor
  itself is **not** a rejection; rejection begins strictly below it. Assert this explicitly.
- `release_gate(5_149_999_999, speed_bonus=False)` → `"REJECT"` — one VND below the hard floor.
- `build_cost()` → `{"construction": 3_250_000_000, "design_permits": 200_000_000,
  "ffe": 300_000_000, "contingency": 325_000_000, "total": 3_750_000_000,
  "total_with_contingency": 4_075_000_000}`.
- Every value returned by `waterfall(...)` except `gate` → `isinstance(value, int) is True` and
  `isinstance(value, float) is False`.
- `waterfall(5_950_000_000, speed_bonus=False).keys()` → exactly the set
  `{"price_vnd", "tax_vnd", "commission_vnd", "presentation_vnd", "net_vnd", "build_total_vnd",
  "contingency_vnd", "reserve_vnd", "surplus_vnd", "gate"}`.

**Dependencies**
- PHASE-01, for confirmation that the pricing decision in DEC-003 still stands.
- Python standard library only. Add no new entries to `pyproject.toml`.

**Exit Criteria**
- [ ] `python -m pytest tests/test_sale_waterfall.py -v` reports 9 passed, 0 failed.
- [ ] `python -m pytest` reports 235 passed (226 pre-existing plus 9 new), 0 failed.
- [ ] `python -m ruff check .` exits 0.
- [ ] `python scripts/sale_waterfall.py --price 5350000000 --format json` emits valid JSON with
      `"gate": "PROCEED"` and `"net_vnd": 5142750000`.
- [ ] `deliverables/apartment-sale/10-build-reconciliation.md` exists and states the 1.068 ty
      headline figure.

**Phase Risks**
- **RISK-05-01:** Floating-point arithmetic introduces sub-VND drift that makes the worked
  examples fail by one dong. Mitigation: all amounts are `int` in plain VND and the
  `test_all_amounts_are_integers` test enforces it.
- **RISK-05-02:** The test file cannot import from `scripts/` because that directory is not on
  the path. Mitigation: the explicit `sys.path.insert` prescribed in File Changes.
- **RISK-05-03:** The pre-existing suite count is not exactly 226 at execution time, making the
  235 exit criterion fail spuriously. Mitigation: if the baseline differs, record the actual
  baseline count and assert `baseline + 9` instead; the substantive requirement is that no
  pre-existing test breaks.

### PHASE-06 - HTML Report, Commit and Push

**Goal**
Summarise the whole pack in one styled, self-contained HTML report matching the repository's
existing report house style, then commit and push everything.

**Tasks**
- [ ] TASK-06-01: Read `reports/2026-08-15-final-drawing-truth-and-construction-set.html` and
      reuse its CSS custom-property palette and typography verbatim: `--paper: #fbf7f1`,
      `--paper-strong: #fffdf9`, `--ink: #1f1912`, `--ink-soft: #5f564c`, `--line: #dccdb6`,
      `--line-strong: #bfa37d`, `--accent: #9d6b37`, `--accent-soft: #efe4d0`,
      `--accent-2: #3b6f76`, `--radius-lg: 24px`, `--radius-md: 18px`, `--radius-sm: 12px`,
      `--page-width: 1040px`, display font `Georgia, "Times New Roman", serif`, body font
      `"Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif`, mono font
      `"Cascadia Code", Consolas, monospace`. Include the same
      `<meta name="color-scheme" content="dark light">` tag.
- [ ] TASK-06-02: Build the report with these sections in order: title and as-of date; an
      executive summary stating the 5.95 ty list, 5.35 ty floor and the funded conclusion; a
      pricing section rendering the comparables table from PHASE-01; a Chart.js horizontal bar
      chart comparing asking price per m2 across the captured comparables with the subject
      unit's 82.6 tr/m2 list price highlighted in `--accent`; a Chart.js stacked bar or waterfall
      visual showing net proceeds decomposing into build, contingency, reserve and surplus at the
      floor price; the agent panel method; the sale timeline; the negotiation ladder; the closing
      sequence; and a deliverables index linking every file in `deliverables/apartment-sale/`
      with a relative href.
- [ ] TASK-06-03: Load Chart.js from `https://cdn.jsdelivr.net/npm/chart.js` exactly as the
      existing reports do. Do not vendor it locally and do not add a build step.
- [ ] TASK-06-04: Include a mermaid flowchart of the release-gate decision logic from
      `## Specification` S3, using the same mermaid ESM import and `themeVariables` block as the
      existing report so the diagram matches the palette.
- [ ] TASK-06-05: Ensure the report renders correctly with no network access to anything other
      than the two jsDelivr CDN URLs, and that all content is legible if both scripts fail to
      load — every chart must be preceded by the same data in an HTML `<table>`.
- [ ] TASK-06-06: Verify the working tree contains only intended changes by reviewing
      `git status --porcelain`. The expected additions are exactly: ten files under
      `deliverables/apartment-sale/`, `scripts/sale_waterfall.py`, `tests/test_sale_waterfall.py`,
      `reports/2026-08-29-apartment-sale-execution-pack.html`, and this plan file. Do not commit
      anything under `output/` or any `__pycache__/` directory.
- [ ] TASK-06-07: Re-run the full verification suite one final time before committing:
      `python -m pytest` and `python -m ruff check .`, both must pass.
- [ ] TASK-06-08: Stage and commit with this exact message subject:
      `feat(sale): apartment sale execution pack — pricing, agent panel, closing, build reconciliation`
      and a body summarising the six phases, the 5.95 ty list price, the 5.35 ty floor, and the
      1.068 ty funded margin at the floor.
- [ ] TASK-06-09: Push to `origin master` and confirm the push succeeded by checking that
      `git status -sb` reports the local branch is not ahead of its remote tracking branch.

**File Changes**
- `reports/2026-08-29-apartment-sale-execution-pack.html` (create): the styled report described
  above, self-contained apart from the two CDN script tags.
- No existing file is modified. In particular, leave `activeContext.md`, `lessons.md`,
  `AGENTS.md`, `docs/`, `designs/`, `spec/` and everything under `src/` untouched.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase. Verification is by TEST-006 through TEST-009.

**Dependencies**
- All of PHASE-01 through PHASE-05 complete, with their exit criteria met.
- A configured git remote. The repository's `origin` is
  `https://github.com/tah-allotrope/freecad-blender.git` and the working branch is `master`.

**Exit Criteria**
- [ ] `reports/2026-08-29-apartment-sale-execution-pack.html` exists and is over 15 KB.
- [ ] The report contains at least one `<canvas>` element and at least one `<table>` element.
- [ ] `python -m pytest` passes with zero failures.
- [ ] `git status --porcelain` is empty after the commit.
- [ ] `git status -sb` shows no `ahead` marker for the local branch after the push.
- [ ] `git log --oneline -1` shows the new commit at HEAD.

**Phase Risks**
- **RISK-06-01:** Generated artifacts under `output/` or stray `__pycache__/` directories get
  swept into the commit. Mitigation: TASK-06-06 reviews `git status --porcelain` against an
  explicit expected file list before staging; stage named paths rather than using `git add -A`.
- **RISK-06-02:** The push is rejected because the remote has advanced. Mitigation: run
  `git pull --rebase origin master` before pushing, then re-run `python -m pytest` to confirm the
  rebase did not break anything.

## Gotchas

- **`ty` and `tr` differ by a factor of 1000.** 5.95 ty is 5,950,000,000 VND; 119 tr is
  119,000,000 VND. A single confusion here produces a document that is wrong by three orders of
  magnitude. Every number written into a deliverable carries its unit.
- **The 2% transfer tax is on gross contract value, not on gain.** It does not matter what the
  apartment originally cost. Any document that computes tax on a profit figure is wrong.
- **Aggregator "reference" price tables lag the live market by roughly 0.5 ty** at this project.
  Anchoring to them instead of to dated live listings would under-price the unit by around 10%.
  Always prefer a listing with a visible posting date.
- **Sub-4.0 ty listings for 70–76 m2 units are not comparables.** They are bait listings or
  quotes of the remaining balance on an unfinished purchase contract. They must be excluded from
  the dataset before any median is computed, not after.
- **The hard floor of 5.15 ty is owner-confidential.** It may appear in `01-price-fact-base.md`
  (under a CONFIDENTIAL marking), `08-negotiation-ladder.md`, `10-build-reconciliation.md`, the
  waterfall code and the report — but never in any of the three agent-facing files produced in
  PHASE-02, and never in the listing copy.
- **A 10% discount from asking price is a normal market outcome right now, not a lowball.**
  Liquidity is falling faster than asking prices are, which widens the spread between what
  sellers ask and what buyers pay.
- **The three panel-discipline rules are load-bearing.** An open panel without a single fixed
  price, seller-owned marketing assets, and written buyer attribution degrades into three agents
  undercutting each other on the same unit while none invests in marketing. Do not soften them.
- **Rent of 12 tr/month is not incremental to this decision.** It is paid whether or not the
  apartment sells, so it must never be added into the funding gap. Show it, label it
  non-incremental, and exclude it from the arithmetic.
- **`scripts/` is not on the Python path.** `pyproject.toml` sets `pythonpath = ["src"]` only, so
  the new test file needs an explicit `sys.path` insertion to import `sale_waterfall`.
- **`ruff.toml` sets `line-length = 120`,** which is wider than ruff's default of 88. Do not
  reformat to 88.
- **Do not touch the rendering pipeline.** This plan adds financial documents and one standalone
  script. Nothing under `src/homedesign/`, `designs/` or `spec/` changes. In particular, do not
  run any Blender command; this repository pins Blender 4.1 legacy EEVEE for machine-specific
  reasons documented in `AGENTS.md`, and none of that is relevant here.
- **Do not fabricate agent performance data.** No document may state that a named firm closed a
  specific number of units or achieved a specific price. The candidate pool is a starting list
  for the owner to vet by telephone, and every document naming firms must say so.

## Verification Strategy

- **TEST-001:** `ls deliverables/apartment-sale/ | wc -l` → `10`
- **TEST-002:** `grep -c '^|' deliverables/apartment-sale/01-price-fact-base.md` → a number `>= 10`
  (the comparables table header, separator and at least 8 data rows).
- **TEST-003:** `grep -rl '5.15' deliverables/apartment-sale/02-agent-scorecard.md deliverables/apartment-sale/03-agent-call-script.md deliverables/apartment-sale/04-mandate-terms-sheet.md`
  → no output, exit status 1. The confidential hard floor must not appear in any agent-facing file.
- **TEST-004:** `head -5 deliverables/apartment-sale/06-listing-copy-en.md | grep -c 'HOLD'` → `1`
- **TEST-005:** `python -m pytest tests/test_sale_waterfall.py -v` → `9 passed`
- **TEST-006:** `python -m pytest` → all tests pass, zero failures, zero errors.
- **TEST-007:** `python -m ruff check .` → `All checks passed!`, exit status 0.
- **TEST-008:** `python scripts/sale_waterfall.py --price 5350000000 --format json` → valid JSON
  containing `"gate": "PROCEED"`, `"net_vnd": 5142750000`, `"surplus_vnd": 317750000`.
- **TEST-009:** `python scripts/sale_waterfall.py --price 5000000000 --format json` → valid JSON
  containing `"gate": "REJECT"`.
- **TEST-010:** `test -s reports/2026-08-29-apartment-sale-execution-pack.html && echo OK` → `OK`
- **TEST-011:** `grep -c '<canvas' reports/2026-08-29-apartment-sale-execution-pack.html` → `>= 2`
- **TEST-012:** `git status --porcelain` after committing → empty output.
- **TEST-013:** `git status -sb | head -1` after pushing → a line containing `## master...origin/master`
  with no `[ahead N]` marker.
- **MANUAL-001:** Open `reports/2026-08-29-apartment-sale-execution-pack.html` in a browser and
  confirm both charts render, the mermaid gate diagram renders, and the deliverables index links
  resolve to the files in `deliverables/apartment-sale/`.
- **MANUAL-002:** Read `deliverables/apartment-sale/04-mandate-terms-sheet.md` end to end as if
  you were a broker receiving it, and confirm it contains no confidential figure and no
  instruction that only makes sense to someone who read this plan.
- **MANUAL-003:** Confirm every price in every deliverable carries an explicit `ty`, `tr`, or
  `tr/m2` unit; spot-check at least ten figures across at least four files.

## Risks and Alternatives

- **RISK-001:** The comparable refresh in PHASE-01 finds the market has moved materially against
  the 5.95 ty list price, invalidating figures hard-coded into five later documents. Mitigation:
  ASM-003 requires the deviation to be recorded as an alert without changing DEC-003, so the pack
  stays internally consistent and the owner makes one explicit decision rather than the executor
  silently repricing mid-run.
- **RISK-002:** Portals block automated reads and the fact base rests on August 2026 figures.
  Mitigation: RISK-01-01's fallback writes the document with a prominent freshness warning naming
  the failed sources, so the owner knows precisely how stale the basis is.
- **RISK-003:** The pack is thorough but the owner never makes the one phone call that gates the
  English-language channel. Mitigation: the quota check is the first item of the report's
  executive summary and the HOLD banner makes the dependency impossible to miss.
- **RISK-004:** Documents drift out of agreement — the ladder quoting one floor, the
  reconciliation another. Mitigation: PHASE-05 makes the arithmetic executable, and MANUAL-003
  spot-checks units and figures across files.
- **ALT-001:** Implement the whole pack as a single generated document rather than ten files.
  Not chosen: the mandate terms sheet and the listing copy are sent to third parties and must be
  separable from the confidential pricing floor and the build reconciliation.
- **ALT-002:** Skip the Python waterfall and put the arithmetic in a spreadsheet. Not chosen: the
  repository is Python with a 226-test pytest suite, so tested code is the idiom here, and the
  worked examples become regression tests rather than untested cells.
- **ALT-003:** Model an exclusive-agency sale instead of a three-agent open panel. Not chosen:
  the open panel is fixed by DEC-005. The mandate terms sheet compensates with the discipline
  rules that an exclusive would otherwise provide for free.
- **ALT-004:** List at 5.75 ty for a faster clear. Not chosen: the unit is river-view (DEC-001)
  and the strongest live comparable at the project, 71 m2 at 83.8 tr/m2, is also river-view.
  Listing at 5.75 ty would price a river-view unit into the standard-outlook band and forfeit
  roughly 200 tr. There is no deadline (DEC-010), so the time cost of the higher ask is
  affordable.

## Suggested Next Step

Execute PHASE-01. Create `deliverables/apartment-sale/` and build the price fact base, then
verify TEST-001 and TEST-002 before starting PHASE-02. Each phase's exit criteria are verifiable
before the next begins; PHASE-02, PHASE-03 and PHASE-05 depend only on PHASE-01 and may be
executed in any order once it is complete.
