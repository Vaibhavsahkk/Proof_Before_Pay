import json
import os
import decimal

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_phase2_cases():
    cases = []
    
    # Base template (from case_001)
    def get_base():
        return {
            "invoice": {
                "invoice_number": "INV-2001", "vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111", "currency": "USD", "tax_rate_percent": "10.00",
                "items": [{"item_id": "WIDGET-A", "description": "Standard Widget", "quantity": "100", "unit_price": "5.50", "line_total": "550.00"}],
                "subtotal": "550.00", "tax": "55.00", "total": "605.00"
            },
            "purchase_order": {"po_number": "PO-3001", "currency": "USD", "tax_rate_percent": "10.00", "items": [{"item_id": "WIDGET-A", "quantity": "100", "unit_price": "5.50"}]},
            "goods_receipt": {"grn_number": "GRN-4001", "items": [{"item_id": "WIDGET-A", "quantity_accepted": "100"}]},
            "vendor_master": {"vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }

    # case_007: Math Error
    c7 = get_base()
    c7["invoice"]["items"][0]["line_total"] = "600.00" # Intentionally wrong (100 * 5.50 != 600)
    cases.append({
        "id": "case_007",
        "truth": {"expected_recommendation": "HOLD", "expected_findings": ["Math Error"]},
        "public": c7
    })

    # case_008: Currency Mismatch
    c8 = get_base()
    c8["purchase_order"]["currency"] = "EUR"
    # Since Invoice is USD and PO is EUR, we trigger both Currency Mismatch and Invalid Currency
    cases.append({
        "id": "case_008",
        "truth": {"expected_recommendation": "HOLD", "expected_findings": ["Currency Mismatch", "Invalid Currency"]},
        "public": c8
    })

    # case_009: Vendor Identity Mismatch
    c9 = get_base()
    c9["invoice"]["vendor_name"] = "SYNTHETIC WIDGETS" # Missing LLC
    cases.append({
        "id": "case_009",
        "truth": {"expected_recommendation": "INVESTIGATE", "expected_findings": ["Vendor Identity Mismatch"]},
        "public": c9
    })

    # case_010: Missing PO Line ID
    c10 = get_base()
    c10["invoice"]["items"].append({"item_id": "WIDGET-EXTRA", "description": "Extra Widget", "quantity": "10", "unit_price": "10.00", "line_total": "100.00"})
    c10["invoice"]["subtotal"] = "650.00"
    c10["invoice"]["tax"] = "65.00"
    c10["invoice"]["total"] = "715.00"
    c10["goods_receipt"]["items"].append({"item_id": "WIDGET-EXTRA", "quantity_accepted": "10"})
    cases.append({
        "id": "case_010",
        "truth": {"expected_recommendation": "INVESTIGATE", "expected_findings": ["Missing PO Line ID"]},
        "public": c10
    })

    # case_011: Missing Vendor Master
    c11 = get_base()
    c11["vendor_master"] = None
    cases.append({
        "id": "case_011",
        "truth": {"expected_recommendation": "INVESTIGATE", "expected_findings": ["Missing Vendor Master"]},
        "public": c11
    })

    # case_012: Verified Bank Change -> PAY
    c12 = get_base()
    c12["invoice"]["bank_account"] = "ACC-2222"
    c12["bank_change_evidence"] = {
        "old_bank_account": "ACC-1111",
        "new_bank_account": "ACC-2222",
        "approval_status": "APPROVED",
        "verified_by": "System"
    }
    cases.append({
        "id": "case_012",
        "truth": {"expected_recommendation": "PAY", "expected_findings": []},
        "public": c12
    })

    for c in cases:
        c['public']['case_id'] = c['id']
        c['truth']['case_id'] = c['id']
        write_json(f"data/cases/public/{c['id']}.json", c['public'])
        write_json(f"data/cases/ground_truth/{c['id']}.json", c['truth'])

if __name__ == '__main__':
    generate_phase2_cases()
    print("Successfully generated Phase 2 cases (007-012).")
