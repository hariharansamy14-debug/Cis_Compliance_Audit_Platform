"""
Benchmark loader to parse local JSON benchmark definitions and seed them into MongoDB.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

BENCHMARKS_DIR = Path(__file__).resolve().parent / "benchmarks"

OS_MAPPING = {
    "ubuntu": "ubuntu_22",
    "debian": "ubuntu_22",
    "windows_11": "windows_11",
    "windows": "windows_11",
    "rhel": "rhel_9",
    "centos": "rhel_9",
    "rocky": "rhel_9",
    "amazon_linux": "rhel_9",
    "windows_server": "windows_server_2022"
}

def get_available_benchmarks() -> List[str]:
    """List all benchmark identifiers available locally in the benchmarks folder."""
    if not BENCHMARKS_DIR.exists():
        return []
    return [f.stem for f in BENCHMARKS_DIR.glob("*.json")]

def load_benchmark(benchmark_name: str) -> Optional[Dict[str, Any]]:
    """Load and parse a local benchmark definition from its JSON file."""
    file_path = BENCHMARKS_DIR / f"{benchmark_name}.json"
    if not file_path.exists():
        logger.error("Benchmark file %s does not exist", file_path)
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load benchmark JSON %s: %s", benchmark_name, e)
        return None

def get_benchmark_for_os(os_type: str) -> Optional[Dict[str, Any]]:
    """Determine and load the matching benchmark based on OS string."""
    normalized = os_type.strip().lower()
    
    # Check for direct key match
    benchmark_name = OS_MAPPING.get(normalized)
    
    # Try fuzzy match if direct fails
    if not benchmark_name:
        for key, val in OS_MAPPING.items():
            if key in normalized:
                benchmark_name = val
                break
                
    if not benchmark_name:
        logger.warning("No benchmark mapped for OS: %s. Defaulting to ubuntu_22.", os_type)
        benchmark_name = "ubuntu_22"
        
    return load_benchmark(benchmark_name)

async def seed_benchmarks_to_db(db: Any) -> None:
    """Read all local benchmark files and seed/upsert them into MongoDB."""
    BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
    benchmarks = get_available_benchmarks()
    
    for name in benchmarks:
        data = load_benchmark(name)
        if not data:
            continue
            
        data["created_at"] = datetime.utcnow()
        data["is_active"] = True
        
        # Calculate total controls dynamically
        data["total_controls"] = len(data.get("controls", []))
        
        # Upsert by short_name
        await db["benchmarks"].update_one(
            {"short_name": data["short_name"]},
            {"$set": data},
            upsert=True
        )
        logger.info("Successfully seeded benchmark '%s' into database", data["name"])
