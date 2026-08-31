import urllib.request
import json
import base64
import sys

def run_test(name, file_paths):
    print(f"\n--- Running Test: {name} ---")
    documents = []
    for fp in file_paths:
        with open(fp, "rb") as f:
            content = f.read()
            b64 = base64.b64encode(content).decode('utf-8')
            if fp.endswith(".json"):
                documents.append({"type": "application/json", "name": fp, "data": f"data:application/json;base64,{b64}"})
            elif fp.endswith(".png"):
                documents.append({"type": "image/png", "name": fp, "data": f"data:image/png;base64,{b64}"})
            elif fp.endswith(".txt") or fp.endswith(".pdf"):
                documents.append({"type": "application/pdf" if fp.endswith('.pdf') else "text/plain", "name": fp, "data": f"data:application/pdf;base64,{b64}"})

    req_data = {"files": documents}
    req = urllib.request.Request("http://127.0.0.1:8080/api/investigate", data=json.dumps(req_data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            print("Full response:", json.dumps(res, indent=2))
            print("Recommendation:", res.get("result", {}).get("recommendation"))
            print("Total Findings:", len(res.get("result", {}).get("findings", [])))
            for f in res.get("result", {}).get("findings", []):
                print(f" - {f}")
            print("Missing Evidence:", res.get("result", {}).get("missing_evidence", []))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}:", e.read().decode('utf-8'))
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    # Test 1: Positive Control (Invoice + PO + Vendor)
    run_test("Positive Control", ["scratch_test_docs/public_invoice.png", "scratch_test_docs/purchase_order.json", "scratch_test_docs/vendor_master.json"])
    
    # Test 2: Negative Control (Price Mismatch)
    run_test("Price Mismatch", ["scratch_test_docs/invoice_bad_amount.json", "scratch_test_docs/purchase_order.json", "scratch_test_docs/vendor_master.json"])

    # Test 3: Missing Evidence (Invoice only)
    run_test("Invoice Only (Missing PO/Vendor)", ["scratch_test_docs/invoice_bad_amount.json"])
    
    # Test 4: Image test (Public invoice image + PO + vendor)
    run_test("Image Invoice", ["scratch_test_docs/public_invoice.png", "scratch_test_docs/purchase_order.json", "scratch_test_docs/vendor_master.json"])

    # Test 5: Duplicate Document Test
    run_test("Duplicate Invoice", ["scratch_test_docs/invoice_bad_amount.json", "scratch_test_docs/invoice_bad_amount.json"])

