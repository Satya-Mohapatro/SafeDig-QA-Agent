"""
SafeDig AI - Master Documentation Sync Utility
Generates and populates all 5 technical PDF & Markdown documentation files across all project targets:
- D:\\SafeDig_AG\\Documentation
- D:\\SafeDig_QA_Agent\\Documentation
- D:\\SD\\Documentation
"""

import os
import shutil
import subprocess
import sys

TARGET_ROOTS = [
    r"D:\SafeDig_AG",
    r"D:\SafeDig_QA_Agent",
    r"D:\SD"
]

SCRIPTS = [
    r"D:\SafeDig_AG\tools\generate_17_gates_doc.py",
    r"D:\SafeDig_AG\tools\generate_all_docs.py",
    r"D:\SafeDig_AG\tools\generate_e2e_code_working_doc.py"
]

python_exe = sys.executable

# 1. Execute all 3 generation scripts using the current virtualenv Python
for script in SCRIPTS:
    if os.path.exists(script):
        print(f"[RUNNING] {script} ...")
        res = subprocess.run([python_exe, script], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] Failed {script}: {res.stderr}")
        else:
            print(f"[SUCCESS] {script}")

SOURCE_DOCS_DIR = r"D:\SafeDig_AG\Documentation"
os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)

# Also ensure Tech Stack files from D:\SD\Documentation are in SOURCE_DOCS_DIR if missing
for tech_f in ["SafeDig_Technology_Stack_Specification.md", "SafeDig_Technology_Stack_Specification.pdf"]:
    src_tech = os.path.join(r"D:\SD\Documentation", tech_f)
    dst_tech = os.path.join(SOURCE_DOCS_DIR, tech_f)
    if os.path.exists(src_tech) and not os.path.exists(dst_tech):
        shutil.copy2(src_tech, dst_tech)
        print(f"[COPIED] {tech_f} to {SOURCE_DOCS_DIR}")

print(f"Source docs directory: {SOURCE_DOCS_DIR}")
doc_files = os.listdir(SOURCE_DOCS_DIR)
print(f"Found {len(doc_files)} documentation files in {SOURCE_DOCS_DIR}:")
for f in doc_files:
    print(f"  - {f} ({os.path.getsize(os.path.join(SOURCE_DOCS_DIR, f))} bytes)")

# 2. Replicate Documentation directory to all target roots
for root in TARGET_ROOTS:
    if os.path.exists(root):
        target_docs_dir = os.path.join(root, "Documentation")
        os.makedirs(target_docs_dir, exist_ok=True)
        print(f"\nSyncing to {target_docs_dir} ...")
        for f in doc_files:
            src_f = os.path.join(SOURCE_DOCS_DIR, f)
            dst_f = os.path.join(target_docs_dir, f)
            if os.path.abspath(src_f) != os.path.abspath(dst_f):
                shutil.copy2(src_f, dst_f)
            # Also copy root-level PDFs
            if f.endswith(".pdf"):
                root_pdf_dst = os.path.join(root, f)
                if os.path.abspath(src_f) != os.path.abspath(root_pdf_dst):
                    shutil.copy2(src_f, root_pdf_dst)
        print(f"[SYNC COMPLETE] {root}")

print("\n=== ALL DOCUMENTATION SYNCHRONIZED SUCCESSFULLY ===")
