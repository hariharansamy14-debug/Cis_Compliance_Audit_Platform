"""
Audit Engine orchestrator coordinating connections, execution, evaluation, and DB storage.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from app.audit_engine.linux_auditor import LinuxAuditor
from app.audit_engine.windows_auditor import WindowsAuditor
from app.audit_engine.local_auditor import LocalAuditor
from app.benchmark_engine.evaluator import (
    evaluate_control,
    calculate_compliance_score,
    calculate_risk_score,
    count_by_severity
)

logger = logging.getLogger(__name__)

def get_auditor(system: Dict[str, Any], scan_payload: Optional[Dict[str, Any]] = None, progress_callback: Optional[Callable] = None):
    """Factory method to return the correct auditor subclass."""
    connection_type = system.get("connection_type", "agent")
    
    if connection_type == "ssh":
        return LinuxAuditor(system, progress_callback)
    elif connection_type == "winrm":
        return WindowsAuditor(system, progress_callback)
    else:
        # local agent upload scan
        if not scan_payload:
            raise ValueError("Local agent scan requires an uploaded report payload.")
        return LocalAuditor(system, scan_payload, progress_callback)

async def run_full_audit(
    system: Dict[str, Any],
    benchmark: Dict[str, Any],
    credentials: Optional[Dict[str, Any]] = None,
    scan_payload: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Orchestrates the entire compliance collection lifecycle.
    1. Connect to host
    2. Collect system metadata
    3. Run benchmark checks
    4. Evaluate and calculate score
    5. Clean up connection
    """
    # Merge remote credentials if provided
    system_config = {**system}
    if credentials:
        system_config.update(credentials)
        
    auditor = get_auditor(system_config, scan_payload, progress_callback)
    start_time = time.time()
    
    try:
        # 1. Connect
        connected = await auditor.connect()
        if not connected:
            raise ConnectionError("Auditor failed to connect to the target system.")
            
        # 2. Collect host info
        system_info = await auditor.collect_system_info()
        
        # 3. Execute check commands
        controls = benchmark.get("controls", [])
        total_controls = len(controls)
        check_results = {}
        
        # Report starting checks
        await auditor.report_progress("evaluating", f"Starting compliance checks (0/{total_controls})...", 30)
        
        for idx, control in enumerate(controls):
            control_id = control["control_id"]
            control_name = control["control_name"]
            
            # Calculate dynamic progress step between 30% and 85%
            progress_pct = int(30 + (idx / total_controls) * 55)
            await auditor.report_progress(
                "evaluating",
                f"Running check {idx + 1}/{total_controls}: {control_name}",
                progress_pct
            )
            
            # For LocalAuditor, pass control_id. For remote SSH/WinRM, execute check_command.
            if isinstance(auditor, LocalAuditor):
                output = await auditor.execute_check(control_id)
            else:
                cmd = control["check_command"]
                output = await auditor.execute_check(cmd)
                
            check_results[control_id] = output
            
        # Add collected outputs to system data for evaluation
        eval_system_data = {
            "system_info": system_info,
            "check_results": check_results
        }
        
        # 4. Evaluate controls
        await auditor.report_progress("calculating", "Analyzing results and calculating score...", 90)
        
        evaluated_results = []
        passed_count = 0
        failed_count = 0
        not_applicable_count = 0
        error_count = 0
        
        for control in controls:
            eval_res = evaluate_control(control, eval_system_data)
            evaluated_results.append(eval_res)
            
            status = eval_res["status"]
            if status == "passed":
                passed_count += 1
            elif status == "failed":
                failed_count += 1
            elif status == "not_applicable":
                not_applicable_count += 1
            else:
                error_count += 1
                
        # Aggregate scores
        comp_score = calculate_compliance_score(evaluated_results)
        risk_score = calculate_risk_score(evaluated_results)
        severity_counts = count_by_severity(evaluated_results)
        
        duration = round(time.time() - start_time, 2)
        
        audit_record = {
            "system_id": str(system.get("id")),
            "benchmark_id": benchmark.get("short_name", "unknown"),
            "benchmark_version": benchmark.get("version", "1.0.0"),
            "audit_date": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "duration_seconds": duration,
            "status": "completed",
            "compliance_score": comp_score,
            "risk_score": risk_score,
            
            # Counters
            "total_controls": total_controls,
            "passed_controls": passed_count,
            "failed_controls": failed_count,
            "error_controls": error_count,
            "not_applicable_controls": not_applicable_count,
            
            # Severity counts
            "critical_findings": severity_counts.get("critical", 0),
            "high_findings": severity_counts.get("high", 0),
            "medium_findings": severity_counts.get("medium", 0),
            "low_findings": severity_counts.get("low", 0),
            
            "results": evaluated_results,
            "system_info": system_info
        }
        
        await auditor.report_progress("completed", "Audit verification complete!", 100)
        return audit_record
        
    except Exception as e:
        logger.exception("Error running compliance audit: %s", e)
        if auditor:
            await auditor.report_progress("error", f"Audit failed: {str(e)}", 0)
        raise
    finally:
        if auditor:
            await auditor.disconnect()
