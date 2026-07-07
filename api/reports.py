"""Report generation endpoints for exportable audit evidence."""

import csv
import io
import json
from pathlib import Path
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.authentication.jwt import get_current_user
from app.database.connection import get_database

router = APIRouter()


@router.get("/download/{audit_id}/json")
async def download_report_json(audit_id: str, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Generate and download a JSON report for a specific audit."""
    audit = await db["audit_results"].find_one({"_id": ObjectId(audit_id)})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    system = await db["systems"].find_one({"_id": ObjectId(audit["system_id"]), "owner": current_user["id"]})
    if not system:
        raise HTTPException(status_code=403, detail="Not authorized to view this audit")

    payload = dict(audit)
    payload["id"] = str(payload["_id"])
    payload.pop("_id", None)

    report_path = payload.get("report_path")
    if isinstance(report_path, str) and Path(report_path).exists():
        content = Path(report_path).read_text(encoding="utf-8")
    else:
        content = json.dumps(payload, indent=4, default=str)

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=audit_report_{audit_id}.json"},
    )


@router.get("/download/{audit_id}/csv")
async def download_report_csv(audit_id: str, current_user: dict = Depends(get_current_user), db: Any = Depends(get_database)):
    """Generate and download a CSV report for a specific audit."""
    audit = await db["audit_results"].find_one({"_id": ObjectId(audit_id)})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    system = await db["systems"].find_one({"_id": ObjectId(audit["system_id"]), "owner": current_user["id"]})
    if not system:
        raise HTTPException(status_code=403, detail="Not authorized to view this audit")

    stream = io.StringIO()
    writer = csv.writer(stream)

    writer.writerow(["System ID", "Audit Date", "Compliance Score", "Passed", "Failed"])
    writer.writerow([audit["system_id"], audit["audit_date"], audit["compliance_score"], audit["passed_checks"], audit["failed_checks"]])

    writer.writerow([])
    writer.writerow(["Check Name", "Status", "Details"])

    for result in audit["results"]:
        writer.writerow([result["check"], result["status"], result["details"]])

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=audit_report_{audit_id}.csv"
    return response
