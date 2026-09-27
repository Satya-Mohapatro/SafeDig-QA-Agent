"""Warning Catalogue & Legend Registry API Routes."""

import os
import openpyxl
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException

from src.utils.paths import resolve_catalogue_path
from src.legends.registry import master_legend_registry
from src.config.logging import logger

router = APIRouter(prefix="/catalogue", tags=["Warning Catalogue & Legends"])

_CATALOGUE_CACHE: Optional[Dict[str, Any]] = None


def load_authoritative_catalogue(force_reload: bool = False) -> Dict[str, Any]:
    """Parse warnings_list.xlsx and fuse with authoritative legend profiles."""
    global _CATALOGUE_CACHE
    if _CATALOGUE_CACHE and not force_reload:
        return _CATALOGUE_CACHE

    excel_path = resolve_catalogue_path()
    if not os.path.exists(excel_path):
        logger.error(f"Catalogue Excel not found at: {excel_path}")
        return {"stats": {}, "providers": []}

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        logger.error(f"Error reading {excel_path}: {e}")
        return {"stats": {}, "providers": []}

    data_rows = rows[1:] if len(rows) > 1 else []

    current_util = None
    current_type = None
    grouped: Dict[str, Dict[str, Any]] = {}

    for r in data_rows:
        if not r or len(r) < 3:
            continue
        util, utype, warning = r[0], r[1], r[2]
        status = r[3] if len(r) > 3 else None

        if util and str(util).strip() and str(util).strip() != ' ':
            current_util = str(util).strip()
        if utype and str(utype).strip() and str(utype).strip() != ' ':
            current_type = str(utype).strip()
        if not current_util:
            continue

        if current_util not in grouped:
            grouped[current_util] = {
                "utility_name": current_util,
                "utility_type": current_type or "General",
                "warnings": []
            }

        if warning and str(warning).strip() and str(warning).strip() != ' ':
            w_clean = str(warning).strip().rstrip('|').strip()
            st_clean = str(status).strip() if status else "Info"

            sev_norm = "INFO"
            if "HIGH" in st_clean.upper() or "CRITICAL" in st_clean.upper():
                sev_norm = "HIGH"
            elif "MED" in st_clean.upper():
                sev_norm = "MEDIUM"
            elif "LOW" in st_clean.upper():
                sev_norm = "LOW"

            grouped[current_util]["warnings"].append({
                "warning_text": w_clean,
                "raw_status": st_clean,
                "severity": sev_norm,
                "is_active_high": (sev_norm == "HIGH"),
                "policy": "BLOCKS ON AOI DETECTION" if sev_norm == "HIGH" else "ADVISORY ONLY"
            })

    # Standard Domain Symbology fallbacks when no bespoke profile exists
    DEFAULT_SYMBOLOGY = {
        "Gas": [
            {"description": "Gas Mains & Plant", "rgb": [255, 170, 0], "hex": "#FFAA00", "stroke_width": 1.2, "style": "solid", "labels": ["GAS", "MAINS"]}
        ],
        "Electricity": [
            {"description": "High Voltage / Underground Cables", "rgb": [255, 0, 0], "hex": "#FF0000", "stroke_width": 1.5, "style": "solid", "labels": ["HV", "CABLE", "11KV"]},
            {"description": "Low Voltage Electricity", "rgb": [0, 102, 204], "hex": "#0066CC", "stroke_width": 0.8, "style": "solid", "labels": ["LV"]}
        ],
        "Water": [
            {"description": "Clean Potable Water Distribution", "rgb": [0, 180, 255], "hex": "#00B4FF", "stroke_width": 1.0, "style": "solid", "labels": ["WATER", "POTABLE"]},
            {"description": "Waste / Foul Sewer", "rgb": [128, 0, 128], "hex": "#800080", "stroke_width": 1.0, "style": "solid", "labels": ["SEWER", "FOUL"]}
        ],
        "Telecom": [
            {"description": "Telecom Ducts & Fibre Optic", "rgb": [0, 150, 0], "hex": "#009600", "stroke_width": 0.8, "style": "dashed", "labels": ["TELECOM", "FIBRE", "DUCT"]}
        ],
        "Heat": [
            {"description": "District Heating Pipeline", "rgb": [255, 69, 0], "hex": "#FF4500", "stroke_width": 1.5, "style": "solid", "labels": ["HEATING", "HOT WATER"]}
        ]
    }

    providers_list = []
    total_warnings = 0
    high_count = 0
    med_count = 0
    low_count = 0
    auto_clear_count = 0

    for util_name, d in grouped.items():
        u_type = d["utility_type"]
        warnings = d["warnings"]
        total_warnings += len(warnings)

        u_high = sum(1 for w in warnings if w["severity"] == "HIGH")
        u_med = sum(1 for w in warnings if w["severity"] == "MEDIUM")
        u_low = sum(1 for w in warnings if w["severity"] == "LOW")

        high_count += u_high
        med_count += u_med
        low_count += u_low

        if len(warnings) == 0:
            auto_clear_count += 1

        prof = master_legend_registry.get_profile(util_name)
        legend_data = None

        if prof:
            features_list = []
            for f in prof.features:
                rgb = list(f.color.rgb) if f.color else [128, 128, 128]
                hex_col = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
                is_dashed = bool(f.stroke and f.stroke.dash_pattern)
                min_w = f.stroke.min_width_pt if f.stroke else 1.0
                features_list.append({
                    "feature_id": f.feature_id,
                    "warning_code": f.warning_code,
                    "description": f.description,
                    "geometry_type": f.geometry_type.value if hasattr(f.geometry_type, "value") else str(f.geometry_type),
                    "color_rgb": rgb,
                    "color_hex": hex_col,
                    "stroke_width": min_w,
                    "is_dashed": is_dashed,
                    "text_labels": f.text_labels or []
                })
            legend_data = {
                "legend_id": prof.legend_id,
                "version": prof.version,
                "source": "Authoritative Registry Profile",
                "is_authoritative": True,
                "features": features_list
            }
        else:
            fallback_features = DEFAULT_SYMBOLOGY.get(u_type, [
                {"description": f"{u_type} Plant & Apparatus", "rgb": [100, 116, 139], "hex": "#64748B", "stroke_width": 1.0, "is_dashed": False, "labels": [u_type.upper()]}
            ])
            features_list = []
            for idx, fb in enumerate(fallback_features):
                features_list.append({
                    "feature_id": f"{util_name.upper()[:6]}_{idx+1}",
                    "warning_code": f"{util_name.upper()[:6]}_{idx+1}",
                    "description": fb["description"],
                    "geometry_type": "LINE",
                    "color_rgb": fb["rgb"],
                    "color_hex": fb["hex"],
                    "stroke_width": fb.get("stroke_width", 1.0),
                    "is_dashed": (fb.get("style") == "dashed"),
                    "text_labels": fb.get("labels", [])
                })
            legend_data = {
                "legend_id": f"LGD-{u_type.upper()}-STD",
                "version": "1.0.0-generic",
                "source": "Standard Domain Symbology",
                "is_authoritative": False,
                "features": features_list
            }

        providers_list.append({
            "utility_name": util_name,
            "utility_type": u_type,
            "warnings_count": len(warnings),
            "high_count": u_high,
            "medium_count": u_med,
            "low_count": u_low,
            "status_label": "AUTO-CLEAR / PASS" if len(warnings) == 0 else ("HIGH HAZARD ACTIVE" if u_high > 0 else "ADVISORY ACTIVE"),
            "warnings": warnings,
            "legend": legend_data
        })

    type_counts = {}
    for p in providers_list:
        t = p["utility_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    _CATALOGUE_CACHE = {
        "source_file": "warnings_list.xlsx",
        "excel_path": excel_path,
        "stats": {
            "total_providers": len(providers_list),
            "total_warnings": total_warnings,
            "high_hazard_warnings": high_count,
            "medium_warnings": med_count,
            "low_warnings": low_count,
            "auto_clear_providers": auto_clear_count,
            "type_counts": type_counts
        },
        "providers": providers_list
    }
    return _CATALOGUE_CACHE


@router.get("")
def get_catalogue(
    utility_type: Optional[str] = Query(None, description="Filter by utility type (Gas, Electricity, Water, Telecom, Heat)"),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, MEDIUM, LOW, AUTO_CLEAR)"),
    search: Optional[str] = Query(None, description="Search term across provider name, warning text, or legend"),
    reload: bool = Query(False, description="Force re-reading Excel file")
) -> Dict[str, Any]:
    """Retrieve the authoritative warning catalogue and legend symbology profiles."""
    cat = load_authoritative_catalogue(force_reload=reload)
    providers = cat.get("providers", [])

    if utility_type and utility_type.lower() != "all":
        providers = [p for p in providers if p["utility_type"].lower() == utility_type.lower()]

    if severity:
        sev_up = severity.upper()
        if sev_up == "HIGH":
            providers = [p for p in providers if p["high_count"] > 0]
        elif sev_up == "MEDIUM":
            providers = [p for p in providers if p["medium_count"] > 0]
        elif sev_up == "LOW":
            providers = [p for p in providers if p["low_count"] > 0]
        elif sev_up in ["AUTO_CLEAR", "CLEAR", "NONE"]:
            providers = [p for p in providers if p["warnings_count"] == 0]

    if search:
        s_term = search.lower().strip()
        matched = []
        for p in providers:
            # Check utility name
            if s_term in p["utility_name"].lower() or s_term in p["utility_type"].lower():
                matched.append(p)
                continue
            # Check warning texts
            warn_match = any(s_term in w["warning_text"].lower() for w in p["warnings"])
            if warn_match:
                matched.append(p)
                continue
            # Check legend feature descriptions or labels
            feat_match = False
            if p.get("legend") and p["legend"].get("features"):
                for f in p["legend"]["features"]:
                    if s_term in f["description"].lower() or any(s_term in lbl.lower() for lbl in f.get("text_labels", [])):
                        feat_match = True
                        break
            if feat_match:
                matched.append(p)
        providers = matched

    return {
        "stats": cat.get("stats", {}),
        "total_filtered": len(providers),
        "providers": providers
    }


@router.get("/provider/{provider_name}")
def get_provider_details(provider_name: str) -> Dict[str, Any]:
    """Retrieve detailed warning catalogue rules and legend symbology for a single provider."""
    cat = load_authoritative_catalogue()
    for p in cat.get("providers", []):
        if p["utility_name"].lower().strip() == provider_name.lower().strip():
            return p
    raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found in catalogue.")
