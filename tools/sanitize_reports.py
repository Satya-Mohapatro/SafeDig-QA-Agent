import os
import json
from pathlib import Path
from src.config.settings import settings
from src.config.logging import logger

def sanitize_job_reports():
    output_dir = settings.output_dir
    if not output_dir.exists():
        print(f'No output directory at {output_dir}')
        return
        
    count = 0
    for root, _, files in os.walk(str(output_dir)):
        for f in files:
            if f == 'job_report.json':
                report_path = os.path.join(root, f)
                try:
                    with open(report_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    
                    old_root = data.get('root_dir', '')
                    if old_root:
                        norm = old_root.replace('\\\\', '/')
                        norm_lower = norm.lower()
                        if '/data/' in norm_lower:
                            sub_rel = norm[norm_lower.index('/data/') + 6:].strip('/')
                            new_root = f'Data/{sub_rel}'
                        else:
                            folder_base = os.path.basename(norm.rstrip('/'))
                            new_root = f'Data/{folder_base}'
                            
                        if new_root != old_root:
                            data['root_dir'] = new_root
                            with open(report_path, 'w', encoding='utf-8') as jf:
                                json.dump(data, jf, indent=2)
                            count += 1
                except Exception as e:
                    logger.warning(f'Could not sanitize {report_path}: {e}')
                    
    print(f'Sanitized {count} job_report.json files to portable relative paths.')

if __name__ == '__main__':
    sanitize_job_reports()
