import os
import json
import pytest
from src.agent.memory import MemoryManager

def test_memory_manager_history(tmp_path):
    history_file = tmp_path / "history.json"
    manager = MemoryManager(history_path=str(history_file))
    
    # Record a transaction
    manager.record_transaction("case_001", "TX-123", "INV-001", "500.00")
    
    # Check if duplicate exists
    history = manager.get_prior_history("TX-123", "INV-001")
    assert len(history) == 1
    assert history[0]["case_id"] == "case_001"
    assert history[0]["amount"] == "500.00"
    
    # Check non-existent
    history_none = manager.get_prior_history("TX-123", "INV-002")
    assert len(history_none) == 0

def test_memory_manager_aliases(tmp_path):
    aliases_file = tmp_path / "aliases.json"
    manager = MemoryManager(aliases_path=str(aliases_file))
    
    # Record alias
    manager.add_vendor_alias("SYNTHETIC WIDGETS LLC", "SYNTHETIC WIDGETS")
    manager.add_vendor_alias("SYNTHETIC WIDGETS LLC", "SYNTHETIC WIDGETS INC")
    
    # Resolve known
    assert manager.resolve_vendor("SYNTHETIC WIDGETS") == "SYNTHETIC WIDGETS LLC"
    assert manager.resolve_vendor("SYNTHETIC WIDGETS INC") == "SYNTHETIC WIDGETS LLC"
    
    # Resolve unknown returns original
    assert manager.resolve_vendor("UNKNOWN VENDOR") == "UNKNOWN VENDOR"
