import hashlib
import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime


class CacheManager:
    """Manage caching for reverse engineering operations"""

    def __init__(self, cache_dir: str = "~/.specql/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_hash(self, file_path: str, options: dict) -> str:
        """Compute hash of file content + options"""
        content = Path(file_path).read_text()

        # Include file content + CLI options in hash
        hash_input = f"{content}:{json.dumps(options, sort_keys=True)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def get_cached(self, file_path: str, options: dict) -> Optional[dict]:
        """Get cached result if available and valid"""
        cache_key = self._compute_hash(file_path, options)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if source file has been modified since cache
        cache_mtime = cache_file.stat().st_mtime
        source_mtime = Path(file_path).stat().st_mtime

        if source_mtime and source_mtime > cache_mtime:
            # Source file modified, invalidate cache
            cache_file.unlink()
            return None

        # Return cached result
        return json.loads(cache_file.read_text())

    def set_cached(self, file_path: str, options: dict, result: dict):
        """Store result in cache"""
        cache_key = self._compute_hash(file_path, options)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "options": options,
            "result": result,
        }

        cache_file.write_text(json.dumps(cache_data, indent=2))

    def clear_cache(self, older_than_days: int = None):
        """Clear cache (optionally only old entries)"""
        if older_than_days:
            cutoff = datetime.now().timestamp() - (older_than_days * 86400)
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.stat().st_mtime < cutoff:
                    cache_file.unlink()
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
