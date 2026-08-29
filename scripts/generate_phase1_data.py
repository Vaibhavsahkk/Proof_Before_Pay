import json
import os

def setup_dirs():
    os.makedirs('benchmark/schemas', exist_ok=True)
    os.makedirs('data/cases/public', exist_ok=True)
    os.makedirs('data/cases/ground_truth', exist_ok=True)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

DECIMAL_PATTERN = "^-?\\d+\\.\\d{2}$"

def generate_schemas():
    # Public Evidence Bundle Schema
    public_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Public Evidence Bundle V1.2",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "case_id": {"type": "string"},
            "invoice": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "invoice_number": {"type": "string"},
                    "vendor_name": {"type": "string"},
                    "vendor_tax_id": {"type": "string"},
                    "bank_account": {"type": "string"},
                    "currency": {"type": "string", "enum": ["USD"]},
                    "tax_rate_percent": {"type": "string", "pattern": DECIMAL_PATTERN},
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "item_id": {"type": "string", "minLength": 1},
                                "description": {"type": "string"},
                                "quantity": {"type": "string", "pattern": "^\\d+$"},
                                "unit_price": {"type": "string", "pattern": DECIMAL_PATTERN},
                                "line_total": {"type": "string", "pattern": DECIMAL_PATTERN}
                            },
                            "required": ["item_id", "description", "quantity", "unit_price", "line_total"]
                        }
                    },
                    "subtotal": {"type": "string", "pattern": DECIMAL_PATTERN},
                    "tax": {"type": "string", "pattern": DECIMAL_PATTERN},
                    "total": {"type": "string", "pattern": DECIMAL_PATTERN}
                },
                "required": ["invoice_number", "vendor_name", "vendor_tax_id", "bank_account", "currency", "tax_rate_percent", "items", "subtotal", "tax", "total"]
            },
            "purchase_order": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "po_number": {"type": "string"},
                    "currency": {"type": "string", "enum": ["USD"]},
                    "tax_rate_percent": {"type": "string", "pattern": DECIMAL_PATTERN},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "item_id": {"type": "string", "minLength": 1},
                                "quantity": {"type": "string", "pattern": "^\\d+$"},
                                "unit_price": {"type": "string", "pattern": DECIMAL_PATTERN}
                            },
                            "required": ["item_id", "quantity", "unit_price"]
                        }
                    }
                },
                "required": ["po_number", "currency", "tax_rate_percent", "items"]
            },
            "goods_receipt": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "grn_number": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "item_id": {"type": "string", "minLength": 1},
                                "quantity_accepted": {"type": "string", "pattern": "^\\d+$"}
                            },
                            "required": ["item_id", "quantity_accepted"]
                        }
                    }
                },
                "required": ["grn_number", "items"]
            },
            "vendor_master": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "vendor_name": {"type": "string"},
                    "vendor_tax_id": {"type": "string"},
                    "bank_account": {"type": "string"}
                },
                "required": ["vendor_name", "vendor_tax_id", "bank_account"]
            },
            "prior_payment_history": {
                "type": ["array", "null"],
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "invoice_number": {"type": "string"},
                        "vendor_tax_id": {"type": "string"},
                        "amount": {"type": "string", "pattern": DECIMAL_PATTERN},
                        "payment_date": {"type": "string"}
                    },
                    "required": ["invoice_number", "vendor_tax_id", "amount", "payment_date"]
                }
            },
            "bank_change_evidence": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "old_bank_account": {"type": "string"},
                    "new_bank_account": {"type": "string"},
                    "approval_status": {"type": "string", "enum": ["APPROVED", "PENDING", "REJECTED"]},
                    "verified_by": {"type": "string", "minLength": 1}
                },
                "required": ["old_bank_account", "new_bank_account", "approval_status", "verified_by"]
            }
        },
        "required": ["case_id", "invoice", "purchase_order", "goods_receipt", "vendor_master", "prior_payment_history", "bank_change_evidence"]
    }
    write_json('benchmark/schemas/public_evidence_bundle.json', public_schema)

    # Ground Truth Schema
    gt_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Ground Truth V1.2",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "case_id": {"type": "string"},
            "expected_recommendation": {"type": "string", "enum": ["PAY", "HOLD", "INVESTIGATE"]},
            "expected_findings": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["case_id", "expected_recommendation", "expected_findings"]
    }
    write_json('benchmark/schemas/ground_truth.json', gt_schema)

    # Output Contract Schema
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Output Contract V1.2",
        "type": "object",
        "additionalProperties": False,
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
        "required": [
            "case_id", "recommendation", "findings", "evidence_references",
            "deterministic_calculation_references", "missing_evidence", "uncertainty",
            "required_human_next_step"
        ]
    }
    write_json('benchmark/schemas/output_contract.json', output_schema)

def generate_cases():
    cases = []
    # Case 1: Clean Full Match => PAY
    cases.append({
        "id": "case_001",
        "truth": {"expected_recommendation": "PAY", "expected_findings": []},
        "public": {
            "invoice": {
                "invoice_number": "INV-1001", "vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111", "currency": "USD", "tax_rate_percent": "10.00",
                "items": [{"item_id": "WIDGET-A", "description": "Standard Widget", "quantity": "100", "unit_price": "5.50", "line_total": "550.00"}],
                "subtotal": "550.00", "tax": "55.00", "total": "605.00"
            },
            "purchase_order": {"po_number": "PO-2001", "currency": "USD", "tax_rate_percent": "10.00", "items": [{"item_id": "WIDGET-A", "quantity": "100", "unit_price": "5.50"}]},
            "goods_receipt": {"grn_number": "GRN-3001", "items": [{"item_id": "WIDGET-A", "quantity_accepted": "100"}]},
            "vendor_master": {"vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 2: Exact duplicate => HOLD
    cases.append({
        "id": "case_002",
        "truth": {"expected_recommendation": "HOLD", "expected_findings": ["Duplicate Billing"]},
        "public": {
            "invoice": {
                "invoice_number": "INV-1002", "vendor_name": "FAKECORP INC", "vendor_tax_id": "TX-8888", "bank_account": "ACC-2222", "currency": "USD", "tax_rate_percent": "0.00",
                "items": [{"item_id": "SERVICE-B", "description": "Consulting", "quantity": "10", "unit_price": "100.00", "line_total": "1000.00"}],
                "subtotal": "1000.00", "tax": "0.00", "total": "1000.00"
            },
            "purchase_order": {"po_number": "PO-2002", "currency": "USD", "tax_rate_percent": "0.00", "items": [{"item_id": "SERVICE-B", "quantity": "10", "unit_price": "100.00"}]},
            "goods_receipt": {"grn_number": "GRN-3002", "items": [{"item_id": "SERVICE-B", "quantity_accepted": "10"}]},
            "vendor_master": {"vendor_name": "FAKECORP INC", "vendor_tax_id": "TX-8888", "bank_account": "ACC-2222"},
            "prior_payment_history": [{"invoice_number": "INV-1002", "vendor_tax_id": "TX-8888", "amount": "1000.00", "payment_date": "2025-01-15"}],
            "bank_change_evidence": None
        }
    })

    # Case 3: Invoice quantity exceeds accepted GRN quantity => HOLD
    cases.append({
        "id": "case_003",
        "truth": {"expected_recommendation": "HOLD", "expected_findings": ["Quantity Mismatch"]},
        "public": {
            "invoice": {
                "invoice_number": "INV-1003", "vendor_name": "MOCK SUPPLIES LTD", "vendor_tax_id": "TX-7777", "bank_account": "ACC-3333", "currency": "USD", "tax_rate_percent": "10.00",
                "items": [{"item_id": "PART-C", "description": "Metal Part", "quantity": "500", "unit_price": "2.00", "line_total": "1000.00"}],
                "subtotal": "1000.00", "tax": "100.00", "total": "1100.00"
            },
            "purchase_order": {"po_number": "PO-2003", "currency": "USD", "tax_rate_percent": "10.00", "items": [{"item_id": "PART-C", "quantity": "500", "unit_price": "2.00"}]},
            "goods_receipt": {"grn_number": "GRN-3003", "items": [{"item_id": "PART-C", "quantity_accepted": "450"}]},
            "vendor_master": {"vendor_name": "MOCK SUPPLIES LTD", "vendor_tax_id": "TX-7777", "bank_account": "ACC-3333"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 4: Material price contradiction => HOLD
    cases.append({
        "id": "case_004",
        "truth": {"expected_recommendation": "HOLD", "expected_findings": ["Price Contradiction"]},
        "public": {
            "invoice": {
                "invoice_number": "INV-1004", "vendor_name": "PSEUDO TECHNOLOGIES", "vendor_tax_id": "TX-6666", "bank_account": "ACC-4444", "currency": "USD", "tax_rate_percent": "10.00",
                "items": [{"item_id": "TECH-D", "description": "Server Rack", "quantity": "5", "unit_price": "5000.00", "line_total": "25000.00"}],
                "subtotal": "25000.00", "tax": "2500.00", "total": "27500.00"
            },
            "purchase_order": {"po_number": "PO-2004", "currency": "USD", "tax_rate_percent": "10.00", "items": [{"item_id": "TECH-D", "quantity": "5", "unit_price": "4000.00"}]},
            "goods_receipt": {"grn_number": "GRN-3004", "items": [{"item_id": "TECH-D", "quantity_accepted": "5"}]},
            "vendor_master": {"vendor_name": "PSEUDO TECHNOLOGIES", "vendor_tax_id": "TX-6666", "bank_account": "ACC-4444"},
            "prior_payment_history": [],
            "bank_change_evidence": None
        }
    })

    # Case 5: Payment detail change with incomplete/ambiguous verification => INVESTIGATE
    cases.append({
        "id": "case_005",
        "truth": {"expected_recommendation": "INVESTIGATE", "expected_findings": ["Unverified Bank Change"]},
        "public": {
            "invoice": {
                "invoice_number": "INV-1005", "vendor_name": "TESTAMENT SERVICES", "vendor_tax_id": "TX-5555", "bank_account": "ACC-9999", "currency": "USD", "tax_rate_percent": "0.00",
                "items": [{"item_id": "SERV-E", "description": "Cleaning", "quantity": "1", "unit_price": "200.00", "line_total": "200.00"}],
                "subtotal": "200.00", "tax": "0.00", "total": "200.00"
            },
            "purchase_order": {"po_number": "PO-2005", "currency": "USD", "tax_rate_percent": "0.00", "items": [{"item_id": "SERV-E", "quantity": "1", "unit_price": "200.00"}]},
            "goods_receipt": {"grn_number": "GRN-3005", "items": [{"item_id": "SERV-E", "quantity_accepted": "1"}]},
            "vendor_master": {"vendor_name": "TESTAMENT SERVICES", "vendor_tax_id": "TX-5555", "bank_account": "ACC-5555"},
            "prior_payment_history": [],
            "bank_change_evidence": {
                "old_bank_account": "ACC-5555",
                "new_bank_account": "ACC-9999",
                "approval_status": "PENDING",
                "verified_by": "System"
            }
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
