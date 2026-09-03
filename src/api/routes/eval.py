import os
import json
from fastapi import APIRouter, HTTPException
from src.eval.models import BenchmarkReport
from src.eval import benchmark_runner
from src.config.settings import settings

router = APIRouter(prefix="/eval", tags=["QA Agent Evaluation & Benchmarks"])

@router.post("/run", response_model=BenchmarkReport)
def run_evaluation_benchmark():
    report = benchmark_runner.run_benchmark()
    return report

@router.get("/latest", response_model=BenchmarkReport)
def get_latest_benchmark_report():
    latest_file = os.path.join(settings.output_dir, "benchmarks", "latest_eval_report.json")
    if not os.path.exists(latest_file):
        # Trigger an initial benchmark run if not yet generated
        return benchmark_runner.run_benchmark()
        
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BenchmarkReport(**data)
