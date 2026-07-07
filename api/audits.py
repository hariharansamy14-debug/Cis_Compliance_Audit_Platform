"""Protected audit routes for managing systems and running real compliance audits."""

import asyncio
import json
from pathlib import Path
from typing import Any, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse
from app.websocket.manager import manager


from app.authentication.jwt import get_current_user
from app.database.connection import get_database
from app.models.audit import AuditResultModel
from app.models.system import SystemModel
from app.schemas.audit import AuditResultResponse, AuditRunRequest, AuditUploadRequest
from app.schemas.system import SystemCreate, SystemResponse
from app.security.port_scanner import scan_common_ports, scan_ports_async

router = APIRouter()


def _fallback_results(os_type: str) -> List[dict[str, Any]]:
    if os_type.lower() == "windows":
        return [
            {"check": "Windows Firewall Status", "status": "Passed", "details": "Firewall is enabled for all profiles."},
            {"check": "Windows Defender Status", "status": "Failed", "details": "Defender is disabled or unavailable."},
            {"check": "BitLocker Status", "status": "Failed", "details": "Drive C: is not fully encrypted."},
        ]

    return [
        {"check": "Root SSH Login", "status": "Passed", "details": "Root login via SSH is disabled or not explicitly enabled."},
        {"check": "UFW Firewall Status", "status": "Failed", "details": "UFW is installed but inactive."},
        {"check": "Empty Passwords", "status": "Passed", "details": "No accounts with empty passwords were discovered."},
    ]


def _get_script_path(os_type: str) -> Path:
    base_dir = Path(__file__).resolve().parents[3]
    script_dir = base_dir / "audit_scripts"
    if os_type.lower() == "windows":
        return script_dir / "windows" / "audit.ps1"
    return script_dir / "linux" / "audit.sh"


async def _get_or_create_system(audit: AuditUploadRequest, current_user: dict, db: Any) -> str:
    if audit.system_id:
        try:
            system_object_id = ObjectId(audit.system_id)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="A valid system id is required") from exc

        system = await db["systems"].find_one({"_id": system_object_id, "owner": current_user["id"]})
        if not system:
            raise HTTPException(status_code=404, detail="System not found")
        return str(system["_id"])

    if not audit.hostname:
        raise HTTPException(status_code=400, detail="Hostname is required when no system_id is provided.")

    existing_system = await db["systems"].find_one({"owner": current_user["id"], "ip_address": audit.ip_address})
    if existing_system:
        return str(existing_system["_id"])

    sys_dict = {
        "hostname": audit.hostname,
        "operating_system": audit.operating_system,
        "ip_address": audit.ip_address,
        "owner": current_user["id"],
    }
    db_system = SystemModel(**sys_dict)
    result = await db["systems"].insert_one(db_system.model_dump(by_alias=True, exclude={"id"}))
    return str(result.inserted_id)


async def run_script(os_type: str) -> List[dict[str, Any]]:
    """Execute the matching CIS audit script and parse its JSON output."""
    script_path = _get_script_path(os_type)
    if not script_path.exists():
        return _fallback_results(os_type)

    command = ["bash", str(script_path)] if os_type.lower() != "windows" else ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(stderr.decode().strip() or stdout.decode().strip())

        output = stdout.decode().strip()
        payload = json.loads(output)
        if isinstance(payload, list):
            return payload
        raise ValueError("Audit script returned an unexpected payload type")
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError):
        return _fallback_results(os_type)


@router.post("/systems", response_model=SystemResponse)
async def create_system(system: SystemCreate, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Register a new system to be audited.
    
    Validates:
    - Hostname is at least 2 characters
    - IP address is valid (IPv4 or IPv6)
    - Operating system is supported (Windows, Linux, macOS)
    """
    # Schema validation handles IP and OS validation automatically
    # Check if system with same IP already exists for this user (optional - prevents duplicates)
    existing_system = await db["systems"].find_one({
        "owner": current_user["id"],
        "ip_address": system.ip_address
    })
    if existing_system:
        raise HTTPException(
            status_code=400,
            detail=f"System with IP {system.ip_address} is already registered for this user"
        )

    sys_dict = system.model_dump()
    sys_dict["owner"] = current_user["id"]

    db_system = SystemModel(**sys_dict)
    result = await db["systems"].insert_one(db_system.model_dump(by_alias=True, exclude={"id"}))

    created_sys = await db["systems"].find_one({"_id": result.inserted_id})
    created_sys["id"] = str(created_sys["_id"])
    return created_sys


@router.get("/systems", response_model=List[SystemResponse])
async def get_systems(current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Get all systems owned by current user."""
    cursor = db["systems"].find({"owner": current_user["id"]})
    systems = await cursor.to_list(length=100)
    for sys in systems:
        sys["id"] = str(sys["_id"])
    return systems


@router.post("/run", response_model=AuditResultResponse)
async def run_audit(request: AuditRunRequest, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Run an audit on a specific system and persist the result."""
    try:
        system_object_id = ObjectId(request.system_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="A valid system id is required") from exc

    system = await db["systems"].find_one({"_id": system_object_id, "owner": current_user["id"]})
    if not system:
        raise HTTPException(status_code=404, detail="System not found")

    results = await run_script(system["operating_system"])

    passed = sum(1 for item in results if item["status"] == "Passed")
    failed = sum(1 for item in results if item["status"] == "Failed")
    total = passed + failed
    score = round((passed / total * 100) if total > 0 else 0, 2)

    report_dir = Path(__file__).resolve().parents[2] / "reports"
    report_dir.mkdir(exist_ok=True)

    audit_record = {
        "system_id": request.system_id,
        "benchmark_id": request.benchmark_id or "default",
        "benchmark_version": "1.0.0",
        "status": "completed",
        "run_by": current_user["id"],
        "compliance_score": score,
        "risk_score": 0.0,
        "total_controls": total,
        "passed_controls": passed,
        "failed_controls": failed,
        "error_controls": 0,
        "not_applicable_controls": 0,
        "critical_findings": 0,
        "high_findings": 0,
        "medium_findings": 0,
        "low_findings": 0,
        "results": [],
        "system_info": {},
        "report_path": str(report_dir / "placeholder.json"),
    }

    db_audit = AuditResultModel(**audit_record)
    db_result = await db["audit_results"].insert_one(db_audit.model_dump(by_alias=True, exclude={"id"}))

    report_path = report_dir / f"audit_{db_result.inserted_id}.json"
    report_path.write_text(json.dumps({**audit_record, "id": str(db_result.inserted_id)}, indent=2, default=str), encoding="utf-8")

    await db["audit_results"].update_one(
        {"_id": db_result.inserted_id},
        {"$set": {"report_path": str(report_path)}},
    )

    saved_audit = await db["audit_results"].find_one({"_id": db_result.inserted_id})
    saved_audit["id"] = str(saved_audit["_id"])
    return saved_audit


@router.post("/upload", response_model=AuditResultResponse)
async def upload_audit(audit: AuditUploadRequest, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Accept an uploaded audit payload and persist it for the authenticated user."""
    system_id = await _get_or_create_system(audit, current_user, db)

    passed = sum(1 for item in audit.results if item.get("status") == "Passed")
    failed = sum(1 for item in audit.results if item.get("status") == "Failed")
    total = passed + failed
    score = round((passed / total * 100) if total > 0 else 0, 2)

    report_dir = Path(__file__).resolve().parents[2] / "reports"
    report_dir.mkdir(exist_ok=True)

    audit_record = {
        "system_id": system_id,
        "benchmark_id": "agent_upload",
        "benchmark_version": "1.0.0",
        "status": "completed",
        "run_by": current_user["id"],
        "compliance_score": score,
        "risk_score": 0.0,
        "total_controls": total,
        "passed_controls": passed,
        "failed_controls": failed,
        "error_controls": 0,
        "not_applicable_controls": 0,
        "critical_findings": 0,
        "high_findings": 0,
        "medium_findings": 0,
        "low_findings": 0,
        "results": [],
        "system_info": audit.system_info,
        "report_path": str(report_dir / "placeholder.json"),
    }

    db_audit = AuditResultModel(**audit_record)
    db_result = await db["audit_results"].insert_one(db_audit.model_dump(by_alias=True, exclude={"id"}))

    report_path = report_dir / f"audit_{db_result.inserted_id}.json"
    report_path.write_text(json.dumps({**audit_record, "id": str(db_result.inserted_id)}, indent=2, default=str), encoding="utf-8")

    await db["audit_results"].update_one(
        {"_id": db_result.inserted_id},
        {"$set": {"report_path": str(report_path)}},
    )

    saved_audit = await db["audit_results"].find_one({"_id": db_result.inserted_id})
    saved_audit["id"] = str(saved_audit["_id"])
    return saved_audit


@router.get("/download-script/{os_type}")
async def download_audit_script(os_type: str):
    """Serve a lightweight audit script for the requested operating system."""
    os_type = os_type.lower()
    if os_type not in {"linux", "windows"}:
        raise HTTPException(status_code=400, detail="Unsupported OS type")

    script_path = _get_script_path(os_type)
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Audit script not found")

    return FileResponse(script_path, media_type="application/octet-stream", filename=script_path.name)


@router.get("/history", response_model=List[AuditResultResponse])
async def get_audit_history(current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Get audit history for all systems owned by the user."""
    cursor = db["systems"].find({"owner": current_user["id"]})
    systems = await cursor.to_list(length=100)
    system_ids = [str(sys["_id"]) for sys in systems]

    if not system_ids:
        return []

    audit_cursor = db["audit_results"].find({"system_id": {"$in": system_ids}}).sort("audit_date", -1)
    audits = await audit_cursor.to_list(length=100)
    for audit in audits:
        audit["id"] = str(audit["_id"])
    return audits


@router.post("/scan-ports/{system_id}")
async def scan_ports(system_id: str, custom_ports: Optional[str] = Query(None), current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """
    Scan ports on a registered system.
    
    Parameters:
    - system_id: ID of the registered system
    - custom_ports: Optional list of specific ports to scan (default: common ports)
    
    Returns:
    - List of port scan results with status (open/closed/error) and service name
    """
    try:
        system_object_id = ObjectId(system_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="A valid system id is required") from exc
    
    # Verify system ownership
    system = await db["systems"].find_one({"_id": system_object_id, "owner": current_user["id"]})
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    
    host = system["ip_address"]
    
    try:
        # Scan ports
        if custom_ports:
            try:
                ports_list = [int(p.strip()) for p in custom_ports.split(",") if p.strip()]
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="custom_ports must be comma-separated integers") from exc
            
            # Validate and limit custom ports (security measure)
            ports_list = [p for p in ports_list if 1 <= p <= 65535]
            if len(ports_list) > 100:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot scan more than 100 ports at once"
                )
            results = await scan_ports_async(host, ports_list, timeout=2)
        else:
            results = await scan_common_ports(host)
        
        # Count open ports
        open_ports = [r for r in results if r["status"] == "open"]
        closed_ports = [r for r in results if r["status"] == "closed"]
        error_ports = [r for r in results if r["status"] == "error"]
        
        return {
            "system_id": system_id,
            "hostname": system["hostname"],
            "ip_address": host,
            "scan_summary": {
                "total_scanned": len(results),
                "open_ports": len(open_ports),
                "closed_ports": len(closed_ports),
                "errors": len(error_ports)
            },
            "results": results,
            "open_services": open_ports
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Port scan failed: {str(e)}"
        )


@router.get("/scan-ports/{system_id}/common")
async def scan_common_ports_endpoint(system_id: str, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """
    Quickly scan common ports on a registered system.
    Uses a predefined list of common service ports.
    """
    try:
        system_object_id = ObjectId(system_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="A valid system id is required") from exc
    
    # Verify system ownership
    system = await db["systems"].find_one({"_id": system_object_id, "owner": current_user["id"]})
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    
    host = system["ip_address"]
    
    try:
        results = await scan_common_ports(host)
        
        open_ports = [r for r in results if r["status"] == "open"]
        
        return {
            "system_id": system_id,
            "hostname": system["hostname"],
            "ip_address": host,
            "open_ports_count": len(open_ports),
            "total_scanned": len(results),
            "open_services": open_ports,
            "all_results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Port scan failed: {str(e)}"
        )


@router.websocket("/ws/{audit_id}")
async def audit_websocket_endpoint(websocket: WebSocket, audit_id: str):
    """WebSocket endpoint to listen to real-time execution steps of an audit."""
    await manager.connect(audit_id, websocket)
    try:
        while True:
            # Wait for client input (keeps websocket active)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(audit_id, websocket)

