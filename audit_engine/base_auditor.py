"""
Abstract Base Auditor class defining interface for remote and local compliance collectors.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Dict

class BaseAuditor(ABC):
    def __init__(self, system_config: Dict[str, Any], progress_callback: Optional[Callable] = None):
        self.system_config = system_config
        self.progress_callback = progress_callback
        self.system_data = {}

    async def report_progress(self, stage: str, message: str, progress: int):
        """Call callback to stream execution status updates via WebSockets."""
        if self.progress_callback:
            await self.progress_callback({
                "stage": stage,
                "message": message,
                "progress": progress
            })

    @abstractmethod
    async def connect(self) -> bool:
        """Establish session (e.g. SSH, WinRM). Return True if successful."""
        pass

    @abstractmethod
    async def collect_system_info(self) -> Dict[str, Any]:
        """Fetch general system metadata (OS Version, hostname, hardware details)."""
        pass

    @abstractmethod
    async def execute_check(self, command: str) -> str:
        """Run verification command on host and return stdout string."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Terminate connection clean up resources."""
        pass
