# Negotiation Ladder — Saigon South Residences 72 m2 River View

List price: **5.95 ty**. Published floor: **5.35 ty**. Hard floor: **5.15 ty — CONFIDENTIAL, never disclosed to agents or buyers**. All offers handled per the release-gate logic in `## Specification` S3 and `scripts/sale_waterfall.py`.

## Offer-Band Ladder

| Offer band (ty) | Discount vs 5.95 ty list | What it means | Gate | Scripted response | Concession available |
|---|---|---|---|---|---|
| At or above 5.75 ty | 0-3.4% | Strong offer, near ask. In today's 7-12% discount market this is an unusually tight spread. | **PROCEED** | "Thank you for the offer at [PRICE] ty. We accept in principle — let us move to a 5% dat coc deposit and notarisation within 30 days." | None needed. Close fast; offer the speed bonus to the introducing agent as motivation. |
| 5.60-5.74 ty | 3.5-5.9% | Good offer, within normal negotiation range. | **PROCEED** | "We appreciate the offer at [PRICE] ty. The seller's position is 5.75 ty for a river-view unit with pink book ready. We can close at 5.70 ty with handover on your preferred date and furniture included." | Flexible handover date (cheapest). |
| 5.45-5.59 ty | 6.1-8.4% | Target settlement band (DEC-003). This is where the market is expected to clear. | **PROCEED** | "Thank you — [PRICE] ty is within the seller's working range. We counter at 5.55 ty with furniture included and the seller covering the notary fee. If you can confirm at 5.50 ty we can sign the dat coc this week." | Furniture included; flexible handover; seller pays notary fee (in ascending cost order). |
| 5.35-5.44 ty | 8.6-10.1% | At the published floor. Still a normal market discount (see Expected Discount below). Requires careful handling — the seller will accept but only with best terms. | **PROCEED** (at floor) | "The seller can accept 5.35 ty as the floor for a clean cash close in 30 days with 5% dat coc and forfeiture on buyer default. We ask for your bank pre-approval letter if mortgage-financed, and close within 45 days maximum." | Furniture + handover flexibility + notary fee. Price is the last concession, not the first. |
| 5.15-5.34 ty | 10.3-13.4% | Below the published floor but above the hard floor. | **ESCALATE** — above the 5.15 ty hard floor, below the 5.35 ty published floor; the owner decides. Do not accept or reject on the spot. | "Thank you for the offer at [PRICE] ty. That is below the price the seller has authorised us to accept. We will present it to the owner and respond in writing within 24 hours. In the meantime, can you improve the deposit or close timeline?" | None until owner decides. Use the time to test whether the buyer can stretch. |
| Below 5.15 ty | >13.4% | Below the hard floor. | **REJECT** — do not proceed. Escalate to the owner for explicit written approval; no acceptance is possible without it. | "Thank you for the offer at [PRICE] ty. The seller is not in a position to accept below 5.15 ty. If you can revisit your position we are happy to continue the conversation." | None. Hold the floor. |

Gate logic, applied in order: (1) if `P < 5.15 ty` then REJECT; (2) else if `P < 5.35 ty` then ESCALATE; (3) else if `surplus < 0` then PROCEED WITH REDUCED SCOPE (reserve is reduced); (4) else PROCEED. The surplus gate is computed by `scripts/sale_waterfall.py` and documented in `10-build-reconciliation.md`.

## Non-Price Concessions (in preference order, cheapest first)

1. **Leaving the existing furniture in place** — already advertised as included; conceding it costs the seller nothing incremental.
2. **Flexible handover date** — the unit is empty; the seller can accommodate the buyer's preferred handover within a reasonable window.
3. **Seller pays the notary fee** — a small, one-off cost relative to price.
4. **Longer deposit-to-close window** — extend from 30 to up to 45 days only if the buyer is mortgage-financed with a pre-approval letter.

**Price is the last concession, not the first.** Exhaust non-price concessions before moving on price, and never move below 5.35 ty without escalating to the owner.

## Expected Discount

The HCMC secondary market in Q3 2026 currently clears **7-12% below asking price**, not the usual 3-5%, because transaction liquidity is falling while asking prices remain firm (see `01-price-fact-base.md`).

Arithmetic for this listing:

* List: 5.95 ty. Published floor: 5.35 ty.
* Discount at the floor: `(5.95 - 5.35) / 5.95 = 0.1008 = 10.1%`.
* An offer at 5.35 ty is therefore a **10.1% discount — a normal market outcome, not a lowball**.
* Similarly: an offer at 5.50 ty is a 7.6% discount; at 5.60 ty a 5.9% discount. All are within or near the current 7-12% clearing band.

Do not read a 10% discount as an insult. In a falling-liquidity market, that spread is the market. Rejecting a sound offer at 5.35 ty to chase 5.95 ty risks sitting on the market for another 90 days with no better outcome.

## Tactical Notes

* Every offer must be submitted **in writing** (email or Zalo) with buyer name, price in ty, deposit readiness, and cash vs mortgage status.
* Cash buyers preferred; mortgage buyers only with a bank pre-approval letter and close capped at 45 days.
* Deposit: 5% dat coc, forfeiture on buyer default.
* There is no hard deadline and no automatic time-based price reduction. Hold the price to day 90, then reassess against fresh comparables.

---
*Verify with a licensed Vietnamese notary (phong cong chung) and tax advisor before signing.*
