import os
import pytest
import pandas as pd
import pymupdf
from src.utils.paths import select_best_index_workbook, resolve_index_path
from src.pipeline import run_map_qa_pipeline
from src.domain.enums import Decision

def create_blank_pdf(path: str):
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    doc.save(path)
    doc.close()

def test_toilet_and_hospital_map_resolution_via_index_org(tmp_path):
    job_dir = tmp_path / 'job_folder'
    job_dir.mkdir()
    
    # 1. Create PDFs
    toilet_pdf = job_dir / 'Nearest_Toilet.pdf'
    hospital_pdf = job_dir / 'Nearest_Hospital.pdf'
    create_blank_pdf(str(toilet_pdf))
    create_blank_pdf(str(hospital_pdf))
    
    # 2. Create index.xlsx (WITHOUT FileName column)
    df_index = pd.DataFrame([
        {'UtilityName': 'Toilet Map', 'UtilityType': 'Toilet', 'Status': 'Yes'},
        {'UtilityName': 'Hospital Map', 'UtilityType': 'Hospital', 'Status': 'Yes'},
    ])
    df_index.to_excel(job_dir / 'index.xlsx', index=False)
    
    # 3. Create index_org.xlsx (WITH FileName column)
    df_index_org = pd.DataFrame([
        {'FileName': 'Nearest_Toilet.pdf', 'UtilityName': 'Toilet Map', 'UtilityType': 'Toilet', 'Status': 'Yes'},
        {'FileName': 'Nearest_Hospital.pdf', 'UtilityName': 'Hospital Map', 'UtilityType': 'Hospital', 'Status': 'Yes'},
    ])
    df_index_org.to_excel(job_dir / 'index_org.xlsx', index=False)
    
    # 4. Verify select_best_index_workbook prefers index_org.xlsx based on schema
    candidates = [str(job_dir / 'index.xlsx'), str(job_dir / 'index_org.xlsx')]
    best_file, reason = select_best_index_workbook(candidates)
    assert os.path.basename(best_file) == 'index_org.xlsx'
    assert 'FileName' in reason
    
    # 5. Verify resolve_index_path chooses index_org.xlsx
    resolved_idx = resolve_index_path(str(job_dir))
    assert os.path.basename(resolved_idx) == 'index_org.xlsx'
    
    # 6. Run pipeline on the job folder
    res = run_map_qa_pipeline(str(job_dir), job_id='TEST-TOILET-HOSPITAL')
    
    results = res.get('results', [])
    assert len(results) == 2
    
    toilet_res = next((r for r in results if r.get('utility_name') == 'Toilet Map'), None)
    hospital_res = next((r for r in results if r.get('utility_name') == 'Hospital Map'), None)
    
    assert toilet_res is not None
    assert hospital_res is not None
    
    # Exact FileName resolution
    assert toilet_res.get('filename') == 'Nearest_Toilet.pdf'
    assert hospital_res.get('filename') == 'Nearest_Hospital.pdf'
    
    # Neither should produce missing map errors
    assert "Expected map for 'Toilet Map' was not found in job folder." not in toilet_res.get('reason', '')
    assert "Expected map for 'Hospital Map' was not found in job folder." not in hospital_res.get('reason', '')


def test_fallback_when_only_index_xlsx_exists(tmp_path):
    job_dir = tmp_path / 'job_fallback'
    job_dir.mkdir()
    
    df_index = pd.DataFrame([
        {'UtilityName': 'Cadent Gas', 'UtilityType': 'Gas', 'Status': 'No'},
    ])
    df_index.to_excel(job_dir / 'index.xlsx', index=False)
    
    resolved_idx = resolve_index_path(str(job_dir))
    assert os.path.basename(resolved_idx) == 'index.xlsx'
