# GROUND-TRUTH RULEBOOK (Version 1.0)

## Recommendation Precedence
Deterministic precedence for resolving multiple conditions:
1. **HOLD** (Highest)
2. **INVESTIGATE**
3. **PAY** (Lowest - requires all checks to pass)

## HOLD Conditions
- **Duplicate Invoice**: An exact duplicate of a previously paid invoice (matching invoice number and vendor identity).
- **Quantity Mismatch**: Invoice quantity is greater than the accepted Goods Receipt Note (GRN) quantity.
- **Material Contradiction**: A material unit-price, tax, subtotal, or total contradiction exists between the invoice and the purchase order (PO), exceeding the documented tolerance/rounding rules.

## INVESTIGATE Conditions
- **Missing Required Evidence**: A required piece of evidence (e.g., PO or GRN) is absent.
- **Unverified Payment Detail Change**: A payment-detail change (e.g., bank account update) lacks sufficient approved verification, without a proved contradiction.

## PAY Conditions
- All required evidence is present.
- Identities (vendor name, address, tax ID) are consistent across documents.
- Calculations (price * quantity, tax rate, subtotal, total) are mathematically correct.
- No exception (HOLD or INVESTIGATE) is triggered.

## Unambiguous Rules for Deterministic Verification
1. **Line Matching**: Line items are matched by exact item ID or exact description.
2. **Currency**: All amounts must be in the same currency. Cross-currency invoices are not supported in this version.
3. **Rounding & Tolerance**: Decimal arithmetic is used. A total mismatch of <= 0.01 is tolerated for rounding differences. Anything > 0.01 is a material contradiction.
4. **Duplicate Identity**: A duplicate is defined as matching Vendor Tax ID/Name AND Invoice Number in the prior-payment history.
5. **Vendor Identity**: Vendor Name and Tax ID on the Invoice must match the Vendor Master Record.
6. **Bank-Change Verification**: If the bank account on the invoice differs from the vendor master, there MUST be an official bank-change letter in the optional evidence. If missing, it triggers INVESTIGATE.
7. **Prohibited Terms**: Do not use words such as fraud/fraudulent as a ground-truth conclusion. Use "Duplicate Billing", "Price Contradiction", "Unverified Bank Change", etc.
