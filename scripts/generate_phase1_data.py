import json
import os
from decimal import Decimal

def setup_dirs():
    os.makedirs('benchmark/schemas', exist_ok=True)
    os.makedirs('data/cases/public', exist_ok=True)
    os.makedirs('data/cases/ground_truth', exist_ok=True)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_schemas():
    # Public Evidence Bundle Schema
    public_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Public Evidence Bundle V1",
        "type": "object",
        "properties": {
            "case_id": {"type": "string"},
            "invoice": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "vendor_name": {"type": "string"},
                    "vendor_tax_id": {"type": "string"},
                    "bank_account": {"type": "string"},
                    "currency": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"},
                                "description": {"type": "string"},
                                "quantity": {"type": "string"},
                                "unit_price": {"type": "string"},
                                "line_total": {"type": "string"}
                            },
                            "required": ["item_id", "quantity", "unit_price"]
                        }
                    },
                    "subtotal": {"type": "string"},
                    "tax": {"type": "string"},
                    "total": {"type": "string"}
                },
                "required": ["invoice_number", "vendor_name", "total"]
            },
            "purchase_order": {"type": ["object", "null"]},
            "goods_receipt": {"type": ["object", "null"]},
            "vendor_master": {"type": ["object", "null"]},
            "prior_payment_history": {"type": ["array", "null"]},
            "bank_change_evidence": {"type": ["object", "null"]}
        },
        "required": ["case_id", "invoice"]
    }
    write_json('benchmark/schemas/public_evidence_bundle.json', public_schema)

    # Ground Truth Schema
    gt_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Ground Truth V1",
        "type": "object",
        "properties": {
            "case_id": {"type": "string"},
            "expected_recommendation": {"type": "string", "enum": ["PAY", "HOLD", "INVESTIGATE"]},
            "expected_exception_name": {"type": ["string", "null"]}
        },
        "required": ["case_id", "expected_recommendation"]
    }
    write_json('benchmark/schemas/ground_truth.json', gt_schema)

    # Output Contract Schema
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Output Contract V1",
        "type": "object",
        "properties": {
            "case_id": {"type": "string"},
            "recommendation": {"type": "string", "enum": ["PAY", "HOLD", "INVESTIGATE"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "evidence_references": {"type": "array", "items": {"type": "string"}},
            "deterministic_calculation_references": {"type": "array", "items": {"type": "string"}},
            "missing_evidence": {"type": "array", "items": {"type": "string"}},
            "uncertainty": {"type": "string"},
            "required_human_next_step": {"type": "string"}
        },
        "required": ["case_id", "recommendation", "findings"]
    }
    write_json('benchmark/schemas/output_contract.json', output_schema)

def generate_cases():
    cases = []
    # Case 1: Clean Full Match => PAY
    cases.append({
        "id": "case_1_pay",
        "truth": {"expected_recommendation": "PAY", "expected_exception_name": None},
        "public": {
            "invoice": {
                "invoice_number": "INV-1001", "vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111", "currency": "USD",
                "items": [{"item_id": "WIDGET-A", "description": "Standard Widget", "quantity": "100", "unit_price": "5.50", "line_total": "550.00"}],
                "subtotal": "550.00", "tax": "55.00", "total": "605.00"
            },
            "purchase_order": {"po_number": "PO-2001", "items": [{"item_id": "WIDGET-A", "quantity": "100", "unit_price": "5.50"}]},
            "goods_receipt": {"grn_number": "GRN-3001", "items": [{"item_id": "WIDGET-A", "quantity_accepted": "100"}]},
            "vendor_master": {"vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 2: Exact duplicate => HOLD
    cases.append({
        "id": "case_2_duplicate_hold",
        "truth": {"expected_recommendation": "HOLD", "expected_exception_name": "Duplicate Billing"},
        "public": {
            "invoice": {
                "invoice_number": "INV-1002", "vendor_name": "FAKECORP INC", "vendor_tax_id": "TX-8888", "bank_account": "ACC-2222", "currency": "USD",
                "items": [{"item_id": "SERVICE-B", "description": "Consulting", "quantity": "10", "unit_price": "100.00", "line_total": "1000.00"}],
                "subtotal": "1000.00", "tax": "0.00", "total": "1000.00"
            },
            "purchase_order": {"po_number": "PO-2002", "items": [{"item_id": "SERVICE-B", "quantity": "10", "unit_price": "100.00"}]},
            "goods_receipt": {"grn_number": "GRN-3002", "items": [{"item_id": "SERVICE-B", "quantity_accepted": "10"}]},
            "vendor_master": {"vendor_name": "FAKECORP INC", "vendor_tax_id": "TX-8888", "bank_account": "ACC-2222"},
            "prior_payment_history": [{"invoice_number": "INV-1002", "vendor_tax_id": "TX-8888", "amount": "1000.00", "payment_date": "2025-01-15"}],
            "bank_change_evidence": None
        }
    })

    # Case 3: Invoice quantity exceeds accepted GRN quantity => HOLD
    cases.append({
        "id": "case_3_qty_mismatch_hold",
        "truth": {"expected_recommendation": "HOLD", "expected_exception_name": "Quantity Mismatch"},
        "public": {
            "invoice": {
                "invoice_number": "INV-1003", "vendor_name": "MOCK SUPPLIES LTD", "vendor_tax_id": "TX-7777", "bank_account": "ACC-3333", "currency": "USD",
                "items": [{"item_id": "PART-C", "description": "Metal Part", "quantity": "500", "unit_price": "2.00", "line_total": "1000.00"}],
                "subtotal": "1000.00", "tax": "100.00", "total": "1100.00"
            },
            "purchase_order": {"po_number": "PO-2003", "items": [{"item_id": "PART-C", "quantity": "500", "unit_price": "2.00"}]},
            "goods_receipt": {"grn_number": "GRN-3003", "items": [{"item_id": "PART-C", "quantity_accepted": "450"}]},
            "vendor_master": {"vendor_name": "MOCK SUPPLIES LTD", "vendor_tax_id": "TX-7777", "bank_account": "ACC-3333"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 4: Material price contradiction => HOLD (combine multiple documents: invoice vs PO)
    cases.append({
        "id": "case_4_price_contradiction_hold",
        "truth": {"expected_recommendation": "HOLD", "expected_exception_name": "Price Contradiction"},
        "public": {
            "invoice": {
                "invoice_number": "INV-1004", "vendor_name": "PSEUDO TECHNOLOGIES", "vendor_tax_id": "TX-6666", "bank_account": "ACC-4444", "currency": "USD",
                "items": [{"item_id": "TECH-D", "description": "Server Rack", "quantity": "5", "unit_price": "5000.00", "line_total": "25000.00"}],
                "subtotal": "25000.00", "tax": "2500.00", "total": "27500.00"
            },
            "purchase_order": {"po_number": "PO-2004", "items": [{"item_id": "TECH-D", "quantity": "5", "unit_price": "4000.00"}]},
            "goods_receipt": {"grn_number": "GRN-3004", "items": [{"item_id": "TECH-D", "quantity_accepted": "5"}]},
            "vendor_master": {"vendor_name": "PSEUDO TECHNOLOGIES", "vendor_tax_id": "TX-6666", "bank_account": "ACC-4444"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 5: Payment detail change with incomplete/ambiguous verification => INVESTIGATE
    cases.append({
        "id": "case_5_bank_change_investigate",
        "truth": {"expected_recommendation": "INVESTIGATE", "expected_exception_name": "Unverified Bank Change"},
        "public": {
            "invoice": {
                "invoice_number": "INV-1005", "vendor_name": "TESTAMENT SERVICES", "vendor_tax_id": "TX-5555", "bank_account": "ACC-9999", "currency": "USD",
                "items": [{"item_id": "SERV-E", "description": "Cleaning", "quantity": "1", "unit_price": "200.00", "line_total": "200.00"}],
                "subtotal": "200.00", "tax": "0.00", "total": "200.00"
            },
            "purchase_order": {"po_number": "PO-2005", "items": [{"item_id": "SERV-E", "quantity": "1", "unit_price": "200.00"}]},
            "goods_receipt": {"grn_number": "GRN-3005", "items": [{"item_id": "SERV-E", "quantity_accepted": "1"}]},
            "vendor_master": {"vendor_name": "TESTAMENT SERVICES", "vendor_tax_id": "TX-5555", "bank_account": "ACC-5555"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    for c in cases:
        c['public']['case_id'] = c['id']
        c['truth']['case_id'] = c['id']
        write_json(f"data/cases/public/{c['id']}.json", c['public'])
        write_json(f"data/cases/ground_truth/{c['id']}.json", c['truth'])

if __name__ == '__main__':
    setup_dirs()
    generate_schemas()
    generate_cases()
    print("Successfully generated Phase 1 schemas and cases.")
