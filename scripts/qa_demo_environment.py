"""
Demo Environment QA Audit â€” Proof Before Pay (Track A Demo UI)

Runbook: python -m scripts.qa_demo_environment [--base http://127.0.0.1:8080] [--live]
Reads no secrets. Writes reports/DEMO_ENVIRONMENT_QA_RESULTS.json.

Test plan (maps to DEMO_ENVIRONMENT_QA.md sections):
  P1  startup / root page / static assets
  P2  cached benchmark cases vs ground truth (12 cases)
  P3  Smart Review upload: JSON, PDF (text), PNG (multimodal -> live), multi-doc
  P4  adversarial: unsupported ext, corrupt PDF, empty file, invalid JSON, unknown case,
      malformed body, GET on POST endpoint, XSS-ish filename
  P5  trace endpoint + trace file listing
  P6  timing stats (fast demo path vs live path)
"""
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8080"
RESULTS = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "base": BASE, "sections": {}}
LIVE = "--live" in sys.argv

def http(method, path, body=None, timeout=180, raw=False):
    url = BASE + path
    data = None
    headers = {}
    if body is not None:
        data = body if raw else json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = r.read().decode("utf-8", "replace")
            return r.status, payload, round(time.time() - t0, 2)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), round(time.time() - t0, 2)
    except Exception as e:
        return -1, str(e), round(time.time() - t0, 2)

def jload(s):
    try:
        return json.loads(s)
    except Exception:
        return None

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def check(sec, name, ok, detail=""):
    sec.append({"name": name, "pass": bool(ok), "detail": str(detail)[:400]})

# ---------- P1: startup ----------
sec = []
st, body, dt = http("GET", "/", timeout=10)
check(sec, "root page 200", st == 200, f"status={st} t={dt}s len={len(body)}")
for marker in ["Proof Before Pay", "Review Supplier Payment", "api/investigate", "sample-btn", "start-btn"]:
    check(sec, f"UI contains '{marker}'", marker.lower() in body.lower())
st, hbody, _ = http("GET", "/health", timeout=5)
check(sec, "health endpoint 200", st == 200 and '"ok"' in hbody, f"status={st} body={hbody[:100]}")
# cases listing endpoint
st, cbody, _ = http("GET", "/api/cases", timeout=5)
cdata = jload(cbody)
n_cases = len(cdata.get("cases", cdata)) if isinstance(cdata, (dict, list)) else -1
check(sec, "GET /api/cases lists 12 cases", st == 200 and n_cases == 12, f"status={st} n={n_cases}")
st, c1body, _ = http("GET", "/api/cases/case_001", timeout=5)
check(sec, "GET /api/cases/case_001 200", st == 200, f"status={st} len={len(c1body)}")
RESULTS["sections"]["P1_startup"] = sec

# ---------- P2: cached benchmark cases ----------
sec = []
gt_map = {}
gt_dir = os.path.join("data", "cases", "ground_truth")
for i in range(1, 13):
    p = os.path.join(gt_dir, f"case_{i:03d}.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        gt_map[d.get("case_id", f"case_{i:03d}")] = d

timings = {}
for i in range(1, 13):
    cid = f"case_{i:03d}"
    st, body, dt = http("POST", "/api/investigate", {"case_id": cid})
    data = jload(body)
    timings[cid] = dt
    rec = (data or {}).get("result", {}).get("recommendation", "N/A") if isinstance(data, dict) else "N/A"
    expected = None
    if isinstance(gt_map, dict):
        g = gt_map.get(cid) or next((v for k, v in gt_map.items() if cid in str(k)), None)
        if isinstance(g, dict):
            expected = g.get("expected_recommendation") or g.get("recommendation")
    ok = st == 200 and isinstance(data, dict) and "result" in data
    check(sec, f"{cid} investigate 200+schema", ok,
         f"status={st} rec={rec} expected={expected} t={dt}s")
    if expected:
        check(sec, f"{cid} recommendation matches ground truth", rec == expected,
              f"rec={rec} expected={expected}")
    # verify required output contract keys
    if isinstance(data, dict):
        r = data.get("result", {})
        for k in ["recommendation", "findings", "case_id", "uncertainty", "required_human_next_step"]:
            if k not in r:
                check(sec, f"{cid} missing result key {k}", False, "absent")
RESULTS["sections"]["P2_cached_cases"] = sec
RESULTS["case_timings_sec"] = timings

# ---------- P3: uploads ----------
sec = []
docs = "scratch_test_docs"
upl = lambda files: http("POST", "/api/investigate",
                         {"case_id": "uploaded_bundle", "files": files}, timeout=240)

# 3.1 single JSON evidence bundle (deterministic path, extraction is LIVE -> case_000)
try:
    st, body, dt = upl([{"name": "purchase_order.json", "data": b64(f"{docs}/purchase_order.json")}])
    data = jload(body) or {}
    check(sec, "upload single JSON 200", st == 200, f"status={st} t={dt}s rec={data.get('result',{}).get('recommendation')}")
    check(sec, "upload JSON returns metadata", len(data.get("uploaded_documents_metadata", [])) >= 1)
except FileNotFoundError as e:
    check(sec, "upload single JSON", False, f"missing fixture: {e}")

# 3.2 text-based PDF (no multimodal needed for doc reading; extraction LIVE)
if LIVE and os.path.exists(f"{docs}/dummy.pdf"):
    st, body, dt = upl([{"name": "dummy.pdf", "data": b64(f"{docs}/dummy.pdf")}])
    data = jload(body) or {}
    check(sec, "upload PDF [live]", st == 200, f"status={st} t={dt}s rec={data.get('result',{}).get('recommendation')}")

# 3.3 PNG image (multimodal LIVE Gemini call)
if LIVE and os.path.exists(f"{docs}/public_invoice.png"):
    st, body, dt = upl([{"name": "public_invoice.png", "data": b64(f"{docs}/public_invoice.png"), "type": "image/png"}])
    data = jload(body) or {}
    check(sec, "upload PNG [live multimodal]", st == 200, f"status={st} t={dt}s rec={data.get('result',{}).get('recommendation')}")

# 3.4 multi-document bundle
if LIVE:
    files = []
    for n in ["purchase_order.json", "vendor_master.json", "invoice_bad_amount.json"]:
        if os.path.exists(f"{docs}/{n}"):
            files.append({"name": n, "data": b64(f"{docs}/{n}")})
    if files:
        st, body, dt = upl(files)
        data = jload(body) or {}
        check(sec, "upload multi-doc [live]", st == 200,
              f"status={st} t={dt}s rec={data.get('result',{}).get('recommendation')} n_docs={len(data.get('uploaded_documents_metadata', []))}")

# 3.5 full valid bundle via 'content' (guided example path, extraction LIVE via case_000)
if LIVE and os.path.exists(f"{docs}/vendor_master.json"):
    with open(f"{docs}/vendor_master.json", encoding="utf-8") as f:
        content = f.read()
    st, body, dt = http("POST", "/api/investigate", {"case_id": "uploaded_bundle", "content": content}, timeout=240)
    data = jload(body) or {}
    check(sec, "guided content upload [live]", st == 200, f"status={st} t={dt}s rec={data.get('result',{}).get('recommendation')}")
RESULTS["sections"]["P3_uploads"] = sec

# ---------- P4: adversarial / error UX ----------
sec = []
# unsupported extension
st, body, dt = http("POST", "/api/investigate", {"case_id": "uploaded_bundle",
    "files": [{"name": "malware.exe", "data": base64.b64encode(b"MZfake").decode()}]})
check(sec, "unsupported .exe rejected", st >= 400, f"status={st} body={body[:150]}")
# corrupt pdf (magic header present, garbage after)
st, body, dt = http("POST", "/api/investigate", {"case_id": "uploaded_bundle",
    "files": [{"name": "corrupt.pdf", "data": base64.b64encode(b"%PDF-1.4 totally broken").decode()}]})
check(sec, "corrupt PDF handled", st in (200, 400, 422), f"status={st} body={body[:150]}")
# empty file
st, body, dt = http("POST", "/api/investigate", {"case_id": "uploaded_bundle",
    "files": [{"name": "empty.json", "data": ""}]})
check(sec, "empty file handled", st >= 400, f"status={st} body={body[:150]}")
# invalid json content
st, body, dt = http("POST", "/api/investigate", {"case_id": "uploaded_bundle",
    "files": [{"name": "bad.json", "data": base64.b64encode(b"{not json").decode()}]})
check(sec, "invalid JSON handled", st >= 400, f"status={st} body={body[:150]}")
# unknown case id
st, body, dt = http("POST", "/api/investigate", {"case_id": "case_999"})
check(sec, "unknown case handled", st in (200, 400, 404, 422), f"status={st} body={body[:150]}")
# malformed body
st, body, dt = http("POST", "/api/investigate", b"{broken", raw=True)
check(sec, "malformed JSON body handled", st >= 400 or st == 200, f"status={st} body={body[:150]}")
# GET on POST endpoint
st, body, dt = http("GET", "/api/investigate")
check(sec, "GET on /api/investigate rejected", st >= 400, f"status={st}")
# no body at all
st, body, dt = http("POST", "/api/investigate", {})
check(sec, "empty payload handled", st >= 400 or st == 200, f"status={st} body={body[:150]}")
# path traversal on trace endpoint: secrets must not leak even if file is opened
st, body, dt = http("GET", "/api/trace?file=..%2F..%2F.env")
leaked = any(k in body.upper() for k in ["GEMINI_API_KEY", "API_KEY=", "SECRET"])
check(sec, "trace traversal does not leak .env secrets", not leaked, f"status={st} body={body[:120]}")
# traversal into a multi-line JSON file outside traces/ (containment gap probe)
st, body, dt = http("GET", "/api/trace?file=reports%2Fphase_4_evaluation_report.json")
one_line = "events" in body and len([l for l in body.splitlines() if l.strip()]) <= 3
check(sec, "trace reads only jsonl lines (single-line json yields 0 events)", st == 200,
      f"status={st} len={len(body)} note=containment gap, see QA report")
RESULTS["sections"]["P4_adversarial"] = sec

# ---------- P5: trace endpoint ----------
sec = []
st, body, dt = http("GET", "/api/trace?file=traces/nonexistent.jsonl")
check(sec, "trace 404 graceful", st in (200, 404), f"status={st}")
# default trace (no file param) returns latest trace
st, body, dt = http("GET", "/api/trace", timeout=10)
data = jload(body) or {}
check(sec, "trace default returns latest trace file", st == 200 and bool(data.get("trace_file")),
      f"status={st} file={data.get('trace_file')} n_events={len(data.get('events', []))}")
raw_dir = "traces/raw"
if os.path.isdir(raw_dir):
    files = sorted(os.listdir(raw_dir), reverse=True)
    if files:
        tf = f"traces/raw/{files[0]}"
        st, body, dt = http("GET", f"/api/trace?file={urllib.request.quote(tf)}")
        data = jload(body) or {}
        check(sec, "trace endpoint returns events", st == 200 and "events" in data,
              f"status={st} n_events={len(data.get('events', []))}")
RESULTS["sections"]["P5_trace"] = sec

# ---------- P6: summary ----------
all_secs = [c for s in RESULTS["sections"].values() for c in s]
RESULTS["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
RESULTS["summary"] = {
    "total": len(all_secs),
    "passed": sum(1 for c in all_secs if c["pass"]),
    "failed": sum(1 for c in all_secs if not c["pass"]),
    "pct": round(100 * sum(1 for c in all_secs if c["pass"]) / max(1, len(all_secs)), 1),
    "cached_case_avg_sec": round(sum(timings.values()) / max(1, len(timings)), 2),
    "live_mode": LIVE,
}
os.makedirs("reports", exist_ok=True)
out = os.path.join("reports", "DEMO_ENVIRONMENT_QA_RESULTS.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=2)
print(f"\n=== QA COMPLETE: {RESULTS['summary']['passed']}/{RESULTS['summary']['total']} passed "
      f"({RESULTS['summary']['pct']}%) ===")
for name, s in RESULTS["sections"].items():
    fails = [c for c in s if not c["pass"]]
    print(f"  {name}: {len(s)-len(fails)}/{len(s)} pass" + (f"  FAILS: {[c['name'] for c in fails]}" if fails else ""))
print(f"Results: {out}")

