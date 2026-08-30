import pytest
from decimal import Decimal
from src.tools.calculator import DecimalCalculator, CalculatorError
from src.tools.equality import EqualityChecker
from src.tools.rule_evaluator import RuleEvaluator

def test_decimal_calculator_conversion():
    assert DecimalCalculator._to_decimal("1.23") == Decimal("1.23")
    assert DecimalCalculator._to_decimal(1.23) == Decimal("1.23")
    assert DecimalCalculator._to_decimal(1) == Decimal("1")
    
    with pytest.raises(CalculatorError):
        DecimalCalculator._to_decimal(None)
    
    with pytest.raises(CalculatorError):
        DecimalCalculator._to_decimal("abc")

def test_decimal_calculator_round_to_cents():
    assert DecimalCalculator.round_to_cents(Decimal("1.234")) == Decimal("1.23")
    assert DecimalCalculator.round_to_cents(Decimal("1.235")) == Decimal("1.24")
    assert DecimalCalculator.round_to_cents(Decimal("1.236")) == Decimal("1.24")

def test_decimal_calculator_check_equality():
    assert DecimalCalculator.check_equality("1.23", "1.23")
    assert DecimalCalculator.check_equality("1.234", "1.23")
    assert DecimalCalculator.check_equality("1.236", "1.24") # wait, 1.236 is not equal to 1.24 within 0.01 tolerance, 1.24 - 1.236 = 0.004 <= 0.01, so it is equal.
    assert DecimalCalculator.check_equality("1.23", "1.24") # equal? abs(1.23 - 1.24) = 0.01 <= 0.01. So True.
    assert not DecimalCalculator.check_equality("1.23", "1.25") # abs(1.23 - 1.25) = 0.02 > 0.01. So False.

def test_decimal_calculator_multiply():
    assert DecimalCalculator.multiply("2", "3") == Decimal("6.00")
    assert DecimalCalculator.multiply("1.5", "1.5") == Decimal("2.25")
    assert DecimalCalculator.multiply("1.333", "2") == Decimal("2.67")

def test_decimal_calculator_sum_values():
    assert DecimalCalculator.sum_values(["1.11", "2.22", "3.33"]) == Decimal("6.66")
    assert DecimalCalculator.sum_values([]) == Decimal("0.00")
    assert DecimalCalculator.sum_values(["1.114", "1.114"]) == Decimal("2.23")

def test_decimal_calculator_calculate_tax():
    assert DecimalCalculator.calculate_tax("100", "5") == Decimal("5.00")
    assert DecimalCalculator.calculate_tax("10", "8.25") == Decimal("0.83")
    assert DecimalCalculator.calculate_tax("0", "10") == Decimal("0.00")

def test_equality_checker():
    assert EqualityChecker.is_exact_match("A", "A")
    assert not EqualityChecker.is_exact_match("A", "a")
    assert EqualityChecker.is_exact_match(1, "1")
    assert not EqualityChecker.is_exact_match(None, None) # by design, returns False if either is None
    assert not EqualityChecker.is_exact_match("A", None)

def test_rule_evaluator():
    # Test PAY
    result = RuleEvaluator.evaluate([])
    assert result["recommendation"] == "PAY"
    assert result["findings"] == []

    # Test HOLD
    result = RuleEvaluator.evaluate(["Math Error"])
    assert result["recommendation"] == "HOLD"
    assert result["findings"] == ["Math Error"]
    
    # Test INVESTIGATE
    result = RuleEvaluator.evaluate(["Missing PO"])
    assert result["recommendation"] == "INVESTIGATE"
    assert result["findings"] == ["Missing PO"]
    
    # Test precedence: HOLD > INVESTIGATE
    result = RuleEvaluator.evaluate(["Missing PO", "Math Error"])
    assert result["recommendation"] == "HOLD"
    assert sorted(result["findings"]) == ["Math Error", "Missing PO"]

    # Test unrecognized defaults to INVESTIGATE
    result = RuleEvaluator.evaluate(["Some unknown finding"])
    assert result["recommendation"] == "INVESTIGATE"
    assert result["findings"] == ["Some unknown finding"]
