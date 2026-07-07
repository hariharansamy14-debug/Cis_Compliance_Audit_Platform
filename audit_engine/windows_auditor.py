"""
Windows WinRM-based compliance auditor utilizing pywinrm and asyncio.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
import winrm
from app.audit_engine.base_auditor import BaseAuditor

logger = logging.getLogger(__name__)

class WindowsAuditor(BaseAuditor):
    def __init__(self, system_config: Dict[str, Any], progress_callback: Optional[Callable] = None):
        super().__init__(system_config, progress_callback)
        self.session: Optional[winrm.Session] = None

    async def connect(self) -> bool:
        """Establish WinRM session in a non-blocking thread."""
        hostname = self.system_config.get("ip_address") or self.system_config.get("hostname")
        port = int(self.system_config.get("winrm_port", 5985))
        username = self.system_config.get("ssh_username")  # Reuse standard username field
        password = self.system_config.get("ssh_password")  # Reuse password field
        
        if not username or not password:
            raise ValueError("WinRM username and password are required for remote Windows audits.")
            
        await self.report_progress("connecting", f"Establishing WinRM connection to {hostname}:{port}...", 10)
        
        # Setup WinRM transport URL
        endpoint = f"http://{hostname}:{port}/wsman"
        
        def _connect_blocking():
            # Create winrm Session object (lazily verified on first command run)
            session = winrm.Session(
                endpoint,
                auth=(username, password),
                transport="ntlm",
                server_cert_validation="ignore"
            )
            # Run simple echo to test connection
            r = session.run_cmd("echo 'winrm-connected'")
            if r.status_code != 0:
                raise ConnectionError(f"WinRM authentication failed or endpoint unreachable (Code {r.status_code}): {r.std_err.decode()}")
            return session

        try:
            self.session = await asyncio.to_thread(_connect_blocking)
            logger.info("Successfully connected to WinRM host %s", hostname)
            return True
        except Exception as e:
            logger.error("WinRM connection failed to %s: %s", hostname, e)
            await self.report_progress("error", f"WinRM Connection failed: {str(e)}", 0)
            return False

    async def collect_system_info(self) -> Dict[str, Any]:
        """Gather Windows system details using PowerShell."""
        await self.report_progress("collecting", "Querying remote Windows host information...", 20)
        
        hostname = await self.execute_check("[System.Net.Dns]::GetHostName()")
        os_name = await self.execute_check("(Get-CimInstance Win32_OperatingSystem).Caption")
        os_version = await self.execute_check("(Get-CimInstance Win32_OperatingSystem).Version")
        
        return {
            "hostname": hostname.strip() or self.system_config.get("hostname"),
            "operating_system": "windows",
            "os_version": f"{os_name.strip()} ({os_version.strip()})"
        }

    async def execute_check(self, command: str) -> str:
        """Execute a PowerShell command/script block over WinRM."""
        if not self.session:
            raise RuntimeError("WinRM session is not established.")
            
        def _exec_blocking():
            # Run command inside powershell wrapper
            r = self.session.run_ps(command)
            out = r.std_out.decode("utf-8", errors="ignore")
            err = r.std_err.decode("utf-8", errors="ignore")
            if r.status_code != 0 or err:
                return f"Error: {err or 'Non-zero status code: ' + str(r.status_code)}"
            return out

        try:
            return await asyncio.to_thread(_exec_blocking)
        except Exception as e:
            logger.error("WinRM command execution failed '%s': %s", command, e)
            return f"Error: {str(e)}"

    async def disconnect(self) -> None:
        """WinRM is stateless, no active persistent TCP connection needs closure."""
        self.session = None
        logger.info("WinRM session cleared.")
        return None
