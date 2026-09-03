from typing import Dict, List, Optional
from src.domain.legend import LegendProfile, LegendFeature, ColorSignature, StrokeStyle
from src.domain.enums import GeometryType
from src.config.logging import logger

class LegendRegistry:
    def __init__(self):
        self.profiles: Dict[str, LegendProfile] = {}
        self._init_standard_profiles()
        
    def _init_standard_profiles(self):
        # 1. SGN (Scotia Gas Networks)
        self.profiles["SGN"] = LegendProfile(
            legend_id="LGD-SGN",
            provider="SGN",
            utility_type="Gas",
            version="1.2.0",
            features=[
                LegendFeature(
                    feature_id="SGN_HP_GAS",
                    warning_code="SGN_HP_GAS",
                    description="High Pressure Gas Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),  # Red
                    stroke=StrokeStyle(min_width_pt=1.2, max_width_pt=6.0),
                    text_labels=["HP", "HIGH PRESSURE", "GAS MAIN"]
                ),
                LegendFeature(
                    feature_id="SGN_MP_GAS",
                    warning_code="SGN_MP_GAS",
                    description="Medium Pressure Gas Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 140, 0), tolerance=40),  # Orange
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=5.0),
                    text_labels=["MP", "MEDIUM PRESSURE"]
                ),
                LegendFeature(
                    feature_id="SGN_LP_GAS",
                    warning_code="SGN_LP_GAS",
                    description="Low Pressure Gas Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 255, 0), tolerance=40),  # Yellow
                    stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=4.0),
                    text_labels=["LP", "LOW PRESSURE"]
                )
            ]
        )
        
        # 2. Cadent Gas
        self.profiles["CADENT"] = LegendProfile(
            legend_id="LGD-CADENT",
            provider="Cadent Gas",
            utility_type="Gas",
            version="1.1.0",
            features=[
                LegendFeature(
                    feature_id="CADENT_HP_GAS",
                    warning_code="CADENT_HP_GAS",
                    description="High Pressure Gas Pipeline",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),  # Red
                    stroke=StrokeStyle(min_width_pt=1.5, max_width_pt=6.0),
                    text_labels=["HP", "HIGH PRESSURE"]
                ),
                LegendFeature(
                    feature_id="CADENT_IP_GAS",
                    warning_code="CADENT_IP_GAS",
                    description="Intermediate Pressure Gas Pipeline",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 128, 0), tolerance=40),  # Orange
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=5.0),
                    text_labels=["IP", "INTERMEDIATE PRESSURE"]
                )
            ]
        )
        
        # 3. UK Power Networks (UKPN)
        self.profiles["UKPN"] = LegendProfile(
            legend_id="LGD-UKPN",
            provider="UK Power Networks",
            utility_type="Electricity",
            version="2.0.0",
            features=[
                LegendFeature(
                    feature_id="UKPN_HV_CABLE",
                    warning_code="UKPN_HV_CABLE",
                    description="High Voltage Cable (11kV / 33kV / 132kV)",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),  # Red / Magenta
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=6.0),
                    text_labels=["11KV", "33KV", "132KV", "HV", "HIGH VOLTAGE"]
                ),
                LegendFeature(
                    feature_id="UKPN_LV_CABLE",
                    warning_code="UKPN_LV_CABLE",
                    description="Low Voltage Cable",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(0, 0, 0), tolerance=40),  # Black
                    stroke=StrokeStyle(min_width_pt=0.5, max_width_pt=3.0),
                    text_labels=["LV", "LOW VOLTAGE"]
                )
            ]
        )
        
        # 4. National Grid Electricity Distribution (NGED / WPD)
        self.profiles["NGED"] = LegendProfile(
            legend_id="LGD-NGED",
            provider="National Grid Electricity Distribution",
            utility_type="Electricity",
            version="1.0.0",
            features=[
                LegendFeature(
                    feature_id="NGED_11KV_LINE",
                    warning_code="NGED_11KV",
                    description="11kV High Voltage Electricity Line",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=5.0),
                    text_labels=["11KV", "11000V", "HV"]
                )
            ]
        )
        
        # 5. Wales & West Utilities (WWU)
        self.profiles["WWU"] = LegendProfile(
            legend_id="LGD-WWU",
            provider="Wales and West Utilities",
            utility_type="Gas",
            version="1.0.0",
            features=[
                LegendFeature(
                    feature_id="WWU_HP_GAS",
                    warning_code="WWU_HP_GAS",
                    description="High Pressure Gas Line",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),
                    stroke=StrokeStyle(min_width_pt=1.5, max_width_pt=5.0),
                    text_labels=["HP", "HIGH PRESSURE"]
                )
            ]
        )
        
        # 6. GTC Multi-Utility
        self.profiles["GTC"] = LegendProfile(
            legend_id="LGD-GTC",
            provider="GTC",
            utility_type="Multi",
            version="1.0.0",
            features=[
                LegendFeature(
                    feature_id="GTC_PLANT",
                    warning_code="GTC_PLANT",
                    description="GTC Utility Network Asset",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(0, 128, 255), tolerance=40),  # Blue
                    stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=4.0),
                    text_labels=["GTC"]
                )
            ]
        )
        
        # 7. Water Networks (Clean Water & Waste Water)
        self.profiles["WATER"] = LegendProfile(
            legend_id="LGD-WATER",
            provider="Water Networks",
            utility_type="Water",
            version="1.1.0",
            features=[
                LegendFeature(
                    feature_id="WATER_TRUNK_MAIN",
                    warning_code="WATER_TRUNK_MAIN",
                    description="Water Trunk Transmission Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(255, 0, 0), tolerance=40),  # Red solid line
                    stroke=StrokeStyle(min_width_pt=1.0, max_width_pt=6.0),
                    text_labels=["TRUNK", "TRUNK MAIN"]
                ),
                LegendFeature(
                    feature_id="WATER_CLEAN_MAIN",
                    warning_code="WATER_CLEAN_MAIN",
                    description="Clean Potable Water Distribution Main",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(0, 180, 255), tolerance=60),  # Cyan / Blue
                    stroke=StrokeStyle(min_width_pt=0.5, max_width_pt=5.0),
                    text_labels=["WATER", "100 MM", "100MM", "150 MM", "150MM", "POTABLE"]
                ),
                LegendFeature(
                    feature_id="WATER_WASTE_SEWER",
                    warning_code="WATER_WASTE_SEWER",
                    description="Waste Water Foul / Surface Sewer",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(128, 0, 128), tolerance=40),  # Purple / Brown
                    stroke=StrokeStyle(min_width_pt=0.8, max_width_pt=5.0),
                    text_labels=["SEWER", "FOUL", "SURFACE", "DRAIN"]
                )
            ]
        )

        
        # 8. Telecoms (BT Openreach & Virgin Media)
        self.profiles["TELECOM"] = LegendProfile(
            legend_id="LGD-TELECOM",
            provider="Telecom Networks",
            utility_type="Telecom",
            version="1.0.0",
            features=[
                LegendFeature(
                    feature_id="TELECOM_DUCT_CABLE",
                    warning_code="TELECOM_DUCT_CABLE",
                    description="Telecommunications Duct and Fibre Network",
                    geometry_type=GeometryType.LINE,
                    color=ColorSignature(rgb=(0, 150, 0), tolerance=40),  # Green
                    stroke=StrokeStyle(min_width_pt=0.6, max_width_pt=4.0),
                    text_labels=["BT", "OPENREACH", "VIRGIN", "TELECOM", "FIBRE"]
                )
            ]
        )

    def get_profile(self, provider_name: str) -> Optional[LegendProfile]:
        p_clean = provider_name.lower().strip()
        
        if any(k in p_clean for k in ["sgn", "scotia"]):
            return self.profiles["SGN"]
        if any(k in p_clean for k in ["cadent"]):
            return self.profiles["CADENT"]
        if any(k in p_clean for k in ["uk power", "ukpn"]):
            return self.profiles["UKPN"]
        if any(k in p_clean for k in ["national grid electricity", "nged", "western power"]):
            return self.profiles["NGED"]
        if any(k in p_clean for k in ["wales and west", "wales & west", "wwu"]):
            return self.profiles["WWU"]
        if any(k in p_clean for k in ["gtc"]):
            return self.profiles["GTC"]
        if any(k in p_clean for k in ["water", "thames", "southern water", "welsh water", "clean_water", "waste_water", "sewer"]):
            return self.profiles["WATER"]
        if any(k in p_clean for k in ["bt", "openreach", "virgin", "vm", "telecom"]):
            return self.profiles["TELECOM"]
            
        return None

master_legend_registry = LegendRegistry()
