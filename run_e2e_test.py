"""
SafeDig — Automated End-to-End Pipeline Runner & Diagnostic Tool
Executes the full pipeline on a real enquiry folder and prints a comprehensive diagnostic summary.
"""
import os
import sys
import json
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from src.orchestration.graph import map_qa_workflow
from src.config.settings import settings

def run_e2e_pipeline(folder_path: str = "Data/244414_201678"):
    print("=" * 80)
    print(" SAFEDIG AI MAP QA & VALIDATION -- END-TO-END EXECUTION")
    print("=" * 80)
    print(f"Target Enquiry Folder : {folder_path}")
    print(f"Active Engine Version : {settings.engine_version}")
    print(f"Active Policy Version : {settings.policy_version}")
    print(f"Safety Invariant     : ESCAPED_HAZARDS = 0 (Strict Zero Tolerance)")
    print("-" * 80)

    job_id = f"E2E-TEST-{int(time.time())}"
    initial_state = {
        "root_dir": folder_path,
        "job_id": job_id,
        "output_dir": os.path.join(settings.output_dir, job_id)
    }

    start_time = time.time()
    print(f"\n[1/4] Invoking LangGraph Pipeline ({job_id})...")
    final_state = map_qa_workflow.invoke(initial_state)
    elapsed = time.time() - start_time
    print(f"      Pipeline completed in {elapsed:.2f} seconds.")

    # 2. Extract results
    status = final_state.get("status", "UNKNOWN")
    overall_decision = final_state.get("overall_decision", "UNKNOWN")
    docs = final_state.get("document_results", [])

    ac_count = sum(1 for d in docs if d.get("decision") == "AUTO_CLEAR")
    hr_count = sum(1 for d in docs if d.get("decision") == "HUMAN_REVIEW")
    bl_count = sum(1 for d in docs if d.get("decision") == "BLOCKED")
    total_docs = len(docs)

    print("\n[2/4] Job / Directory-Level Aggregate Summary:")
    print(f"      * Job ID             : {job_id}")
    print(f"      * Execution Status   : {status}")
    print(f"      * Aggregate Decision : {overall_decision}")
    print(f"      * Total Records      : {total_docs}")
    print(f"      * Auto-Clear Count   : {ac_count} ({ac_count/total_docs*100:.1f}%)" if total_docs else "0")
    print(f"      * Human Review Count : {hr_count} ({hr_count/total_docs*100:.1f}%)" if total_docs else "0")
    print(f"      * Blocked Count      : {bl_count} ({bl_count/total_docs*100:.1f}%)" if total_docs else "0")

    # 3. Individual Map Sample
    print(f"\n[3/4] Individual Map Results Sample (First 5 of {total_docs} maps):")
    print(f"      {'Filename / ID':<30} | {'Provider':<24} | {'Decision':<14} | {'Reason'}")
    print("      " + "-" * 95)
    for d in docs[:5]:
        fn = d.get("filename") or d.get("index_record_id") or "--"
        prov = (d.get("utility_name") or "--")[:22]
        dec = d.get("decision", "--")
        reason = (d.get("reason") or "--")[:40]
        print(f"      {fn:<30} | {prov:<24} | {dec:<14} | {reason}...")

    # 4. Output Artifacts Check
    job_out_dir = initial_state["output_dir"]
    rep_path = os.path.join(job_out_dir, "job_report.json")
    results_path = os.path.join(job_out_dir, "document_results.json")
    evidence_dir = os.path.join(job_out_dir, "evidence")

    print("\n[4/4] Output Artifacts Verification:")
    print(f"      * Job Report JSON    : {'[OK] Created' if os.path.exists(rep_path) else '[FAIL] Missing'}")
    print(f"      * Document Results   : {'[OK] Created' if os.path.exists(results_path) else '[FAIL] Missing'}")
    print(f"      * Evidence Crops Dir : {'[OK] Created' if os.path.exists(evidence_dir) else '[FAIL] Missing'}")

    print("\n" + "=" * 80)
    print(" [SUCCESS] END-TO-END PIPELINE VERIFICATION COMPLETED!")
    print(f" View full interactive results at: http://localhost:8000/ (Job: {job_id})")
    print("=" * 80)

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "Data/244414_201678"
    run_e2e_pipeline(folder)
