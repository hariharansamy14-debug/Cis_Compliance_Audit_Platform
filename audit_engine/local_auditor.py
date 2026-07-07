"""
Local / Agent compliance auditor.
Processes uploaded offline scan results instead of connecting to a remote host.
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from app.audit_engine.base_auditor import BaseAuditor

logger = logging.getLogger(__name__)

class LocalAuditor(BaseAuditor):
    def __init__(self, system_config: Dict[str, Any], scan_payload: Dict[str, Any], progress_callback: Optional[Callable] = None):
        super().__init__(system_config, progress_callback)
        self.scan_payload = scan_payload

    async def connect(self) -> bool:
        """Local execution is pre-scanned, so connection is always successful."""
        await self.report_progress("connecting", "Initializing local agent scan parser...", 10)
        return True

    async def collect_system_info(self) -> Dict[str, Any]:
        """Extract host metadata from the uploaded agent report payload."""
        await self.report_progress("collecting", "Parsing agent system details...", 20)
        return self.scan_payload.get("system_info", {})

    async def execute_check(self, control_id: str) -> str:
        """Lookup pre-collected output for the specified control ID inside the uploaded payload."""
        results: List[Dict[str, Any]] = self.scan_payload.get("results", [])
        for item in results:
            if item.get("control_id") == control_id:
                # Return actual value or fallback check command output
                return str(item.get("actual_value") or item.get("output") or "")
        return "Control not evaluated by agent scan"

    async def disconnect(self) -> None:
        """No sessions to close."""
        pass
