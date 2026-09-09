import os
import re
import pandas as pd
from typing import Dict, List, Optional, Set
from src.domain.warning import WarningDefinition
from src.domain.enums import Severity, GeometryType
from src.config.logging import logger
from src.config.settings import settings
from src.utils.paths import resolve_catalogue_path

# Canonical provider mapping to bridge index naming to warnings_list.xlsx naming
PROVIDER_CANONICAL_MAP = {
    "uk power networks": "ukpn",
    "ukpn": "ukpn",
    "cadent gas": "cadentgas",
    "cadent": "cadentgas",
    "cadentgas": "cadentgas",
    "wales and west utilities": "wales & west utilities ltd",
    "wales and west utilities ltd": "wales & west utilities ltd",
    "wales & west utilities": "wales & west utilities ltd",
    "wales & west utilities ltd": "wales & west utilities ltd",
    "wwu": "wales & west utilities ltd",
    "sgn": "sgn",
    "scotia gas": "sgn",
    "national gas transmission": "national gas transmission",
    "national grid electricity distribution": "national grid electricity distribution",
    "nged": "national grid electricity distribution",
    "western power": "national grid electricity distribution",
    "national grid electricity transmission": "national grid electricity transmission",
    "nget": "national grid electricity transmission",
    "scottish and southern electricity networks": "scottish & southern energy power networks ltd",
    "scottish & southern energy power networks ltd": "scottish & southern energy power networks ltd",
    "ssen": "scottish & southern energy power networks ltd",
    "sp energy networks": "sp energy networks",
    "spen": "sp energy networks",
    "eirgrid": "eirgrid",
    "tfl": "tfl london underground hv cables",
    "tfl london underground hv cables": "tfl london underground hv cables",
    "tfl – london underground hv cables": "tfl london underground hv cables",
    "tfl  london underground hv cables": "tfl london underground hv cables",
    "esp utilities": "esp utilities",
    "esp utilities group": "esp utilities group",
    "clean_water": "clean_water",
    "clean water": "clean_water",
    "waste_water": "waste_water",
    "waste water": "waste_water",
    "bt": "bt",
    "openreach": "bt",
    "vm": "vm",
    "virgin media": "vm",
    "gtc-gas": "gtc-gas",
    "gtc-electricity": "gtc-electricity",
}

def _clean_name(name: str) -> str:
    """Normalize provider string for robust comparison."""
    if not name:
        return ""
    lower = name.lower().strip()
    return PROVIDER_CANONICAL_MAP.get(lower, re.sub(r'[^a-z0-9]', '', lower))


class WarningCatalogue:
    """Warning Catalogue strictly adhering to warnings_list.xlsx.
    
    Per operational safety requirements:
    - Only HIGH status warnings defined in warnings_list.xlsx are active.
    - Medium, Low, or unlisted utilities have NO warning and pass automatically.
    """
    def __init__(self, excel_path: Optional[str] = None):
        self.excel_path = resolve_catalogue_path(excel_path)
        self.definitions: Dict[str, WarningDefinition] = {}
        self.high_warning_providers: Set[str] = set()
        self._load_catalogue()
        
    def _load_catalogue(self):
        if not os.path.exists(self.excel_path):
            logger.warning(f"Warning catalogue excel not found at {self.excel_path}. Using built-in defaults.")
            self._load_defaults()
            return
            
        try:
            df = pd.read_excel(self.excel_path, sheet_name=0)
        except Exception as e:
            logger.error(f"Failed to read warning catalogue excel from {self.excel_path}: {e}")
            self._load_defaults()
            return
            
        df["UtilityName"] = df["UtilityName"].ffill()
        df["UtilityType"] = df["UtilityType"].ffill()
        
        valid_df = df.dropna(subset=["Warning"])
        
        for idx, row in valid_df.iterrows():
            provider = str(row["UtilityName"]).strip()
            u_type = str(row["UtilityType"]).strip()
            w_text = str(row["Warning"]).strip()
            
            raw_sev = str(row.get("Status", "")).strip().upper()
            
            # STRICT REQUIREMENT: Only High severity warnings are active warnings.
            # Medium and Low warnings are not treated as active warnings.
            if not ("HIGH" in raw_sev or "CRITICAL" in raw_sev):
                continue
                
            code = f"{re.sub(r'[^A-Za-z0-9]', '_', provider).upper()}_{idx + 1:03d}"
            
            wdef = WarningDefinition(
                warning_code=code,
                provider=provider,
                utility_type=u_type,
                business_warning_text=w_text,
                severity=Severity.HIGH,
                geometry_type=GeometryType.LINE,
                aoi_required=True,
                version="1.0.0"
            )
            self.definitions[code] = wdef
            self.high_warning_providers.add(_clean_name(provider))
            
        logger.info(f"Loaded {len(self.definitions)} HIGH warning definitions from catalogue ({self.excel_path}).")
        
    def _load_defaults(self):
        self.definitions["SGN_HP_GAS"] = WarningDefinition(
            warning_code="SGN_HP_GAS",
            provider="SGN",
            utility_type="Gas",
            business_warning_text="There is a High Pressure Gas Line in this area | ",
            severity=Severity.HIGH,
            geometry_type=GeometryType.LINE,
            aoi_required=True
        )
        self.high_warning_providers.add(_clean_name("SGN"))
        self.definitions["UKPN_HV_CABLE"] = WarningDefinition(
            warning_code="UKPN_HV_CABLE",
            provider="UK Power Networks",
            utility_type="Electricity",
            business_warning_text="There is HV Cable in this area|",
            severity=Severity.HIGH,
            geometry_type=GeometryType.LINE,
            aoi_required=True
        )
        self.high_warning_providers.add(_clean_name("UK Power Networks"))
        
    def has_warnings_for_provider(self, provider_name: str) -> bool:
        """Returns True if the provider has active HIGH warnings in the catalogue."""
        c_name = _clean_name(provider_name)
        if c_name in self.high_warning_providers:
            return True
        for hwp in self.high_warning_providers:
            if hwp and (hwp in c_name or c_name in hwp):
                return True
        return False
        
    def get_definitions_for_provider(self, provider_name: str) -> List[WarningDefinition]:
        """Return all active HIGH warning definitions for a given utility provider."""
        c_name = _clean_name(provider_name)
        matched = []
        for w in self.definitions.values():
            w_clean = _clean_name(w.provider)
            if c_name == w_clean or c_name in w_clean or w_clean in c_name:
                matched.append(w)
        return matched
        
    def find_by_text(self, text: str) -> Optional[WarningDefinition]:
        """Match incoming raw warning text against active HIGH warning definitions."""
        if not text:
            return None
        t_clean = text.lower().strip().replace("|", "").strip()
        # If text explicitly states clean / not found / no plant, it is not a warning
        if any(neg in t_clean for neg in ["no gtc", "no plant", "not found", "no warning", "nil", "none"]):
            return None
        for w in self.definitions.values():
            w_clean = w.business_warning_text.lower().strip().replace("|", "").strip()
            if t_clean == w_clean or t_clean in w_clean or w_clean in t_clean:
                return w
        return None

master_warning_catalogue = WarningCatalogue()

