class EqualityChecker:
    @staticmethod
    def is_exact_match(a: str, b: str) -> bool:
        """Exact deterministic string comparison."""
        if a is None or b is None:
            return False
        return str(a) == str(b)
