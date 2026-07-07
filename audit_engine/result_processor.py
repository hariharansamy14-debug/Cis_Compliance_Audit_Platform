"""
Result processor helper to format and aggregate compliance scan runs.
"""

from typing import Dict, List, Any
from datetime import datetime

def build_audit_summary(
    system_id: str,
    benchmark: Dict[str, Any],
    evaluated_results: List[Dict[str, Any]],
    system_info: Dict[str, Any],
    duration: float,
    run_by_id: str
) -> Dict[str, Any]:
    """Compile final compliant report record structure for DB serialization."""
    total = len(evaluated_results)
    passed = sum(1 for r in evaluated_results if r["status"] == "passed")
    failed = sum(1 for r in evaluated_results if r["status"] == "failed")
    na = sum(1 for r in evaluated_results if r["status"] == "not_applicable")
    err = sum(1 for r in evaluated_results if r["status"] == "error")
    
    # Calculate severity counts
    critical = sum(1 for r in evaluated_results if r["status"] == "failed" and r["severity"] == "critical")
    high = sum(1 for r in evaluated_results if r["status"] == "failed" and r["severity"] == "high")
    medium = sum(1 for r in evaluated_results if r["status"] == "failed" and r["severity"] == "medium")
    low = sum(1 for r in evaluated_results if r["status"] == "failed" and r["severity"] == "low")
    
    # Calculations
    total_valid = passed + failed
    score = round((passed / total_valid * 100) if total_valid > 0 else 100.0, 2)
    
    # Simple weighted risk score
    # Critical=10, High=7, Medium=4, Low=1
    total_possible_risk = (passed + failed) * 5  # normalized average weight
    actual_risk = (critical * 10) + (high * 7) + (medium * 4) + (low * 1)
    risk_score = round((actual_risk / max(total_possible_risk, 1)) * 100, 2)
    risk_score = min(risk_score, 100.0)

    return {
        "system_id": system_id,
        "benchmark_id": benchmark.get("short_name", "unknown"),
        "benchmark_version": benchmark.get("version", "1.0.0"),
        "audit_date": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
        "duration_seconds": duration,
        "status": "completed",
        "run_by": run_by_id,
        "compliance_score": score,
        "risk_score": risk_score,
        "total_controls": total,
        "passed_controls": passed,
        "failed_controls": failed,
        "error_controls": err,
        "not_applicable_controls": na,
        "critical_findings": critical,
        "high_findings": high,
        "medium_findings": medium,
        "low_findings": low,
        "results": evaluated_results,
        "system_info": system_info
    }
