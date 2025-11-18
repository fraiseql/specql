import json
from pathlib import Path
from typing import Dict, Set, List
from datetime import datetime


class IncrementalTracker:
    """Track file modifications for incremental processing"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.state_file = self.output_dir / ".specql_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, dict]:
        """Load previous processing state"""
        if not self.state_file.exists():
            return {}
        return json.loads(self.state_file.read_text())

    def _save_state(self):
        """Save current processing state"""
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def needs_processing(self, file_path: Path) -> bool:
        """Check if file needs to be processed"""
        file_key = str(file_path.absolute())

        if file_key not in self.state:
            return True

        current_mtime = file_path.stat().st_mtime
        previous_mtime = self.state[file_key].get("mtime", 0)

        return current_mtime > previous_mtime

    def mark_processed(self, file_path: Path, result: dict):
        """Mark file as processed"""
        file_key = str(file_path.absolute())
        self.state[file_key] = {
            "mtime": file_path.stat().st_mtime,
            "hash": hash(file_path.read_bytes()) if file_path.exists() else None,
            "timestamp": datetime.now().isoformat(),
            "output": result.get("output_file"),
        }
        self._save_state()

    def get_changed_files(self, all_files: List[Path]) -> Set[Path]:
        """Get list of files that have changed"""
        return {f for f in all_files if self.needs_processing(f)}
