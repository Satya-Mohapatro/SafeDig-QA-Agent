import re
from typing import List, Dict, Tuple
from src.domain.index_record import IndexRecord
from src.domain.document import DiscoveredFile
from src.domain.enums import DocumentResolutionStatus, FileClassification
from src.config.logging import logger

# Canonical mapping aliases with precise utility discrimination
UTILITY_ALIASES = {
    "national grid electricity distribution": ["nged", "wales", "western power", "national grid electricity"],
    "national grid electricity transmission": ["nget", "national grid transmission"],
    "national gas transmission": ["ngt", "national gas"],
    "wales and west utilities": ["wwu", "wales and west", "wales & west"],
    "wales & west utilities ltd": ["wwu", "wales and west", "wales & west"],
    "welsh water": ["w.pdf", "welsh water", "dwrcymru", "dwr cymru"],
    "gtc-gas": ["gtc.pdf", "gtc-gas", "gtc_gas"],
    "gtc-electricity": ["gtc.pdf", "gtc-electricity", "gtc_electricity"],
    "gtc-water": ["gtc.pdf", "gtc-water", "gtc_water"],
    "gtc-fibre": ["gtc.pdf", "gtc-fibre", "gtc_fibre"],
    "bt": ["bt.pdf", "openreach", "british telecom"],
    "vm": ["vm.pdf", "virgin", "virgin media"],
    "uk power networks": ["ukpn", "uk power networks", "uk power distribution"],
    "sgn": ["sgn", "scotia gas"],
    "cadent gas": ["cadent", "cadentgas"],
    "cadentgas": ["cadent", "cadentgas"],
    "thames water": ["thames", "thames_water", "thames water"],
    "southern water": ["southern_water", "southern water"],
    "clean_water": ["clean_water.pdf", "clean_water", "clean water"],
    "waste_water": ["waste_water.pdf", "waste_water", "waste water", "sewer"],
    "esp utilities group": ["esp", "esp utilities", "esp_utilities"],
    "scottish and southern electricity networks": ["ssen", "scottish and southern"],
    "electricity north west limited": ["enwl", "electricity north west"],
}

def resolve_documents(
    records: List[IndexRecord],
    discovered_files: List[DiscoveredFile]
) -> Tuple[List[IndexRecord], Dict[str, DiscoveredFile]]:
    map_files = [f for f in discovered_files if f.classification == FileClassification.MAP]
    resolved_map: Dict[str, DiscoveredFile] = {}
    
    for rec in records:
        if not rec.is_asset_present:
            rec.resolution_status = DocumentResolutionStatus.EXCLUDED
            continue
            
        matches: List[DiscoveredFile] = []
        
        # 1. Exact or partial filename match if rec.file_name is provided in index
        if rec.file_name:
            target_fn = rec.file_name.lower().strip()
            for mf in map_files:
                mf_fn = mf.filename.lower().strip()
                if target_fn == mf_fn or target_fn in mf_fn or mf_fn in target_fn:
                    if mf not in matches:
                        matches.append(mf)
                        
        # 2. Provider / UtilityName matching if no match yet
        if not matches and rec.utility_name:
            u_clean = rec.utility_name.lower().strip()
            aliases = UTILITY_ALIASES.get(u_clean, [u_clean])
            
            for mf in map_files:
                mf_fn = mf.filename.lower()
                for alias in aliases:
                    alias_clean = alias.lower().strip()
                    if alias_clean.endswith(".pdf"):
                        if mf_fn == alias_clean:
                            if mf not in matches:
                                matches.append(mf)
                    elif "_" in alias_clean or "-" in alias_clean or " " in alias_clean:
                        if alias_clean in mf_fn:
                            if mf not in matches:
                                matches.append(mf)
                    else:
                        # Word boundary match for short acronyms like 'bt', 'vm', 'esp', 'wwu'
                        if re.search(r'(?i)(?<![a-z0-9])' + re.escape(alias_clean) + r'(?![a-z0-9])', mf_fn):
                            if mf not in matches:
                                matches.append(mf)
                                
        # Evaluate matched candidates
        if len(matches) == 1:
            matched_file = matches[0]
            rec.resolution_status = DocumentResolutionStatus.UNIQUE
            rec.resolved_file_id = matched_file.file_id
            rec.file_name = matched_file.filename
            resolved_map[rec.index_record_id] = matched_file
        elif len(matches) > 1:
            # Check for exact filename match preference
            exact = [m for m in matches if rec.file_name and m.filename.lower() == rec.file_name.lower()]
            if len(exact) == 1:
                matched_file = exact[0]
                rec.resolution_status = DocumentResolutionStatus.UNIQUE
                rec.resolved_file_id = matched_file.file_id
                rec.file_name = matched_file.filename
                resolved_map[rec.index_record_id] = matched_file
            else:
                # Prefer main map over polygon overlay if one contains 'polygon'
                non_poly = [m for m in matches if "polygon" not in m.filename.lower()]
                if len(non_poly) == 1:
                    matched_file = non_poly[0]
                    rec.resolution_status = DocumentResolutionStatus.UNIQUE
                    rec.resolved_file_id = matched_file.file_id
                    rec.file_name = matched_file.filename
                    resolved_map[rec.index_record_id] = matched_file
                else:
                    rec.resolution_status = DocumentResolutionStatus.AMBIGUOUS
                    logger.warning(f"Ambiguous mapping for row {rec.row_index} '{rec.utility_name}': {[m.filename for m in matches]}")
        else:
            rec.resolution_status = DocumentResolutionStatus.MISSING
            logger.warning(f"Missing map file for row {rec.row_index} '{rec.utility_name}' (Status='Yes')")
            
    logger.info(f"Resolved {len(resolved_map)} unique documents out of {len(records)} index records.")
    return records, resolved_map
