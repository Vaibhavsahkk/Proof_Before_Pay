# BLOCKERS

## BLOCKER 1 — No repository remote

- Exact evidence: `git remote -v` returns no entries with exit code 0.
- Impact: clean-clone reproducibility cannot be demonstrated, and reviewers have no clone URL.
- Smallest human action: provide the intended remote repository URL. Adding a remote or publishing is a consequential external action and will not be inferred.

A blocker must include exact evidence, impact, and the smallest required human action.
