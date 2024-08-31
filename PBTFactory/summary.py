from typing import Dict, List


def summary(results: List[Dict]) -> Dict[str, float]:
    summary = {"success": 0, "error": 0, "score_total": 0.0, "score_avg": 0.0}

    for r in results:
        if "error" in r:
            summary["error"] += 1
        else:
            summary["success"] += 1
            summary["score_total"] += r.get("killed_percent", 0.0)

    if summary["success"] > 0:
        summary["score_avg"] = summary["score_total"] / summary["success"]

    return summary
