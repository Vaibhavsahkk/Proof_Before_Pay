# GROUND-TRUTH RULEBOOK (Version 1.2)

## Recommendation Precedence
Deterministic precedence for resolving multiple conditions (first match wins):
1. **HOLD** (Highest)
2. **INVESTIGATE**
3. **PAY** (Lowest - requires all checks to pass)

## HOLD Conditions
- **Duplicate Billing**: Exact match of `vendor_tax_id`, `invoice_number`, and total `amount` in `prior_payment_history`.
- **Quantity Mismatch**: Any invoice item's `quantity` is greater than the accepted `quantity_accepted` in the GRN (matched by exact `item_id`).
- **Price Contradiction**: Any invoice item's `unit_price` differs from the PO's `unit_price` by more than 0.01 (matched by exact `item_id`).
- **Currency Mismatch**: Invoice `currency` differs from PO `currency`.
- **Tax Rate Contradiction**: Invoice `tax_rate_percent` differs from PO `tax_rate_percent`.
- **Math Error**:
  - `quantity * unit_price` differs from `line_total` by > 0.01.
  - Sum of `line_total`s differs from `subtotal` by > 0.01.
  - `subtotal * (tax_rate_percent / 100)` differs from `tax` by > 0.01.
  - `subtotal + tax` differs from `total` by > 0.01.

## INVESTIGATE Conditions
- **Missing Vendor Master**: The `vendor_master` object is null.
- **Vendor Identity Mismatch**: Invoice `vendor_name` or `vendor_tax_id` does not exactly match the Vendor Master Record.
- **Unverified Bank Change**: Invoice `bank_account` differs from Vendor Master `bank_account`, unless all three verification conditions hold: `old_bank_account` matches the Vendor Master account, `new_bank_account` matches the Invoice account, and `approval_status` is exactly `APPROVED`.
- **Missing PO**: The `purchase_order` object is null.
- **Missing GRN**: The `goods_receipt` object is null.
- **Duplicate Line ID**: Duplicate `item_id` values in the Invoice, PO, or GRN.
- **Missing PO Line ID**: An invoice `item_id` has no matching PO line.
- **Missing GRN Line ID**: An invoice `item_id` has no matching GRN line.

## PAY Conditions
- All required evidence is present.
- Identities are consistent.
- Math checks pass exactly (with rounding tolerance).
- No HOLD or INVESTIGATE conditions triggered.

## Unambiguous Execution Rules
1. **Line Matching**: Match by exact string `item_id`. Duplicate IDs and missing PO/GRN line matches produce the INVESTIGATE findings listed above.
2. **Currency**: Must be exactly "USD".
3. **Decimal Rules**: All math must use exact Decimal arithmetic with `ROUND_HALF_UP` and a scale of 2 (0.01). Tolerance for matching is strictly `<= 0.01`.
4. **Vocabulary**: Recommendations are strictly advisory. Never label a supplier "fraudulent" or "fraud". Use the exact exception names provided above.
