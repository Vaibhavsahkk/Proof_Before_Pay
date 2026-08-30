from typing import List, Dict, Any

class RuleEvaluator:
    FINDINGS_HOLD = [
        "Duplicate Billing",
        "Quantity Mismatch",
        "Price Contradiction",
        "Currency Mismatch",
        "Invalid Currency",
        "Tax Rate Contradiction",
        "Math Error"
    ]
    
    FINDINGS_INVESTIGATE = [
        "Missing Vendor Master",
        "Vendor Identity Mismatch",
        "Unverified Bank Change",
        "Missing PO",
        "Missing GRN",
        "Duplicate Invoice Line ID",
        "Duplicate PO Line ID",
        "Duplicate GRN Line ID",
        "Missing PO Line ID",
        "Missing GRN Line ID"
    ]
    
    @classmethod
    def evaluate(cls, anomalies: List[str]) -> Dict[str, Any]:
        """
        Evaluate anomalies and return final recommendation based on precedence:
        HOLD > INVESTIGATE > PAY.
        """
        unique_anomalies = list(set(anomalies))
        
        holds = [a for a in unique_anomalies if a in cls.FINDINGS_HOLD]
        investigates = [a for a in unique_anomalies if a in cls.FINDINGS_INVESTIGATE]
        
        # Any anomaly not recognized should default to INVESTIGATE for safety
        unrecognized = [a for a in unique_anomalies if a not in cls.FINDINGS_HOLD and a not in cls.FINDINGS_INVESTIGATE]
        if unrecognized:
            investigates.extend(unrecognized)
            
        findings = holds + investigates
        
        if holds:
            recommendation = "HOLD"
        elif investigates:
            recommendation = "INVESTIGATE"
        else:
            recommendation = "PAY"
            
        return {
            "recommendation": recommendation,
            "findings": sorted(list(set(findings)))
        }
