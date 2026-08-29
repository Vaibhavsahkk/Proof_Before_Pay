FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217 AS base

WORKDIR /app

COPY requirements.lock requirements.txt ./
RUN pip install --no-cache-dir -r requirements.lock

RUN useradd -m micro1user && chown micro1user:micro1user /app

# Evaluator-only image. This image owns the frozen answer key and validation
# code; it is never used as the agent/runtime service.
FROM base AS verifier
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY --chown=micro1user:micro1user src/ ./src/
COPY --chown=micro1user:micro1user tests/ ./tests/
COPY --chown=micro1user:micro1user scripts/ ./scripts/
COPY --chown=micro1user:micro1user benchmark/ ./benchmark/
COPY --chown=micro1user:micro1user data/ ./data/
COPY --chown=micro1user:micro1user baseline/ ./baseline/
COPY --chown=micro1user:micro1user eval/ ./eval/
COPY --chown=micro1user:micro1user evidence/phase_1/SHA256_MANIFEST.txt ./evidence/phase_1/SHA256_MANIFEST.txt
COPY --chown=micro1user:micro1user pytest.ini Dockerfile .dockerignore docker-compose.yml ./
USER micro1user
CMD ["python", "-m", "pytest", "-q"]

# Agent/runtime image. The explicit allowlist prevents ground truth,
# evaluator code, tests, evidence, and reports from entering this image.
FROM base AS runtime
COPY --chown=micro1user:micro1user src/ ./src/
COPY --chown=micro1user:micro1user benchmark/RULEBOOK.md ./benchmark/RULEBOOK.md
COPY --chown=micro1user:micro1user benchmark/schemas/public_evidence_bundle.json benchmark/schemas/output_contract.json ./benchmark/schemas/
COPY --chown=micro1user:micro1user data/cases/public/ ./data/cases/public/
COPY --chown=micro1user:micro1user baseline/ ./baseline/
COPY --chown=micro1user:micro1user scripts/verify_container_security.sh ./scripts/verify_container_security.sh
USER micro1user

CMD ["python", "-m", "src.main", "--smoke"]
