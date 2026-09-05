import os
import re
import time
from enum import Enum
from typing import List

class CredentialState(Enum):
    ACTIVE = "ACTIVE"
    COOLDOWN = "COOLDOWN"
    EXHAUSTED = "EXHAUSTED"

class RetrySignal(Exception):
    """Signal raised when current operation needs to be retried due to quota/rate limits."""
    pass

class Credential:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.state = CredentialState.ACTIVE
        self.cooldown_until = 0.0
        self.exhausted_reason = ""

    @property
    def masked_key(self) -> str:
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

class CredentialManager:
    def __init__(self, explicit_keys: List[str] = None, provider: str = None):
        self.provider = (provider or os.environ.get("LLM_PROVIDER", "gemini")).lower()
        keys = self._load_keys(explicit_keys)
        if not keys:
            raise ValueError("No provider API keys found. Configure the selected provider in the environment.")
        self.credentials = [Credential(k) for k in keys]
        self.current_index = 0

    def _load_keys(self, explicit_keys: List[str] = None) -> List[str]:
        keys = []
        if explicit_keys:
            for k in explicit_keys:
                if k and k.strip():
                    keys.append(k.strip())
            if keys:
                return list(dict.fromkeys(keys))

        tokenrouter_mode = self.provider == "tokenrouter"
        nvidia_mode = self.provider == "nvidia"
        if tokenrouter_mode:
            env_keys = os.environ.get("TOKENROUTER_API_KEYS") or os.environ.get("TOKENROUTER_API_KEY")
        elif nvidia_mode:
            env_keys = os.environ.get("NVIDIA_API_KEYS") or os.environ.get("NVIDIA_API_KEY")
        else:
            env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY")
        if env_keys:
            for part in re.split(r"[,;\n\s]+", env_keys.strip()):
                if part.startswith("AQ.") or part.startswith("AIza") or len(part) > 20:
                    keys.append(part.strip())

        if tokenrouter_mode:
            env_path = os.environ.get("TOKENROUTER_ENV_FILE", ".env")
        elif nvidia_mode:
            env_path = os.environ.get("NVIDIA_ENV_FILE", "nvidia.local.env")
        else:
            env_path = ".env"
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            name, val = line.split("=", 1)
                            name = name.strip()
                            if tokenrouter_mode:
                                if name not in {"TOKENROUTER_API_KEY", "TOKENROUTER_API_KEYS"}:
                                    continue
                            elif nvidia_mode:
                                if name not in {"NVIDIA_API_KEY", "NVIDIA_API_KEYS"}:
                                    continue
                            elif name not in {"GEMINI_API_KEY", "GEMINI_API_KEYS"}:
                                continue
                            val = val.strip()
                            for part in re.split(r"[,;\s]+", val):
                                if len(part) > 20:
                                    keys.append(part.strip())
                        elif not tokenrouter_mode and not nvidia_mode and len(line) > 20:
                            keys.append(line)
            except Exception:
                pass

        return list(dict.fromkeys(keys))

    def get_current_key(self) -> str:
        self._refresh_cooldowns()
        
        # Try to find next active
        for i in range(len(self.credentials)):
            idx = (self.current_index + i) % len(self.credentials)
            if self.credentials[idx].state == CredentialState.ACTIVE:
                self.current_index = idx
                return self.credentials[idx].api_key
                
        raise RetrySignal("All credentials are in cooldown or exhausted.")

    def mark_cooldown(self, cooldown_seconds: float = 60.0):
        curr = self.credentials[self.current_index]
        curr.state = CredentialState.COOLDOWN
        curr.cooldown_until = time.time() + cooldown_seconds
        print(f"[CREDENTIAL] Key {curr.masked_key} entering COOLDOWN for {cooldown_seconds}s.")

    def mark_exhausted(self, reason: str = ""):
        curr = self.credentials[self.current_index]
        curr.state = CredentialState.EXHAUSTED
        curr.exhausted_reason = reason
        print(f"[CREDENTIAL] Key {curr.masked_key} is EXHAUSTED: {reason}")

    def _refresh_cooldowns(self):
        now = time.time()
        for cred in self.credentials:
            if cred.state == CredentialState.COOLDOWN and now >= cred.cooldown_until:
                cred.state = CredentialState.ACTIVE
                print(f"[CREDENTIAL] Key {cred.masked_key} recovered from COOLDOWN and is now ACTIVE.")

    def get_wait_time(self) -> float:
        self._refresh_cooldowns()
        active = [c for c in self.credentials if c.state == CredentialState.ACTIVE]
        if active:
            return 0.0
        cooldowns = [c for c in self.credentials if c.state == CredentialState.COOLDOWN]
        if not cooldowns:
            return -1.0
        soonest = min(cooldowns, key=lambda c: c.cooldown_until)
        return max(0.1, soonest.cooldown_until - time.time())
