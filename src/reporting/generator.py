import os
import json
from typing import List, Dict, Any
from datetime import datetime

def generate_job_reports(
    job_id: str,
    root_dir: str,
    results: List[Dict[str, Any]],
    output_dir: str
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    total = len(results)
    auto_clear = sum(1 for r in results if r.get("decision") == "AUTO_CLEAR")
    human_review = sum(1 for r in results if r.get("decision") == "HUMAN_REVIEW")
    blocked = sum(1 for r in results if r.get("decision") == "BLOCKED")
    overall_decision = "BLOCKED" if blocked > 0 else ("HUMAN_REVIEW" if human_review > 0 else "AUTO_CLEAR")



    job_report = {
        "job_id": job_id,
        "root_dir": root_dir,
        "overall_decision": overall_decision,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_documents": total,
            "auto_clear_count": auto_clear,
            "auto_clear_pct": round((auto_clear / total) * 100, 1) if total > 0 else 0,
            "human_review_count": human_review,
            "human_review_pct": round((human_review / total) * 100, 1) if total > 0 else 0,
            "blocked_count": blocked,
            "blocked_pct": round((blocked / total) * 100, 1) if total > 0 else 0,
        },
        "results": results
    }

    
    job_report_path = os.path.join(output_dir, "job_report.json")
    with open(job_report_path, "w", encoding="utf-8") as f:
        json.dump(job_report, f, indent=2)
        
    doc_results_path = os.path.join(output_dir, "document_results.json")
    with open(doc_results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    return {
        "job_report_path": job_report_path,
        "document_results_path": doc_results_path
    }
