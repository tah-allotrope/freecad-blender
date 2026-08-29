# Build Reconciliation — Sale Proceeds vs Tubehouse Cost

*As of: 2026-08-29 (Asia/Ho_Chi_Minh)*

## Summary

The sale of the 72.0 m2 river-view apartment at Saigon South Residences funds the 500 m2, 5-storey tubehouse (medium finish at 6.5 tr/m2) with margin at every price down to the hard floor. At the published floor of **5.35 ty** the sale nets **5.143 ty** against a build-plus-contingency cost of **4.075 ty**, leaving **1.068 ty**, of which **750 tr** is held as hard reserve and **318 tr** is free surplus.

## Build Cost (medium finish, DEC-002)

| Component | Amount (VND) | Amount (ty/tr) |
|---|---|---|
| Gross floor area | 500 m2 (100 m2 x 5 storeys) | — |
| Unit cost (medium finish) | 6_500_000 VND/m2 | 6.5 tr/m2 |
| Construction (500 x 6.5 tr) | 3_250_000_000 VND | 3.25 ty |
| Design, permits & connections (ASM-004) | 200_000_000 VND | 200 tr |
| Furniture, fittings & equipment (ASM-005) | 300_000_000 VND | 300 tr |
| **Build total (without contingency)** | **3_750_000_000 VND** | **3.75 ty** |
| Contingency 10% of construction only | 325_000_000 VND | 325 tr |
| **Build with contingency** | **4_075_000_000 VND** | **4.075 ty** |
| Hard reserve (S3) | 750_000_000 VND | 750 tr |
| Build with contingency + reserve | 4_825_000_000 VND | 4.825 ty |

Verify with a licensed Vietnamese notary (phong cong chung) and tax advisor before signing.

## Waterfall — Worked Examples (Specification S4)

All amounts are integers in plain VND. Tax is 2% of gross contract value, final. Commission is 1.5% winner-takes-all plus 0.3% speed bonus when the notarised agreement is signed within 45 calendar days of listing. Presentation spend is 20 tr (ASM-008).

| Scenario | `P` (VND) | `s` | Tax (VND) | Commission (VND) | Net (VND) | Surplus (VND) | Gate |
|---|---|---|---|---|---|---|---|
| List price, no bonus | 5_950_000_000 | 0 | 119_000_000 | 89_250_000 | 5_721_750_000 | 896_750_000 | PROCEED |
| Target mid, bonus earned | 5_500_000_000 | 1 | 110_000_000 | 99_000_000 | 5_271_000_000 | 446_000_000 | PROCEED |
| Published floor, no bonus | 5_350_000_000 | 0 | 107_000_000 | 80_250_000 | 5_142_750_000 | 317_750_000 | PROCEED |
| Below published floor | 5_300_000_000 | 0 | 106_000_000 | 79_500_000 | 5_094_500_000 | 269_500_000 | ESCALATE |
| At hard floor | 5_150_000_000 | 0 | 103_000_000 | 77_250_000 | 4_949_750_000 | 124_750_000 | ESCALATE |
| Below hard floor | 5_000_000_000 | 0 | 100_000_000 | 75_000_000 | 4_805_000_000 | -20_000_000 | REJECT |

In ty for a human reader:

| Scenario | Price | Tax | Commission | Net | Surplus | Gate |
|---|---|---|---|---|---|---|
| List price, no bonus | 5.950 ty | 119 tr | 89.25 tr | 5.722 ty | 897 tr | PROCEED |
| Target mid, bonus | 5.500 ty | 110 tr | 99 tr | 5.271 ty | 446 tr | PROCEED |
| Published floor | 5.350 ty | 107 tr | 80.25 tr | 5.143 ty | 318 tr | PROCEED |
| Below published floor | 5.300 ty | 106 tr | 79.5 tr | 5.095 ty | 270 tr | ESCALATE |
| At hard floor | 5.150 ty | 103 tr | 77.25 tr | 4.950 ty | 125 tr | ESCALATE |
| Below hard floor | 5.000 ty | 100 tr | 75 tr | 4.805 ty | -20 tr | REJECT |

Every figure in the table above reproduces the Specification S4 worked examples exactly. The implementation in `scripts/sale_waterfall.py` is asserted against these figures in `tests/test_sale_waterfall.py`.

## Release Gates (Specification S3, in order)

1. If `P < 5_150_000_000` (hard floor, DEC-004) — **REJECT**. Do not proceed. Escalate to the owner for explicit written approval. This floor is confidential and never disclosed to agents or buyers.
2. Else if `P < 5_350_000_000` (published floor, DEC-003) — **ESCALATE**. Above the hard floor but below the published floor; the owner decides.
3. Else if `surplus(P, s) < 0` — **PROCEED WITH REDUCED SCOPE**. Funds cover the build plus contingency but not the full 750 tr reserve. Record the shortfall and reduce `R` accordingly before engaging a contractor.
4. Else — **PROCEED**. Release `build_with_contingency` (4.075 ty) to the build in stages against contractor milestones, hold `R` (750 tr) untouched, and report `surplus` as free capital.

## Headline Conclusion

At the published floor of **5.35 ty** the sale nets **5.143 ty** against a build-plus-contingency cost of **4.075 ty**, leaving **1.068 ty**, of which **750 tr** is held as hard reserve and **318 tr** is free surplus. **The build is funded with margin at every price down to the hard floor** (5.15 ty still leaves 125 tr of surplus after the reserve).

## Rent During the Build — Non-Incremental

The owner's current rent is **12 tr/month**. Over the assumed **15-month** build (ASM-006), that is **15 x 12 tr = 180 tr**.

**180 tr — NON-INCREMENTAL — paid whether or not the apartment sells.** This rent is already being paid and is not caused by the sale decision. It is shown here for information only and is **excluded from the funding gap calculation**. The surplus figures above are stated before rent.

If rent were added to the build cost, the total cash need would be 4.075 ty + 750 tr + 180 tr = 5.005 ty, still below the floor-price net of 5.143 ty.

## How to Recompute Any Offer

```bash
python scripts/sale_waterfall.py --price 5350000000 --format text
python scripts/sale_waterfall.py --price 5350000000 --format json
python scripts/sale_waterfall.py --price 5500000000 --speed-bonus --format json
```

The JSON output carries the ten keys `price_vnd`, `tax_vnd`, `commission_vnd`, `presentation_vnd`, `net_vnd`, `build_total_vnd`, `contingency_vnd`, `reserve_vnd`, `surplus_vnd`, `gate`.

---
*Verify with a licensed Vietnamese notary (phong cong chung) and tax advisor before signing.*
