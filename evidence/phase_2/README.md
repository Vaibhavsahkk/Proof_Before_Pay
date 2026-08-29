# Phase 2 Evidence

**STATUS: VALID portable baseline verified from an exact remote clean clone; ready for external review.**

## Accepted decision evidence

- Run: `runs/run_20260829_154058_02e9416b/`
- Source commit: `7512b9eace0e43045a406bc7cf46d76e1eb21ea7`
- Requested/returned model: `gemini-3.6-flash`
- Manifest: `phase2-baseline-run-v2`
- Input hash mode: `utf8-text-normalized-lf`
- Evaluator status: `VALID`
- Clean-clone candidate: `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c`
- Clean-clone evidence: `final_clean_clone_execution.txt`
- Clean-clone evidence SHA-256: `D720522023C2ACBB17399E1F47A976FD2894FBBD1E4E3AD761518E5E159D2D15`

The clean-clone harness re-ran 35 focused tests, verified the committed report deterministically, ran both 81-test Docker pipelines, checked Git cleanliness, and removed its exact temporary resources. The normalized log is machine-captured evidence, not a byte-for-byte terminal transcript.

## Metrics

- Exact case-level recommendation accuracy: 100% (6/6)
- Findings correctness: 100% (6/6)
- Schema validity: 100% (6/6)
- Unsafe-PAY rate: 0% (0/5 non-PAY ground-truth cases)
- Total runtime: 181.891378800006 seconds
- Prompt tokens: 11,710
- Candidate tokens: 1,439
- Cost: UNKNOWN

These results apply only to the frozen six-case synthetic benchmark. They are not a production-performance claim.

## Historical and superseded evidence

- `runs/run_20260829_151625_260ba740/`: INVALID, six HTTP 404 provider responses.
- `runs/run_20260829_152146_25ba3699/`: INVALID, six HTTP 429 zero-quota responses.
- `runs/run_20260829_152514_caab4d45/`: superseded. Its v1 raw-byte input hashes were checkout-line-ending dependent and failed clean-clone verification.
- `superseded_clean_clone_failure_c21cb36.txt`: the observed portability failure that caused manifest v2.
- `superseded_clean_clone_invalid_sha_attempt.txt`: a command-input error using a guessed nonexistent SHA; not a product failure.
- `scaffold_*`: earlier API-independent scaffold evidence.

No superseded or INVALID run contributes to the accepted metrics.

## Offline verification

```powershell
python -m eval.evaluate_baseline evidence/phase_2/runs/run_20260829_154058_02e9416b --verify-existing
```

This verifies the existing report without making an API call or modifying the run.
