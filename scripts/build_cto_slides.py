from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
OUT = MEDIA / "cto_slides"
OUT.mkdir(exist_ok=True)

FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")
MONO = Path("C:/Windows/Fonts/consola.ttf")

def font(path, size):
    return ImageFont.truetype(str(path), size)

def wrap(text, width, f):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(candidate, font=f) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def slide(number, title, body, code=None, image=None, kicker="PROOF BEFORE PAY / CTO WALKTHROUGH"):
    canvas = Image.new("RGB", (1280, 720), "#08111f")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1280, 8), fill="#4fd1c5")
    draw.text((70, 48), kicker, fill="#7dd3fc", font=font(BOLD, 17))
    draw.text((70, 88), title, fill="#f8fafc", font=font(BOLD, 42))
    draw.line((70, 155, 1210, 155), fill="#26485b", width=2)

    if image:
        source = Image.open(MEDIA / image).convert("RGB")
        source.thumbnail((560, 430))
        x, y = 660, 205
        draw.rounded_rectangle((x - 12, y - 12, x + source.width + 12, y + source.height + 12), radius=12, fill="#102b3b", outline="#31566a", width=2)
        canvas.paste(source, (x, y))
    text_width = 530 if image else 1110
    y = 205
    for line in wrap(body, text_width, font(FONT, 24)):
        draw.text((70, y), line, fill="#d7e3ea", font=font(FONT, 24))
        y += 35
    if code:
        box_y = max(y + 20, 350)
        draw.rounded_rectangle((70, box_y, 1210, 655), radius=10, fill="#0d1d2b", outline="#31566a", width=2)
        cy = box_y + 22
        for line in code.splitlines():
            draw.text((95, cy), line, fill="#9ee7df", font=font(MONO, 20))
            cy += 27
    draw.text((70, 675), f"{number:02d}  |  evidence-led engineering, human-controlled consequences", fill="#7891a1", font=font(FONT, 15))
    canvas.save(OUT / f"chapter_{number:02d}.png")

def build_live_run_visual():
    canvas = Image.new("RGB", (1280, 720), "#071018")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1280, 8), fill="#4fd1c5")
    draw.text((70, 48), "LIVE RUN / LOCAL VERIFICATION", fill="#7dd3fc", font=font(BOLD, 17))
    draw.text((70, 88), "The repository running for real", fill="#f8fafc", font=font(BOLD, 42))
    draw.rounded_rectangle((70, 180, 1210, 605), radius=12, fill="#020609", outline="#31566a", width=2)
    lines = [
        "PS D:\\Proof Before Pay\\MICRO.1>",
        "> python -m src.main --smoke",
        "Running smoke test...",
        "Smoke test complete. Check traces directory for output.",
        "",
        "> docker compose config --services",
        "micro1_app",
        "phase1_verifier",
        "",
        "STATUS: executable path passed | runtime/verifier boundary resolved",
    ]
    y = 215
    for index, line in enumerate(lines):
        color = "#9ee7df" if index in (2, 3, 6, 7, 9) else "#d7e3ea"
        draw.text((105, y), line, fill=color, font=font(MONO, 22))
        y += 36
    draw.text((70, 675), "LIVE EVIDENCE  |  no personal documents, API keys, or private data shown", fill="#7891a1", font=font(FONT, 15))
    canvas.save(MEDIA / "live_run.png")

build_live_run_visual()

slides = [
    ("Executive overview", "What is being built and why", "Proof Before Pay is a focused investigation workflow for supplier payment exceptions. It turns scattered records into a traceable recommendation without taking payment action.", None, "github_repo.png"),
    ("The problem", "A plausible invoice is not proof", "The expensive failures are cross-document failures: duplicate billing, price contradictions, missing receipts, identity mismatch, and unverified bank changes.", None, "01_architecture.png"),
    ("Product boundary", "Useful automation with a hard stop", "The product returns PAY, HOLD, or INVESTIGATE. It never moves money, changes bank details, or declares fraud. A human owns the consequence.", "PAY    = evidence agrees\nHOLD   = contradiction found\nINVESTIGATE = proof is incomplete", None),
    ("Repository", "An executable project, not a prompt", "The public repository puts README claims next to source, schemas, tests, Docker targets, public cases, traces, and verification scripts. The repo itself is part of the evidence.", None, "github_repo.png"),
    ("Architecture", "Separate interpretation from correctness", "AI reads and explains. Deterministic tools calculate. Rules classify. Schemas validate. Traces record. Humans decide.", None, "01_architecture.png"),
    ("Request path", "From evidence intake to a review decision", "The reviewer UI accepts PDF, images, or JSON, normalizes the request, and sends it to the orchestrator. The demo uses bounded local fixtures, never personal documents.", "UI -> /api/investigate\n     -> AgentOrchestrator\n     -> trace + structured result", None),
    ("Live run", "The repository running for real", "The smoke command completes successfully, and Compose resolves both the application runtime and the separate verifier service. This is the first operational checkpoint before provider-backed review.", None, "live_run.png"),
    ("Orchestrator", "The control flow is intentionally readable", "The orchestrator is the system's spine. Its phases are visible in code and in trace events, so a reviewer can follow the decision rather than trusting a black box.", "extract -> verify -> apply_rules\n        -> explain -> validate -> escalate", None),
    ("Extraction contract", "The model cannot silently drop required facts", "LLM schemas are not always strong enough. The extractor checks item fields and invoice totals after the response, reinforces the prompt, retries, and repairs only when the evidence makes the repair deterministic.", "missing = _missing_item_fields(data)\nif missing:\n    retry_with_reinforced_contract()\n    repair_from_purchase_order()", None),
    ("Deterministic checks", "Do not ask a model to guess arithmetic", "The verifier checks totals, prices, quantities, currencies, taxes, duplicates, vendor identity, bank changes, PO matching, and GRN matching with explicit calculator and equality helpers.", "DecimalCalculator.multiply(...)\nDecimalCalculator.check_equality(...)\nRuleEvaluator.evaluate(anomalies)", None),
    ("Policy", "Conservative precedence makes uncertainty visible", "HOLD outranks INVESTIGATE, and INVESTIGATE outranks PAY. Missing evidence is recorded as skipped work instead of being hidden inside a confidence score.", "HOLD > INVESTIGATE > PAY\nmissing evidence -> human next step", None),
    ("Reviewer UI", "Every recommendation has an explanation path", "The UI keeps the recommendation, action, extracted facts, linked documents, automated checks, and audit trace in one review surface.", None, "05_result.png"),
    ("API hardening", "The reviewer surface has abuse boundaries", "The API requires X-Auth-Token, uses constant-time comparison, defaults to same-origin CORS, and caps request bodies. These controls address the actual public surface.", "secrets.compare_digest(presented, token)\n413 when body exceeds max\nCORS default: same-origin only", None),
    ("Docker boundary", "The verifier knows the truth; runtime does not", "The runtime target receives public application assets. The verifier target owns tests, manifests, evaluator code, and hidden ground truth. The runtime runs as a non-root user.", "FROM base AS verifier\nFROM base AS runtime\nUSER micro1user", None),
    ("Tests and evidence", "Claims are backed by executable checks", "The suite covers credentials, extraction, calculations, schemas, UI, recovery, manifests, and orchestration. The full Docker verification path also checks isolation and forced failures.", "pytest + phase validators\nmanifest + schema checks\ncontainer security assertions", None),
    ("Metrics with context", "Accuracy claims must name their boundary", "The accepted Phase 2 run was 100 percent on twelve synthetic cases with zero unsafe PAY. Track B's pre-fix measurement was 75 percent versus an 83.33 percent baseline; post-fix remeasurement was still pending.", "12 synthetic cases != production\nunsafe-PAY is a separate guardrail\nquota-limited remeasurement: honest pending", None),
    ("Failure modes", "Hardening responds to observed defects", "OCR fallback handles unavailable models. Missing-document guards distinguish absent evidence from extraction loss. Frozen clocks make cooldown tests deterministic. UI tests verify auth and size limits.", "retry + validation + repair\nfail closed on missing proof\nno silent optimistic fallback", None),
    ("Why this is different", "Not a generic generative AI assistant", "This system compares a bounded evidence graph, delegates correctness to deterministic code, preserves references, exposes missing checks, and stops before the consequential action.", None, "01_architecture.png"),
    ("Production honesty", "Strong core, explicit remaining work", "Before broad deployment, the service still needs owned ingress and TLS, readiness probes, metrics, centralized logs, alerting, secret rotation, rollback, and an operations runbook.", "core workflow: executable + tested\nservice operations: still to formalize", None),
    ("Closing", "Proof before payment", "AI helps interpret. Deterministic code checks. Schemas protect contracts. Traces preserve accountability. A human makes the consequential decision. That is the system in one sentence.", None, "01_architecture.png"),
]

for idx, (kicker, title, body, code, image) in enumerate(slides, 1):
    slide(idx, title, body, code, image, kicker=kicker.upper())

print(json.dumps({"slides": len(slides), "output": str(OUT)}))