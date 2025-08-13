from typing import Dict, Any
import csv

def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate a CSV of transactions by category.

    Args: {"path": "transactions.csv", "amount_field": "amount", "category_field": "category"}
    Returns: {"totals": {"category": sum}, "rows": N}
    """
    path = args.get("path")
    if not path:
        return {"error": "missing_path"}
    amount_field = args.get("amount_field", "amount")
    category_field = args.get("category_field", "category")
    totals: Dict[str, float] = {}
    rows = 0
    try:
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                rows += 1
                try:
                    cat = (row.get(category_field) or "uncategorized").strip()
                    amt = float(row.get(amount_field) or 0)
                except Exception:
                    continue
                totals[cat] = totals.get(cat, 0.0) + amt
        return {"totals": totals, "rows": rows}
    except Exception as e:
        return {"error": "csv_failed", "detail": str(e)}


