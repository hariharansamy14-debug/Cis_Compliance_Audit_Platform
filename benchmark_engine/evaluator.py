"""
Evaluator module to compare collected configuration values against expected benchmark controls.
"""

import re
from typing import Dict, List, Any

def evaluate_control(control: Dict[str, Any], system_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare raw check execution outputs against benchmark rules to determine pass/fail.
    """
    control_id = control["control_id"]
    expected_value = str(control.get("expected_value", "")).strip()
    
    # Extract the command output collected during the audit
    raw_output = system_data.get("check_results", {}).get(control_id)
    
    # Default outputs
    status = "failed"
    actual_value = "No output collected"
    evidence = "Command failed to execute or did not return output."
    
    if raw_output is not None:
        actual_value = str(raw_output).strip()
        
        # Strip trailing/leading white spaces and quotes
        norm_actual = actual_value.lower()
        norm_expected = expected_value.lower()
        
        # 1. Check if the output contains a specific signature of failure/pass
        if "not installed" in norm_actual or "no such file" in norm_actual:
            if "not installed" in norm_expected:
                status = "passed"
                evidence = f"Requirement met: Package/Service is verified as not installed/active. Output: {actual_value}"
            else:
                status = "failed"
                evidence = f"Requirement failed: File/Service not found. Output: {actual_value}"
        # 2. Check if actual value contains expected pattern
        elif norm_expected in norm_actual or re.search(re.escape(norm_expected), norm_actual):
            status = "passed"
            evidence = f"Requirement met. Expected: '{expected_value}'. Actual: '{actual_value}'."
        else:
            status = "failed"
            evidence = f"Compliance mismatch. Expected pattern: '{expected_value}'. Found output: '{actual_value}'."
            
        # Catch explicit status reports from advanced scripts
        if norm_actual == "passed" or norm_actual == "true":
            status = "passed"
            evidence = "Script verification succeeded."
        elif norm_actual == "failed" or norm_actual == "false":
            status = "failed"
            evidence = "Script verification returned non-compliant status."
        elif norm_actual == "not_applicable" or norm_actual == "na":
            status = "not_applicable"
            evidence = "Control is not applicable for this host configuration."
    
    return {
        "control_id": control_id,
        "control_name": control.get("control_name", ""),
        "description": control.get("description", ""),
        "category": control.get("category", "General"),
        "severity": control.get("severity", "medium").lower(),
        "expected_value": expected_value,
        "actual_value": actual_value,
        "status": status,
        "evidence": evidence,
        "remediation": control.get("remediation", ""),
        "remediation_command": control.get("remediation_command"),
        "references": control.get("references", []),
        "impact": control.get("impact")
    }

def evaluate_all_controls(benchmark: Dict[str, Any], system_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluate all controls in a benchmark against collected system outputs."""
    results = []
    controls = benchmark.get("controls", [])
    for control in controls:
        res = evaluate_control(control, system_data)
        results.append(res)
    return results

def calculate_compliance_score(results: List[Dict[str, Any]]) -> float:
    """Calculate percentage score based on passed / (passed + failed) checks."""
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    total = passed + failed
    if total == 0:
        return 100.0
    return round((passed / total) * 100, 2)

def calculate_risk_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculate an enterprise risk score from 0 (best) to 100 (worst).
    Weighted by severity: critical=10, high=7, medium=4, low=1.
    """
    severity_weights = {
        "critical": 10,
        "high": 7,
        "medium": 4,
        "low": 1,
        "informational": 0
    }
    
    total_possible_risk = 0
    actual_risk = 0
    
    for r in results:
        sev = r["severity"]
        weight = severity_weights.get(sev, 1)
        total_possible_risk += weight
        
        if r["status"] == "failed":
            actual_risk += weight
            
    if total_possible_risk == 0:
        return 0.0
    return round((actual_risk / total_possible_risk) * 100, 2)

def count_by_severity(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count failed controls broken down by severity."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for r in results:
        if r["status"] == "failed":
            sev = r["severity"]
            if sev in counts:
                counts[sev] += 1
    return counts
