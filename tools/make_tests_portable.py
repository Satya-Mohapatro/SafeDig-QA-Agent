import os
import glob
import re

TESTS_DIR = os.path.join(os.path.dirname(__file__), "..", "tests")

# Pattern matching d:/Safedig_AG/Data/... or d:\Safedig_AG\Data\...
PATTERNS = [
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]244414_201678[/\\]42332089_NGED - Wales\.pdf"'), 'str(SAMPLE_NGED_PDF)'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]244414_201678"'), 'str(SAMPLE_FOLDER_244414)'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata"'), 'str(DATA_DIR)'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]299208_172565"'), 'str(DATA_DIR / "299208_172565")'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]534668_175407"'), 'str(DATA_DIR / "534668_175407")'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]550782_169179"'), 'str(DATA_DIR / "550782_169179")'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\][dD]ata[/\\]Sample1"'), 'str(DATA_DIR / "Sample1")'),
    (re.compile(r'r?"[dD]:[/\\][sS]afedig_AG[/\\]NonExistentFolder_999"'), 'str(PROJECT_ROOT / "NonExistentFolder_999")'),
]

IMPORT_LINE = "from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF\n"

for filepath in glob.glob(os.path.join(TESTS_DIR, "**", "*.py"), recursive=True):
    if "conftest.py" in filepath:
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False
    new_content = content
    for pattern, replacement in PATTERNS:
        if pattern.search(new_content):
            new_content = pattern.sub(replacement, new_content)
            modified = True

    if modified:
        # Check if import is already present
        if "from tests.conftest import" not in new_content:
            # Insert import after the last import line or at top
            lines = new_content.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_idx = i + 1
            lines.insert(insert_idx, "from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF")
            new_content = "\n".join(lines) + "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated: {filepath}")

print("All tests made portable successfully!")
