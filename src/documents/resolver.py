import re
from typing import List, Dict, Tuple
from src.domain.index_record import IndexRecord
from src.domain.document import DiscoveredFile
from src.domain.enums import DocumentResolutionStatus, FileClassification
from src.config.logging import logger

def _normalize_utility_key(name: str) -> str:
    """Normalize utility name into a canonical search key."""
    if not name:
        return ""
    # Replace en-dash, em-dash, unicode replacement chars, hyphens, underscores
    cleaned = name.lower().strip()
    cleaned = re.sub(r'[\u2013\u2014\ufffd_\-]+', ' ', cleaned)
    cleaned = re.sub(r'[^a-z0-9 ]', ' ', cleaned)
    tokens = cleaned.split()
    if not tokens:
        return ""
    if "tfl" in tokens:
        return "tfl"
    return " ".join(tokens)

# Canonical mapping aliases with comprehensive coverage of all UK utilities and map types
UTILITY_ALIASES: Dict[str, List[str]] = {
    "national grid electricity distribution": [
        "nged", "wales", "western power", "national grid electricity distribution"
    ],
    "national grid electricity transmission": [
        "national grid electricity", "nget", "national grid electricity transmission", "national grid transmission"
    ],
    "national gas transmission": [
        "ngt", "national gas", "national gas transmission"
    ],
    "wales and west utilities": [
        "wwu", "wales and west", "wales & west"
    ],
    "wales and west utilities ltd": [
        "wwu", "wales and west", "wales & west"
    ],
    "welsh water": [
        "w.pdf", "welsh water", "dwrcymru", "dwr cymru"
    ],
    "gtc gas": [
        "gtc.pdf", "gtc", "gtc gas", "gtc-gas", "gtc_gas"
    ],
    "gtc electricity": [
        "gtc.pdf", "gtc", "gtc-electricity", "gtc_electricity"
    ],
    "gtc water": [
        "gtc.pdf", "gtc", "gtc-water", "gtc_water"
    ],
    "gtc fibre": [
        "gtc.pdf", "gtc", "gtc-fibre", "gtc_fibre"
    ],
    "bt": [
        "bt.pdf", "openreach", "british telecom"
    ],
    "vm": [
        "vm.pdf", "virgin", "virgin media"
    ],
    "uk power networks": [
        "ukpn", "uk power networks", "uk power distribution"
    ],
    "sgn": [
        "sgn", "scotia gas"
    ],
    "cadent gas": [
        "cadent", "cadentgas"
    ],
    "clean water": [
        "clean_water.pdf", "clean_water", "clean water", "cleanwater"
    ],
    "waste water": [
        "waste_water.pdf", "waste_water", "waste water", "wastewater", "sewer"
    ],
    "esp utilities group": [
        "esp", "esp utilities", "esp utilities group", "esp_utilities"
    ],
    "esp utilities": [
        "esp", "esp utilities", "esp utilities group", "esp_utilities"
    ],
    "toilet map": [
        "nearest_toilet.pdf", "nearest_toilet", "toilet"
    ],
    "hospital map": [
        "nearest_hospital.pdf", "nearest_hospital", "hospital"
    ],
    "tfl": [
        "tfl", "london underground", "tfl_r", "tfl london underground"
    ],
    "scottish and southern electricity networks": [
        "ssen", "scottish and southern"
    ],
    "electricity north west limited": [
        "enwl", "electricity north west"
    ],
    "thames water": [
        "thames", "thames_water", "thames water"
    ],
    "southern water": [
        "southern_water", "southern water"
    ],
}

def resolve_documents(
    records: List[IndexRecord],
    discovered_files: List[DiscoveredFile]
) -> Tuple[List[IndexRecord], Dict[str, DiscoveredFile]]:
    """Map index records to discovered files deterministically and auditably."""
    map_files = [f for f in discovered_files if f.classification == FileClassification.MAP]
    # Fallback to all files if no maps discovered
    search_files = map_files if map_files else discovered_files
    resolved_map: Dict[str, DiscoveredFile] = {}
    
    for rec in records:
        if not rec.is_asset_present:
            rec.resolution_status = DocumentResolutionStatus.EXCLUDED
            continue
            
        matches: List[DiscoveredFile] = []
        resolution_notes = []
        
        # 1. Exact or partial filename match if rec.file_name is provided in index
        if rec.file_name:
            candidates = [c.strip() for c in re.split(r'[,;]', rec.file_name) if c.strip()]
            candidate_matches: List[Tuple[int, DiscoveredFile]] = []
            
            # Pass 1a: exact filename match against discovered_files
            for cand_idx, cand in enumerate(candidates):
                cand_lower = cand.lower().strip()
                for df in discovered_files:
                    if df.filename.lower().strip() == cand_lower:
                        if not any(m.file_id == df.file_id for _, m in candidate_matches):
                            candidate_matches.append((cand_idx, df))
                            resolution_notes.append(f"exact filename '{df.filename}'")
                            
            # Pass 1b: if no exact matches, check containment
            if not candidate_matches:
                for cand_idx, cand in enumerate(candidates):
                    cand_lower = cand.lower().strip()
                    for df in search_files:
                        df_lower = df.filename.lower().strip()
                        if cand_lower in df_lower or df_lower in cand_lower:
                            if not any(m.file_id == df.file_id for _, m in candidate_matches):
                                candidate_matches.append((cand_idx, df))
                                resolution_notes.append(f"contained filename '{df.filename}'")
                                
            # Extract matched files in priority order
            if candidate_matches:
                candidate_matches.sort(key=lambda x: x[0])
                matches = [m for _, m in candidate_matches]
                        
        # 2. Provider / UtilityName matching if no match yet
        if not matches and rec.utility_name:
            u_norm = _normalize_utility_key(rec.utility_name)
            aliases = UTILITY_ALIASES.get(u_norm, [u_norm])
            
            for mf in search_files:
                mf_fn = mf.filename.lower()
                for alias in aliases:
                    alias_clean = alias.lower().strip()
                    if alias_clean.endswith(".pdf"):
                        if mf_fn == alias_clean:
                            if mf not in matches:
                                matches.append(mf)
                                resolution_notes.append(f"alias '{alias}' exact match '{mf.filename}'")
                    elif "_" in alias_clean or "-" in alias_clean or " " in alias_clean:
                        if alias_clean in mf_fn:
                            if mf not in matches:
                                matches.append(mf)
                                resolution_notes.append(f"alias '{alias}' substring match '{mf.filename}'")
                    else:
                        # Word boundary match for short acronyms like 'bt', 'vm', 'esp', 'wwu', 'tfl'
                        if re.search(r'(?i)(?<![a-z0-9])' + re.escape(alias_clean) + r'(?![a-z0-9])', mf_fn):
                            if mf not in matches:
                                matches.append(mf)
                                resolution_notes.append(f"alias '{alias}' word match '{mf.filename}'")
                                
        # Evaluate matched candidates
        if len(matches) == 1:
            matched_file = matches[0]
            rec.resolution_status = DocumentResolutionStatus.UNIQUE
            rec.resolved_file_id = matched_file.file_id
            rec.file_name = matched_file.filename
            resolved_map[rec.index_record_id] = matched_file
            if resolution_notes:
                rec.raw_comments = (rec.raw_comments or "") + f" [Resolved via: {resolution_notes[0]}]"
        elif len(matches) > 1:
            # Prefer first exact candidate if specified in index
            if rec.file_name:
                first_cand = candidates[0].lower().strip()
                first_exact = [m for m in matches if m.filename.lower().strip() == first_cand]
                if len(first_exact) == 1:
                    matched_file = first_exact[0]
                    rec.resolution_status = DocumentResolutionStatus.UNIQUE
                    rec.resolved_file_id = matched_file.file_id
                    rec.file_name = matched_file.filename
                    resolved_map[rec.index_record_id] = matched_file
                    continue

            # Prefer main utility map over secondary/environmental overlays
            non_secondary = [
                m for m in matches if not any(
                    tok in m.filename.lower() for tok in ["sssi", "polygon", "overlay", "boundary", "booklet", "letter"]
                )
            ]
            if len(non_secondary) == 1:
                matched_file = non_secondary[0]
                rec.resolution_status = DocumentResolutionStatus.UNIQUE
                rec.resolved_file_id = matched_file.file_id
                rec.file_name = matched_file.filename
                resolved_map[rec.index_record_id] = matched_file
            elif len(non_secondary) > 1:
                matched_file = non_secondary[0]
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
