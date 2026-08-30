from decimal import Decimal, ROUND_HALF_UP

class CalculatorError(Exception):
    pass

class DecimalCalculator:
    TOLERANCE = Decimal("0.01")
    
    @staticmethod
    def _to_decimal(val) -> Decimal:
        if val is None:
            raise CalculatorError("Cannot convert None to Decimal")
        try:
            return Decimal(str(val))
        except Exception as e:
            raise CalculatorError(f"Invalid decimal value: {val}") from e
    
    @classmethod
    def round_to_cents(cls, val: Decimal) -> Decimal:
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
    @classmethod
    def check_equality(cls, a, b) -> bool:
        """Check equality within 0.01 tolerance."""
        da = cls._to_decimal(a)
        db = cls._to_decimal(b)
        return abs(da - db) <= cls.TOLERANCE
        
    @classmethod
    def multiply(cls, a, b) -> Decimal:
        da = cls._to_decimal(a)
        db = cls._to_decimal(b)
        return cls.round_to_cents(da * db)
        
    @classmethod
    def sum_values(cls, values: list) -> Decimal:
        total = Decimal("0")
        for val in values:
            total += cls._to_decimal(val)
        return cls.round_to_cents(total)
        
    @classmethod
    def calculate_tax(cls, subtotal, tax_rate_percent) -> Decimal:
        d_subtotal = cls._to_decimal(subtotal)
        d_rate = cls._to_decimal(tax_rate_percent)
        return cls.round_to_cents(d_subtotal * (d_rate / Decimal("100")))
