"""
Linux SSH-based compliance auditor utilizing Paramiko and asyncio.
"""

import logging
import asyncio
import io
from typing import Dict, Any, Optional, Callable
import paramiko
from app.audit_engine.base_auditor import BaseAuditor

logger = logging.getLogger(__name__)

class LinuxAuditor(BaseAuditor):
    def __init__(self, system_config: Dict[str, Any], progress_callback: Optional[Callable] = None):
        super().__init__(system_config, progress_callback)
        self.ssh_client: Optional[paramiko.SSHClient] = None

    async def connect(self) -> bool:
        """Establish SSH connection in a non-blocking thread."""
        hostname = self.system_config.get("ip_address") or self.system_config.get("hostname")
        port = int(self.system_config.get("ssh_port", 22))
        username = self.system_config.get("ssh_username")
        password = self.system_config.get("ssh_password")
        pkey_str = self.system_config.get("ssh_key")
        
        if not username:
            raise ValueError("SSH username is required for remote auditing.")
            
        await self.report_progress("connecting", f"Establishing SSH connection to {hostname}:{port}...", 10)
        
        # Define blocking connection logic to run in a thread pool
        def _connect_blocking():
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load private key if provided
            pkey = None
            if pkey_str:
                try:
                    pkey = paramiko.RSAKey.from_private_key(io.StringIO(pkey_str))
                except Exception:
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(pkey_str))
                    except Exception as e:
                        logger.error("Failed to parse SSH private key: %s", e)
                        
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                pkey=pkey,
                timeout=15
            )
            return client

        try:
            self.ssh_client = await asyncio.to_thread(_connect_blocking)
            logger.info("Successfully connected to SSH host %s", hostname)
            return True
        except Exception as e:
            logger.error("SSH connection failed to %s: %s", hostname, e)
            await self.report_progress("error", f"SSH Connection failed: {str(e)}", 0)
            return False

    async def collect_system_info(self) -> Dict[str, Any]:
        """Gather host details like operating system name and version."""
        await self.report_progress("collecting", "Querying remote Linux host information...", 20)
        
        hostname = await self.execute_check("hostname")
        uname = await self.execute_check("uname -a")
        os_release = await self.execute_check("cat /etc/os-release 2>/dev/null")
        uptime = await self.execute_check("uptime")
        
        info = {
            "hostname": hostname.strip() or self.system_config.get("hostname"),
            "kernel": uname.strip(),
            "uptime": uptime.strip()
        }
        
        # Parse /etc/os-release
        if os_release:
            for line in os_release.splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip('"').strip("'")
                    if key == "PRETTY_NAME":
                        info["os_version"] = val
                    elif key == "ID":
                        info["os_id"] = val
                        
        return info

    async def execute_check(self, command: str) -> str:
        """Execute a bash command on the remote host."""
        if not self.ssh_client:
            raise RuntimeError("SSH Client is not connected.")
            
        def _exec_blocking():
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=10)
            # Read stdout and stderr
            out = stdout.read().decode("utf-8", errors="ignore")
            err = stderr.read().decode("utf-8", errors="ignore")
            if err and not out:
                return f"Error: {err}"
            return out

        try:
            return await asyncio.to_thread(_exec_blocking)
        except Exception as e:
            logger.error("Command execution failed '%s': %s", command, e)
            return f"Error: {str(e)}"

    async def disconnect(self) -> None:
        """Close the SSH client session."""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception as e:
                logger.error("Error closing SSH client: %s", e)
            self.ssh_client = None
            logger.info("SSH connection closed.")
