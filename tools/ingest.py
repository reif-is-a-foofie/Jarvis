import os
from typing import Dict, Any

def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest a local text file into vector memory.

    Args:
        args: {"path": "/absolute/or/relative/path"}
    Returns:
        {"ingested": path, "bytes": N}
    """
    path = args.get("path")
    if not path:
        return {"error": "missing_path"}
    if not os.path.exists(path):
        return {"error": "not_found"}
    try:
        from main_graph import ingest as _ingest
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
        _ingest(data, src=f"file:{os.path.abspath(path)}")
        return {"ingested": path, "bytes": len(data)}
    except Exception as e:
        return {"error": "ingest_failed", "detail": str(e)}

