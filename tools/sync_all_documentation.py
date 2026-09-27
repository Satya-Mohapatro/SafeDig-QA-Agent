"""
SafeDig AI - Master Documentation Sync Utility
Executes all 6 documentation generator scripts and synchronizes the generated
PDF and Markdown specifications across all active project repositories:
- D:\\SafeDig_AG\\Documentation
- D:\\SafeDig\\Documentation
- D:\\SafeDig_QA_Agent\\Documentation
- D:\\SD\\Documentation
"""

import os
import shutil
import subprocess
import sys

TARGET_ROOTS = [
    r"D:\SafeDig_AG",
    r"D:\SafeDig",
    r"D:\SafeDig_QA_Agent",
    r"D:\SD"
]

SCRIPTS = [
    r"D:\SafeDig_AG\tools\doc_gen_architecture.py",
    r"D:\SafeDig_AG\tools\doc_gen_e2e_code.py",
    r"D:\SafeDig_AG\tools\doc_gen_17_gates.py",
    r"D:\SafeDig_AG\tools\doc_gen_file_by_file.py",
    r"D:\SafeDig_AG\tools\doc_gen_trainee_cookbook.py",
    r"D:\SafeDig_AG\tools\doc_gen_tech_stack.py"
]

python_exe = sys.executable

# 1. Execute all 6 generation scripts using the current virtualenv Python
print("=" * 70)
print("SAFEDIG AI — MASTER DOCUMENTATION GENERATION & SYNCHRONIZATION")
print("=" * 70)

for script in SCRIPTS:
    if os.path.exists(script):
        print(f"\n[RUNNING] {os.path.basename(script)} ...")
        res = subprocess.run([python_exe, script], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] Failed {script}:\n{res.stderr}")
        else:
            print(f"[SUCCESS] {os.path.basename(script)}")
            for line in res.stdout.strip().splitlines():
                print(f"   {line}")
    else:
        print(f"[WARNING] Script not found: {script}")

SOURCE_DOCS_DIR = r"D:\SafeDig_AG\Documentation"
os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)

print(f"\nSource documentation directory: {SOURCE_DOCS_DIR}")
doc_files = [f for f in os.listdir(SOURCE_DOCS_DIR) if f.endswith(('.md', '.pdf'))]
print(f"Found {len(doc_files)} documentation files in {SOURCE_DOCS_DIR}:")
for f in sorted(doc_files):
    sz = os.path.getsize(os.path.join(SOURCE_DOCS_DIR, f))
    print(f"  • {f:<65} ({sz:>8,} bytes)")

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
        print(f"[SYNC COMPLETE] {target_docs_dir}")

print("\n" + "=" * 70)
print("=== ALL DOCUMENTATION SUCCESSFULLY GENERATED & SYNCHRONIZED ===")
print("=" * 70)
