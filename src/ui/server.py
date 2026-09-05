import os
import sys
import glob
import json
import re
import secrets
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any

from dotenv import load_dotenv
from src.agent.orchestrator import AgentOrchestrator
from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError

# Hardening defaults (overridable via environment):
#   PBP_UI_AUTH_TOKEN   - if set, all /api/* POST requests must present it as
#                         the X-Auth-Token header. If unset, a random
#                         per-process token is generated and printed to
#                         stdout so a local reviewer can still call the API
#                         deliberately, while random network scans fail.
#   PBP_UI_CORS_ORIGIN  - allowed cross-origin source. Defaults to
#                         same-origin (no cross-site browser access).
#   PBP_UI_MAX_BODY_BYTES - POST body cap (default 20 MiB) to stop
#                         unbounded uploads from exhausting memory.
DEFAULT_MAX_BODY_BYTES = 20 * 1024 * 1024

def _get_cors_origin() -> str:
    origin = os.environ.get("PBP_UI_CORS_ORIGIN", "")
    return origin if origin else "null"

class ReviewerAppHandler(SimpleHTTPRequestHandler):
    orchestrator = None
    auth_token = os.environ.get("PBP_UI_AUTH_TOKEN") or secrets.token_urlsafe(24)
    if not os.environ.get("PBP_UI_AUTH_TOKEN"):
        # Ephemeral token for this process lifetime only.
        print(f"[UI AUTH] No PBP_UI_AUTH_TOKEN configured; generated ephemeral API token: {auth_token}")

    @classmethod
    def get_orchestrator(cls):
        if cls.orchestrator is None:
            load_dotenv()
            cls.orchestrator = AgentOrchestrator()
        return cls.orchestrator

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", _get_cors_origin())
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Auth-Token")

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        presented = self.headers.get("X-Auth-Token", "")
        # Constant-time comparison to avoid token-byte timing leaks.
        return secrets.compare_digest(presented, self.auth_token)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/cases":
            cases = []
            files = sorted(glob.glob("data/cases/public/case_*.json"))
            for f in files:
                cid = os.path.basename(f).replace(".json", "")
                cases.append({
                    "case_id": cid,
                    "filename": f,
                    "title": f"Sample {cid.replace('_', ' ').title()}"
                })
            self._send_json({"cases": cases})
            return

        elif path.startswith("/api/cases/"):
            cid = path.replace("/api/cases/", "").strip()
            filepath = os.path.join("data", "cases", "public", f"{cid}.json")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                self._send_json({"case_id": cid, "content": content})
            else:
                self._send_json({"error": "Case file not found"}, status=404)
            return

        elif path == "/api/trace":
            query = urllib.parse.parse_qs(parsed.query)
            trace_file = query.get("file", [None])[0]
            if not trace_file:
                # Return latest trace in traces/raw/
                traces = sorted(glob.glob("traces/raw/trace_*.jsonl"), reverse=True)
                trace_file = traces[0] if traces else None

            if trace_file and os.path.exists(trace_file):
                events = []
                with open(trace_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except Exception:
                                pass
                self._send_json({"trace_file": trace_file, "events": events})
            else:
                self._send_json({"trace_file": trace_file, "events": []})
            return

        elif path == "/health":
            self._send_json({"status": "ok", "app": "Proof Before Pay"})
            return

        # Serve static HTML/assets
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        if path == "/" or path == "/index.html":
            index_path = os.path.join(static_dir, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    content = f.read()
                # Same-origin trust: the reviewer loads the UI from this
                # server itself, so the page receives the session token it
                # will need for /api/investigate. Cross-origin sites cannot
                # read this page (strict CORS), so the token is not exposed
                # to them.
                token_inject = (
                    f"<script>window.UI_AUTH_TOKEN = {json.dumps(self.auth_token)};</script>"
                ).encode("utf-8")
                content = content.replace(b"</head>", token_inject + b"</head>", 1) if b"</head>" in content else content
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/investigate":
            # Auth gate: without a valid token the request is refused before
            # any payload parsing or orchestrator work happens.
            if not self._authorized():
                self._send_json(
                    {"error": "Unauthorized: missing or invalid X-Auth-Token."},
                    status=401,
                )
                return

            try:
                length = int(self.headers.get("Content-Length", 0))
                max_body = int(os.environ.get("PBP_UI_MAX_BODY_BYTES", DEFAULT_MAX_BODY_BYTES))
                if length <= 0:
                    raise ValueError("empty request body")
                if length > max_body:
                    self._send_json(
                        {"error": f"Request body exceeds the {max_body} byte limit."},
                        status=413,
                    )
                    return
                body = self.rfile.read(length).decode("utf-8")
                req = json.loads(body)
            except Exception as e:
                self._send_json({"error": f"Invalid JSON payload: {e}"}, status=400)
                return

            raw_case_id = str(req.get("case_id", "case_000"))
            raw_evidence = req.get("raw_evidence")
            uploaded_files = req.get("files")
            single_file = req.get("file")
            uploaded_metadata = []

            # Normalize case_id to match output contract pattern ^case_\d{3}$
            match = re.search(r"case_(\d{3})", raw_case_id)
            if match:
                case_id = f"case_{match.group(1)}"
            else:
                case_id = "case_000"

            if single_file:
                if not uploaded_files:
                    uploaded_files = [single_file]
                else:
                    uploaded_files.append(single_file)

            # If documents (PDF/image/json) were uploaded
            if uploaded_files:
                try:
                    orch = self.get_orchestrator()
                    adapter = DocumentAdapter(credential_manager=orch.extractor.cred_manager)
                    raw_evidence, uploaded_metadata = adapter.process_bundle(uploaded_files)
                except DocumentProcessingError as dpe:
                    self._send_json({
                        "error": str(dpe),
                        "result": {
                            "case_id": case_id,
                            "recommendation": "INVESTIGATE",
                            "findings": ["Unreadable Document"],
                            "evidence_references": [],
                            "deterministic_calculation_references": [],
                            "missing_evidence": [],
                            "uncertainty": f"Unable to verify document: {str(dpe)}",
                            "required_human_next_step": "Human review required. Ensure uploaded PDF or image is clear and not corrupted."
                        }
                    }, status=400)
                    return
                except Exception as ex:
                    self._send_json({
                        "error": f"Document processing failed: {ex}",
                        "result": {
                            "case_id": case_id,
                            "recommendation": "INVESTIGATE",
                            "findings": ["Extraction or System Failure"],
                            "evidence_references": [],
                            "deterministic_calculation_references": [],
                            "missing_evidence": [],
                            "uncertainty": f"Document adapter failure: {str(ex)}",
                            "required_human_next_step": "Human review required due to document ingestion error."
                        }
                    }, status=500)
                    return

            # If raw_evidence is not directly provided as string, but case_id is a known public case
            elif not raw_evidence:
                filepath = os.path.join("data", "cases", "public", f"{case_id}.json")
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        raw_evidence = f.read()
                elif req.get("content"):
                    raw_evidence = json.dumps(req.get("content"))
                else:
                    self._send_json({"error": f"Case file '{raw_case_id}' not found. Please upload at least one supplier document to start the review."}, status=400)
                    return

            try:
                orch = self.get_orchestrator()
                result = orch.run_workflow(case_id, raw_evidence)
                
                extracted_data = getattr(orch, "last_extracted_data", None)
                trace_file = getattr(getattr(orch, "logger", None), "log_file", None)
                checks_performed = getattr(orch, "last_checks_performed", [])
                checks_skipped = getattr(orch, "last_checks_skipped", [])

                # Analyze trace for recovery & failover events
                recovery_info = {
                    "failover_occurred": False,
                    "pool_exhausted": False,
                    "slots": [],
                    "events": []
                }
                
                if hasattr(orch, "extractor") and hasattr(orch.extractor, "cred_manager"):
                    cm = orch.extractor.cred_manager
                    for i, c in enumerate(cm.credentials):
                        recovery_info["slots"].append({
                            "slot": i,
                            "masked_key": c.masked_key,
                            "state": c.state.value
                        })
                
                if trace_file and os.path.exists(trace_file):
                    with open(trace_file, "r", encoding="utf-8") as tf:
                        for line in tf:
                            try:
                                ev = json.loads(line.strip())
                                if ev.get("action") == "retry_wait" or "RetrySignal" in str(ev.get("error", "")):
                                    recovery_info["failover_occurred"] = True
                                    recovery_info["events"].append(ev.get("error", "Rate limit failover"))
                                if ev.get("result") == "ERROR" and "exhausted" in str(ev.get("error", "")).lower():
                                    recovery_info["pool_exhausted"] = True
                            except Exception:
                                pass

                if "All credentials exhausted" in result.get("findings", []):
                    recovery_info["pool_exhausted"] = True

                self._send_json({
                    "result": result,
                    "extracted_data": extracted_data,
                    "trace_file": trace_file,
                    "recovery_info": recovery_info,
                    "uploaded_documents_metadata": uploaded_metadata,
                    "checks_performed": checks_performed,
                    "checks_skipped": checks_skipped
                })
            except Exception as e:
                self._send_json({
                    "error": str(e),
                    "result": {
                        "case_id": case_id,
                        "recommendation": "INVESTIGATE",
                        "findings": ["System Failure"],
                        "evidence_references": [],
                        "deterministic_calculation_references": [],
                        "missing_evidence": [],
                        "uncertainty": str(e),
                        "required_human_next_step": "Human review required due to system error."
                    },
                    "recovery_info": {
                        "failover_occurred": False,
                        "pool_exhausted": True,
                        "slots": [],
                        "events": [str(e)]
                    }
                }, status=500)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

def run_server(port: int = 8080):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ReviewerAppHandler)
    print(f"Proof Before Pay Reviewer App running at http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
