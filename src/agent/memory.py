import os
import json
from typing import List, Dict, Any

class MemoryManager:
    def __init__(self, history_path: str = "data/memory/history.json", aliases_path: str = "data/memory/aliases.json"):
        self.history_path = history_path
        self.aliases_path = aliases_path
        self._ensure_file(self.history_path, [])
        self._ensure_file(self.aliases_path, {})

    def _ensure_file(self, path: str, default_data: Any):
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)

    def _read_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: str, data: Any):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def record_transaction(self, case_id: str, vendor_tax_id: str, invoice_number: str, amount: str):
        history = self._read_json(self.history_path)
        history.append({
            "case_id": case_id,
            "vendor_tax_id": vendor_tax_id,
            "invoice_number": invoice_number,
            "amount": amount
        })
        self._write_json(self.history_path, history)

    def get_prior_history(self, vendor_tax_id: str, invoice_number: str) -> List[Dict[str, Any]]:
        history = self._read_json(self.history_path)
        return [
            h for h in history
            if h.get("vendor_tax_id") == vendor_tax_id and h.get("invoice_number") == invoice_number
        ]

    def add_vendor_alias(self, canonical_name: str, alias_name: str):
        aliases = self._read_json(self.aliases_path)
        # We store aliases mapping: alias_name -> canonical_name
        aliases[alias_name] = canonical_name
        self._write_json(self.aliases_path, aliases)

    def resolve_vendor(self, vendor_name: str) -> str:
        if not vendor_name:
            return vendor_name
        aliases = self._read_json(self.aliases_path)
        return aliases.get(vendor_name, vendor_name)
