# Warning Catalogue Specification

**Document:** `docs/warning_catalogue_spec.md`  
**Version:** 1.0.0  
**Source of Authority:** `warnings_list 2 1 (1).xlsx`  
**Status:** Approved Master Specification  

---

## 1. Domain Ontology

A Warning Definition represents a specific utility hazard that the QA agent is configured to detect and validate.

### Schema: `WarningDefinition`
```json
{
  "warning_code": "SGN_HIGH_PRESSURE_GAS",
  "provider": "SGN",
  "utility_type": "Gas",
  "business_warning_text": "There is a High Pressure Gas Line in this area | ",
  "severity": "HIGH",
  "geometry_type": "LINE",
  "aoi_required": true,
  "detection_profile": "sgn_hp_gas_v1",
  "active": true,
  "version": "1.0.0"
}
```

---

## 2. Severity Classification Rules

1. **`CRITICAL` / `HIGH` Severity:**
   - High Pressure Gas Lines (SGN, Cadent, WWU, National Gas Transmission).
   - High Voltage Electricity Lines / Cables (11kV, 33kV, 66kV, 132kV, HVDC, London Underground HV).
   - Intermediate Pressure Gas Lines.
   - *Rule:* Any unresolved HIGH/CRITICAL warning strictly blocks `AUTO_CLEAR` and forces `HUMAN_REVIEW`.

2. **`MEDIUM` Severity:**
   - Medium Pressure Gas Lines.
   - GTC Plant / Electricity / Gas cables.
   - Pressure Main Waste Water Lines.
   - Overhead electricity cables.

3. **`LOW` Severity:**
   - Pilot Cables, Fibre Optic lines, Fulcrum Pipelines, District Heating Assets.

---
