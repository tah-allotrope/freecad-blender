# Closing & Tax Checklist — Saigon South Residences 72 m2 River View

## Ordered Closing Sequence

Follow in order from accepted offer to registered transfer. The seller and buyer attend notarisation together at a licensed notary office (phong cong chung).

1. **Accepted offer in writing** — buyer name, price in ty, deposit readiness, cash vs mortgage status. Seller countersigns acceptance.
2. **Deposit contract (hop dong dat coc)** — 5% of contract value (dat coc), subject to **forfeiture on buyer default**. Signed by both parties. Deposit is held as agreed (typically by the seller or a neutral escrow per local practice — confirm with the notary).
3. **Document assembly** — gather before the notarisation appointment:
   * So hong (pink book) original
   * Seller identity documents (CCCD / passport)
   * Marriage certificate or single-status certificate (giay xac nhan tinh trang hon nhan)
   * Household registration (if required by the notary)
   * Buyer identity documents and marriage/single-status certificate (buyer's responsibility)
   * Deposit contract and proof of deposit payment
4. **Notarisation of the sale-purchase agreement** — at a licensed notary office (phong cong chung). Both seller and buyer sign. The contract value written here is the gross price `P` used for tax.
5. **Transfer tax payment — 2% of gross contract value, final** — paid after notarisation at the tax office. The tax is assessed on the full contract value, not on the gain, and is unaffected by what the apartment originally cost. See Worked Tax Figures below.
6. **Registration fee** — small fixed fee to update the land registry (confirm amount with the notary; typically under 5 tr).
7. **Transfer of the So hong to the buyer's name** — submitted to the land registration office (Van phong dang ky dat dai) after tax is paid. The buyer receives the updated pink book.

Standard timeline: **30 calendar days** from deposit to close for cash buyers; **45 calendar days maximum** for mortgage-financed buyers with a bank pre-approval letter.

## Worked Tax Figures (2% of gross contract value)

The transfer tax is **2% of gross contract value, final**. It does not matter what the apartment originally cost. Any calculation on a profit figure is wrong.

| Contract price `P` | Tax rate | Transfer tax | Tax in tr |
|---|---|---|---|
| 5.95 ty | 2% | `round(5_950_000_000 * 0.02) = 119_000_000 VND` | **119 tr** |
| 5.50 ty | 2% | `round(5_500_000_000 * 0.02) = 110_000_000 VND` | **110 tr** |
| 5.35 ty | 2% | `round(5_350_000_000 * 0.02) = 107_000_000 VND` | **107 tr** |

Commission at these prices (1.5% base, winner-takes-all; +0.3% if notarised within 45 days) is separate and is computed in `scripts/sale_waterfall.py`.

## Mortgage-Financed Buyers

* Accepted **only on presentation of a bank pre-approval letter** (thu chap thuan tin dung).
* Close is capped at **45 calendar days** from deposit.
* **Warning:** a bank valuation coming in below the contract price can reopen the negotiation around week 4. The bank lends against its own valuation, not the contract price. If the valuation is low, the buyer may ask the seller to reduce the price or increase the down payment. This is the specific reason **cash buyers are preferred** — their close is not contingent on a third-party valuation.
* Mitigation: when accepting a mortgage buyer, keep the 5.35 ty published floor firm and treat any valuation-driven price request as a new offer subject to the negotiation ladder in `08-negotiation-ladder.md`.

## Checklist (copy and tick off per transaction)

* [ ] Written offer received and countersigned
* [ ] 5% dat coc deposit contract signed; deposit received; forfeiture clause acknowledged
* [ ] So hong original and all seller documents assembled
* [ ] Notary appointment booked (both parties)
* [ ] Sale-purchase agreement notarised; contract value `P` confirmed
* [ ] 2% transfer tax paid (119 tr at 5.95 ty / 110 tr at 5.50 ty / 107 tr at 5.35 ty)
* [ ] Registration fee paid
* [ ] So hong transfer submitted; buyer receives updated pink book
* [ ] Commission paid to winning panel agent (1.5% + 0.3% bonus if within 45 days of listing)

---
*Verify with a licensed Vietnamese notary (phong cong chung) and tax advisor before signing.*
