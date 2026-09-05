# Proof Before Pay Explainer Media

Generated on 2026-09-06 from the current repository state.

## Deliverables

- `architecture.svg` - code-backed system architecture image.
- `architecture.png` - raster architecture image when a local rasterizer is available.
- `proof_before_pay_explainer.mp4` - approximately five-minute narrated explainer.
- `proof_before_pay_3d_explainer.mp4` - enhanced narrated explainer with a rendered Blender 3D architecture chapter.
- `proof_before_pay_sync_verified.mp4` - paragraph-timed version with measured narration chapters and verified visual checkpoints.
- `proof_before_pay_cto_explainer.mp4` - 7-minute CTO/hiring-manager walkthrough with public GitHub context, key code decisions, evidence, and Blender architecture motion.
- `proof_before_pay_cto_explainer_live.mp4` - local-only final version with the real smoke and Compose live-run chapter added.
- `cto_narration.txt` - narration source for the CTO walkthrough.
- `../scripts/build_cto_slides.py` - reproducible code/evidence slide generator.
- `blender_architecture_3d.mp4` - standalone 15-second narrated Blender architecture clip.
- `../scripts/blender_explainer.py` - reproducible Blender scene and animation script.
- `01_architecture.png` through `07_audit_trace.png` - storyboard evidence frames.
- `narration.txt` - narration source text.
- `../scripts/record_explainer.py` - reproducible browser capture harness.

## Recording boundary

The browser capture uses the real reviewer UI and real UI state transitions. Its
`/api/investigate` and `/api/trace` responses are local, clearly bounded demo
fixtures so the recording does not require provider credentials or claim a live
LLM run. The architecture labels and narration are grounded in the repository's
current `AgentOrchestrator`, reviewer UI, Docker targets, and safety boundaries.

## Sync verification

The sync-verified video uses 16 measured narration chapters. The source audio
duration is `309.169s`; the muxed video is `309.167s`, within roughly `0.002s`.
Checkpoint frames were reviewed at the 3D opening, architecture, intake, case
selection, progress, live UI, HOLD result, automated checks, and audit trace
sections against the narration chapter map.

The CTO walkthrough uses 19 measured chapters. Its source narration is
`428.847s`; the final muxed video is `428.800s`, within roughly `0.047s`.
It intentionally shows only public repository content, bounded demo evidence,
and non-secret code excerpts.

The live-run version uses 20 measured chapters. Its source narration is
`447.027s`; the final muxed video is `446.967s`, within roughly `0.060s`.
The video files are intentionally kept on the local machine and are not
tracked or uploaded to GitHub. The player expects the local MP4 to exist.

Intermediate audio, segment files, and raw browser recordings are local build
artifacts and are intentionally excluded from the repository package.