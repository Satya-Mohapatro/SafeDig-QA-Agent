@echo off
echo ===================================================
echo Starting SafeDig AI Map QA in Production Mode...
echo ===================================================

python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --workers 4
pause
