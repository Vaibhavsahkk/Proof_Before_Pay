import json
import traceback
import jsonschema
from typing import Dict, Any, List

from src.agent.extraction import LLMExtractor
from src.tools.calculator import DecimalCalculator, CalculatorError
from src.tools.equality import EqualityChecker
from src.tools.rule_evaluator import RuleEvaluator
from src.utils.logger import TraceLogger
from src.utils.human_checkpoint import request_human_approval

class AgentOrchestrator:
    def __init__(self, api_key: str = None, output_schema_path: str = "benchmark/schemas/output_contract.json"):
        self.extractor = LLMExtractor(api_key=api_key)
        self.logger = TraceLogger()
        self.output_schema_path = output_schema_path

    def run_workflow(self, case_id: str, raw_evidence: str) -> Dict[str, Any]:
        """
        Orchestrates the workflow: OBSERVE -> EXTRACT -> VERIFY -> APPLY RULES ->
        CHECK COMPLETENESS -> EXPLAIN -> HUMAN ESCALATION.
        """
        try:
            # 1. OBSERVE & EXTRACT
            self.logger.log_event("extract", "orchestrator", "observe_and_extract", "llm_extractor", case_id, None, "STARTED")
            extracted_data = self.extractor.extract_evidence(case_id, raw_evidence)
            self.logger.log_event("extract", "orchestrator", "observe_and_extract", "llm_extractor", case_id, extracted_data, "SUCCESS")
            
            # 2. VERIFY (Deterministic checks)
            self.logger.log_event("verify", "orchestrator", "run_deterministic_checks", "calculator_equality", extracted_data, None, "STARTED")
            anomalies, calculation_refs = self._run_deterministic_verification(extracted_data)
            self.logger.log_event("verify", "orchestrator", "run_deterministic_checks", "calculator_equality", extracted_data, anomalies, "SUCCESS")

            # 3. APPLY RULES
            self.logger.log_event("apply_rules", "orchestrator", "evaluate_rules", "rule_evaluator", anomalies, None, "STARTED")
            rule_result = RuleEvaluator.evaluate(anomalies)
            self.logger.log_event("apply_rules", "orchestrator", "evaluate_rules", "rule_evaluator", anomalies, rule_result, "SUCCESS")

            # 4. EXPLAIN
            self.logger.log_event("explain", "orchestrator", "generate_explanation", "llm_extractor", rule_result["findings"], None, "STARTED")
            uncertainty, next_step = self.extractor.generate_explanation(case_id, rule_result["findings"])
            self.logger.log_event("explain", "orchestrator", "generate_explanation", "llm_extractor", rule_result["findings"], {"uncertainty": uncertainty, "next_step": next_step}, "SUCCESS")
            
            evidence_refs = []
            for doc in ["invoice", "purchase_order", "goods_receipt", "vendor_master", "prior_payment_history", "bank_change_evidence"]:
                if extracted_data.get(doc):
                    evidence_refs.append(doc)

            missing_docs_set = {"Missing PO", "Missing GRN", "Missing Vendor Master"}
            missing_evidence = [f for f in rule_result["findings"] if f in missing_docs_set]


            output = {
                "case_id": case_id,
                "recommendation": rule_result["recommendation"],
                "findings": rule_result["findings"],
                "evidence_references": evidence_refs,
                "deterministic_calculation_references": list(set(calculation_refs)),
                "missing_evidence": missing_evidence,
                "uncertainty": uncertainty,
                "required_human_next_step": next_step
            }

            # 6. OUTPUT VALIDATION
            try:
                with open(self.output_schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(instance=output, schema=schema)
                self.logger.log_event("validate", "orchestrator", "validate_output_schema", "jsonschema", output, None, "SUCCESS")
            except jsonschema.ValidationError as ve:
                self.logger.log_event("validate", "orchestrator", "validate_output_schema", "jsonschema", output, str(ve), "ERROR")
                raise RuntimeError(f"Output schema validation failed: {ve}")

            # 7. HUMAN ESCALATION BOUNDARY
            if output["recommendation"] in ["HOLD", "INVESTIGATE"]:
                self.logger.log_event("escalate", "orchestrator", "human_checkpoint", "human", output["recommendation"], None, "STARTED")
                # We request approval, but since this is batch execution, we just trace it.
                # If we wanted to pause in a real script, we'd call request_human_approval here.
                # For this minimum implementation, outputting HOLD/INVESTIGATE is the escalation.
                self.logger.log_event("escalate", "orchestrator", "human_checkpoint", "human", output["recommendation"], "ESCALATED", "SUCCESS")
            
            return output

        except Exception as e:
            self.logger.log_event("workflow", "orchestrator", "run_workflow", "system", case_id, None, "ERROR", error=traceback.format_exc())
            # Fail closed
            return {
                "case_id": case_id,
                "recommendation": "INVESTIGATE",
                "findings": ["Extraction or System Failure"],
                "evidence_references": [],
                "deterministic_calculation_references": [],
                "missing_evidence": [],
                "uncertainty": f"System failure occurred: {str(e)}",
                "required_human_next_step": "Human review required due to system error."
            }

    def _run_deterministic_verification(self, data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        anomalies = []
        calc_refs = []
        inv = data.get("invoice", {})
        po = data.get("purchase_order")
        grn = data.get("goods_receipt")
        vm = data.get("vendor_master")
        hist = data.get("prior_payment_history")
        bank = data.get("bank_change_evidence")

        # 1. Vendor Checks
        if not vm:
            anomalies.append("Missing Vendor Master")
        else:
            if not EqualityChecker.is_exact_match(inv.get("vendor_name"), vm.get("vendor_name")) or \
               not EqualityChecker.is_exact_match(inv.get("vendor_tax_id"), vm.get("vendor_tax_id")):
                anomalies.append("Vendor Identity Mismatch")
            
            if not EqualityChecker.is_exact_match(inv.get("bank_account"), vm.get("bank_account")):
                if bank and bank.get("approval_status") == "APPROVED" and \
                   EqualityChecker.is_exact_match(bank.get("old_bank_account"), vm.get("bank_account")) and \
                   EqualityChecker.is_exact_match(bank.get("new_bank_account"), inv.get("bank_account")):
                    pass
                else:
                    anomalies.append("Unverified Bank Change")

        # 2. Missing Documents
        if not po:
            anomalies.append("Missing PO")
        if not grn:
            anomalies.append("Missing GRN")

        # 3. Duplicate Billing
        if hist:
            for past in hist:
                if EqualityChecker.is_exact_match(past.get("vendor_tax_id"), inv.get("vendor_tax_id")) and \
                   EqualityChecker.is_exact_match(past.get("invoice_number"), inv.get("invoice_number")):
                    try:
                        calc_refs.append("calculator.check_equality")
                        if DecimalCalculator.check_equality(past.get("amount"), inv.get("total")):
                            anomalies.append("Duplicate Billing")
                    except CalculatorError:
                        anomalies.append("Math Error")

        # 4. Currency
        if not EqualityChecker.is_exact_match(inv.get("currency"), "USD"):
            anomalies.append("Invalid Currency")
        if po and not EqualityChecker.is_exact_match(po.get("currency"), "USD"):
            anomalies.append("Invalid Currency")
        if po and not EqualityChecker.is_exact_match(inv.get("currency"), po.get("currency")):
            anomalies.append("Currency Mismatch")

        # 5. Tax Rate
        if po and not EqualityChecker.is_exact_match(inv.get("tax_rate_percent"), po.get("tax_rate_percent")):
            anomalies.append("Tax Rate Contradiction")

        # 6. Duplicate Line IDs
        def check_dupes(items, label):
            seen = set()
            for i in items:
                item_id = i.get("item_id")
                if item_id in seen:
                    anomalies.append(label)
                seen.add(item_id)

        inv_items = inv.get("items", [])
        po_items = po.get("items", []) if po else []
        grn_items = grn.get("items", []) if grn else []
        
        check_dupes(inv_items, "Duplicate Invoice Line ID")
        check_dupes(po_items, "Duplicate PO Line ID")
        check_dupes(grn_items, "Duplicate GRN Line ID")

        # 7. Line matching & math
        po_dict = {i.get("item_id"): i for i in po_items}
        grn_dict = {i.get("item_id"): i for i in grn_items}

        try:
            line_totals = []
            for item in inv_items:
                item_id = item.get("item_id")
                qty = item.get("quantity")
                price = item.get("unit_price")
                line_total = item.get("line_total")
                
                # Math Error: qty * price != line_total
                calc_refs.append("calculator.multiply")
                calc_refs.append("calculator.check_equality")
                if not DecimalCalculator.check_equality(DecimalCalculator.multiply(qty, price), line_total):
                    anomalies.append("Math Error")
                
                line_totals.append(line_total)

                if item_id not in po_dict:
                    anomalies.append("Missing PO Line ID")
                else:
                    calc_refs.append("calculator.check_equality")
                    if not DecimalCalculator.check_equality(price, po_dict[item_id].get("unit_price")):
                        anomalies.append("Price Contradiction")

                if item_id not in grn_dict:
                    anomalies.append("Missing GRN Line ID")
                else:
                    # Quantity mismatch uses numeric comparison
                    if DecimalCalculator._to_decimal(qty) > DecimalCalculator._to_decimal(grn_dict[item_id].get("quantity_accepted")):
                        anomalies.append("Quantity Mismatch")

            # Math Error: sum(line_totals) != subtotal
            calc_refs.append("calculator.sum_values")
            calc_refs.append("calculator.check_equality")
            if not DecimalCalculator.check_equality(DecimalCalculator.sum_values(line_totals), inv.get("subtotal")):
                anomalies.append("Math Error")

            # Math Error: subtotal * tax_rate != tax
            calc_refs.append("calculator.calculate_tax")
            calc_refs.append("calculator.check_equality")
            expected_tax = DecimalCalculator.calculate_tax(inv.get("subtotal"), inv.get("tax_rate_percent"))
            if not DecimalCalculator.check_equality(expected_tax, inv.get("tax")):
                anomalies.append("Math Error")

            # Math Error: subtotal + tax != total
            calc_refs.append("calculator.sum_values")
            calc_refs.append("calculator.check_equality")
            if not DecimalCalculator.check_equality(DecimalCalculator.sum_values([inv.get("subtotal"), inv.get("tax")]), inv.get("total")):
                anomalies.append("Math Error")
                
        except CalculatorError as e:
            self.logger.log_event("verify", "orchestrator", "calc", "calculator", None, str(e), "ERROR")
            anomalies.append("Math Error")

        return anomalies, calc_refs
