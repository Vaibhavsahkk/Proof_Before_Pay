# Proof Before Pay Explainer Media

Generated on 2026-09-06 from the current repository state.

## Deliverables

- `architecture.svg` - code-backed system architecture image.
- `architecture.png` - raster architecture image when a local rasterizer is available.
- `proof_before_pay_explainer.mp4` - approximately five-minute narrated explainer.
- `01_architecture.png` through `07_audit_trace.png` - storyboard evidence frames.
- `narration.txt` - narration source text.
- `../scripts/record_explainer.py` - reproducible browser capture harness.

## Recording boundary

The browser capture uses the real reviewer UI and real UI state transitions. Its
`/api/investigate` and `/api/trace` responses are local, clearly bounded demo
fixtures so the recording does not require provider credentials or claim a live
LLM run. The architecture labels and narration are grounded in the repository's
current `AgentOrchestrator`, reviewer UI, Docker targets, and safety boundaries.

Intermediate audio, segment files, and raw browser recordings are local build
artifacts and are intentionally excluded from the repository package.