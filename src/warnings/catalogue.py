import os
import pandas as pd
from typing import Dict, List, Optional
from src.domain.warning import WarningDefinition
from src.domain.enums import Severity, GeometryType
from src.config.logging import logger

MASTER_CATALOGUE_PATH = r"d:\Safedig_AG\Data\warnings_list 2 1 (1).xlsx"

# Provider normalization mapping
PROVIDER_ALIASES = {
    "uk power networks": "UK Power Networks",
    "ukpn": "UK Power Networks",
    "national grid electricity distribution": "National Grid Electricity Distribution",
    "nged": "National Grid Electricity Distribution",
    "wales and west utilities": "Wales and West Utilities",
    "wales & west utilities ltd": "Wales and West Utilities",
    "wwu": "Wales and West Utilities",
    "cadent gas": "Cadent Gas",
    "cadent": "Cadent Gas",
    "sgn": "SGN",
    "scotia gas": "SGN",
    "gtc-gas": "GTC",
    "gtc-electricity": "GTC",
    "gtc-water": "GTC",
    "gtc-fibre": "GTC",
    "welsh water": "Welsh Water",
    "thames water": "Thames Water",
    "southern water": "Southern Water",
    "clean_water": "Clean_Water",
    "waste_water": "Waste_Water",
    "bt": "BT",
    "vm": "Virgin Media",
}

class WarningCatalogue:
    def __init__(self, excel_path: Optional[str] = None):
        self.excel_path = excel_path or MASTER_CATALOGUE_PATH
        self.definitions: Dict[str, WarningDefinition] = {}
        self._load_catalogue()
        
    def _load_catalogue(self):
        if not os.path.exists(self.excel_path):
            logger.warning(f"Warning catalogue excel not found at {self.excel_path}. Using built-in defaults.")
            self._load_defaults()
            return
            
        df = pd.read_excel(self.excel_path, sheet_name=0)
        df["UtilityName"] = df["UtilityName"].ffill()
        df["UtilityType"] = df["UtilityType"].ffill()
        
        valid_df = df.dropna(subset=["Warning"])
        
        for idx, row in valid_df.iterrows():
            provider = str(row["UtilityName"]).strip()
            u_type = str(row["UtilityType"]).strip()
            w_text = str(row["Warning"]).strip()
            
            raw_sev = str(row.get("Status", "MEDIUM")).strip().upper()
            if "HIGH" in raw_sev or "CRITICAL" in raw_sev:
                sev = Severity.HIGH
            elif "LOW" in raw_sev:
                sev = Severity.LOW
            else:
                sev = Severity.MEDIUM
                
            code = f"{provider.upper().replace(' ', '_')}_{idx + 1:03d}"
            
            wdef = WarningDefinition(
                warning_code=code,
                provider=provider,
                utility_type=u_type,
                business_warning_text=w_text,
                severity=sev,
                geometry_type=GeometryType.LINE,
                aoi_required=True,
                version="1.0.0"
            )
            self.definitions[code] = wdef
            
        logger.info(f"Loaded {len(self.definitions)} warning definitions from catalogue.")
        
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
        self.definitions["UKPN_HV_CABLE"] = WarningDefinition(
            warning_code="UKPN_HV_CABLE",
            provider="UK Power Networks",
            utility_type="Electricity",
            business_warning_text="There is HV Cable in this area|",
            severity=Severity.HIGH,
            geometry_type=GeometryType.LINE,
            aoi_required=True
        )
        
    def get_definitions_for_provider(self, provider_name: str) -> List[WarningDefinition]:
        p_lower = provider_name.lower().strip()
        matched = []
        for w in self.definitions.values():
            w_prov = w.provider.lower().strip()
            if p_lower in w_prov or w_prov in p_lower:
                matched.append(w)
        return matched
        
    def find_by_text(self, text: str) -> Optional[WarningDefinition]:
        t_clean = text.lower().strip().replace("|", "").strip()
        for w in self.definitions.values():
            w_clean = w.business_warning_text.lower().strip().replace("|", "").strip()
            if t_clean == w_clean or t_clean in w_clean or w_clean in t_clean:
                return w
        return None

master_warning_catalogue = WarningCatalogue()
