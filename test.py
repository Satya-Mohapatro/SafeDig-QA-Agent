from src.orchestration.graph import map_qa_workflow
# Submit a folder to the LangGraph pipeline
initial_state = {
    "root_dir": "D:/SafeDig_AG/Data/547835_156740",
    "job_id": "JOB-MANUAL-TEST"
}
final_state = map_qa_workflow.invoke(initial_state)
print("Job Status:", final_state.get("status"))
print("Overall Decision:", final_state.get("overall_decision"))
print("Items in Human Review Queue:", len(final_state.get("human_review_queue", [])))