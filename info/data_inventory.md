# Data Inventory & Profiling Report

**Document:** `docs/data_inventory.md`  
**Dataset Path:** `d:\Safedig_AG\Data`  
**Date of Profiling:** 2026-09-01  
**Profiling Engine:** Python 3.11 / PyMuPDF 1.24+ / pandas 2.2+  

---

## 1. Executive Summary

The sample dataset contains **13 project job folders** plus **1 master warning catalogue workbook** (`warnings_list 2 1 (1).xlsx`).
A total of **186 files** were profiled across all directories.

---

## 2. Master Warning Catalogue: `warnings_list 2 1 (1).xlsx`

- **File location:** `d:\Safedig_AG\Data\warnings_list 2 1 (1).xlsx`
- **Sheet name:** `Sheet1`
- **Total rows:** 86
- **Raw columns:** `['UtilityName', 'UtilityType', 'Warning', 'Status']`
- **Column Semantic Mapping:**
  - `UtilityName`: Provider name (grouped/hierarchical, rows forward-filled)
  - `UtilityType`: Utility category (Gas, Electricity, Water, Telecom, Heat, Petroleum, etc.)
  - `Warning`: Business-approved warning text phrase
  - `Status`: **Warning Severity level** (`High`, `Medium`, `Low`)
- **Key finding:** In the master warning workbook, the 4th column is labeled `Status`, but its contents are explicitly severity strings: `High`, `Medium`, `Low`.

### Master Warning Distribution by Severity & Provider

| Utility Name | Utility Type | Warning Text | Canonical Severity |
| :--- | :--- | :--- | :--- |
| **CadentGas** | Gas | There is a Medium Pressure Gas Line in this area\| | Medium |
| **CadentGas** | Gas | There is an LHP Pressure Gas Line in this area \| | High |
| **CadentGas** | Gas | There is an Intermediate Pressure Gas Line in this area \| | High |
| **ESP Utilities** | Gas | There is a Medium Pressure Gas Line in this area\| | Medium |
| **ESP Utilities** | Gas | There is an Intermediate Pressure Gas Line in this area \| | High |
| **SGN** | Gas | There is a Medium Pressure Gas Line in this area\| | Medium |
| **SGN** | Gas | There is a High Pressure Gas Line in this area \| | High |
| **SGN** | Gas | There is an Intermediate Pressure Gas Line in this area \| | High |
| **National Gas Transmission** | Gas | There is a NHP mains in this area\| | High |
| **Wales & West Utilities Ltd** | Gas | There is a Medium Pressure Gas Line in this Area\| | Medium |
| **Wales & West Utilities Ltd** | Gas | There is an High Pressure Gas Line in this Area \| | High |
| **Wales & West Utilities Ltd** | Gas | There is an Intermediate Pressure Gas Line in this Area \| | High |
| **GTC-Gas** | Gas | GTC plant has been present in this area | Medium |
| **Fulcrum Pipelines Limited** | Gas | There is Fulcrum Pipeline present in this area \| | Low |
| **MUA Group Limited - Gas** | Gas | There is Gas pipeline present in this area\| | Medium |
| **Energy Assets Networks - Gas** | Gas | There is Gas pipeline present in this area\| | Medium |
| **UKPN** | Electricity | There is HV Cable in this area\| | High |
| **National Grid Electricity Distribution** | Electricity | There is a 11kV High Voltage Electricity Line in this Area \| | High |
| **National Grid Electricity Distribution** | Electricity | There is a 33kV High Voltage Electricity Line in this Area \| | High |
| **National Grid Electricity Distribution** | Electricity | There is a 66kV High Voltage Electricity Line in this Area\| | High |
| **National Grid Electricity Distribution** | Electricity | There is a 132kV High Voltage Electricity Line in this Area\| | High |
| **Scottish & Southern Energy Power Networks** | Electricity | There is HV Cable in this area\| | High |
| **Scottish & Southern Energy Power Networks** | Electricity | There is Fibre Optic in this area\| | Low |
| **Scottish & Southern Energy Power Networks** | Electricity | There is Pilot Cable in this area\| | Low |
| **National Grid Electricity Transmission** | Electricity | There is an Underground Cable in this area\| | High |
| **National Grid Electricity Transmission** | Electricity | There is an Overhead Cable in this area\| | Medium |
| **National Grid Electricity Transmission** | Electricity | There is a Fiber Cable in this area\| | Low |
| **Last Mile** | Electricity | (Blank in catalogue) | Medium |
| **TfL – London Underground HV Cables** | Electricity | TfL – London Underground HV Cables Present | High |
| **SP Energy Networks** | Electricity | There is HV 22/11KV Cable in this area\| | High |
| **SP Energy Networks** | Electricity | There is 33KV Cable in this area\| | High |
| **SP Energy Networks** | Electricity | There is 132KV Cable in this area\| | High |
| **EirGrid** | Electricity | High voltage direct current (HVDC) cables are present | High |
| **GTC-Electricity** | Electricity | Electricity cabels are present in this area | Medium |
| **MUA Group Limited - Electricity** | Electricity | There are Electricity Cables present in this area\| | Medium |
| **Energy Assets Networks - Electricity** | Electricity | There are Electricity Cables present in this area\| | Medium |
| **EDF Energy Renewables Ltd** | Electricity | There are Electricity Cables present in this area\| | Medium |
| **Waste_Water** | Water | There is a Pressure Main Waste Water Line in this Area | Medium |
| **EUNetworks Fiber UK Limited** | Telecom | EUNetworks Fiber UK Limited Asset Present | Low |
| **EXA Infrastructure** | Telecom | EXA Infrastructure Asset Present | Low |
| **Pimlico District Heating Undertaking** | Heat | Pimlico District Heating Undertaking (PDHU) Asset Present | Low |

---

## 3. Project Job Folders Inventory

The 13 sample project folders represent realistic multi-provider utility search packages:

| Folder Name | Total Files | PDF Files | Excel Files | Key Providers Present |
| :--- | :--- | :--- | :--- | :--- |
| `244414_201678` | 15 | 13 | `index.xlsx`, `index_org.xlsx` | NGED, WWU, BT, GTC, VM, Welsh Water |
| `299208_172565` | 12 | 10 | `index.xlsx`, `index_org.xlsx` | WWU, BT, GTC, SGN, UKPN |
| `534668_175407` | 14 | 12 | `index.xlsx`, `index_org.xlsx` | Cadent, ESP, GTC, UKPN, Thames Water |
| `536294_179488` | 13 | 11 | `index.xlsx`, `index_org.xlsx` | Cadent, UKPN, BT, Virgin Media |
| `538189_165956` | 15 | 13 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Thames Water, BT, Virgin Media |
| `538620_162035` | 14 | 12 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, BT, Virgin Media, ESP |
| `541433_168308` | 16 | 14 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Thames Water, GTC, BT |
| `546407_175628` | 13 | 11 | `index.xlsx`, `index_org.xlsx` | Cadent, UKPN, BT, Virgin Media, ESP |
| `547053_155559` | 15 | 13 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Southern Water, BT, Virgin Media |
| `547835_156740` | 14 | 12 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Southern Water, BT, GTC |
| `547960_159487` | 15 | 13 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Southern Water, BT, Virgin Media |
| `548357_172783` | 14 | 12 | `index.xlsx`, `index_org.xlsx` | Cadent, UKPN, Thames Water, BT, Virgin Media |
| `550782_169179` | 16 | 14 | `index.xlsx`, `index_org.xlsx` | SGN, UKPN, Thames Water, GTC, BT, Virgin Media |

---

## 4. Production Excel Index Structure: `index.xlsx`

Every folder contains an `index.xlsx` (and in several cases an unchanged `index_org.xlsx` backup).

### Actual Excel Schema
Columns:
1. `FileName` (string, e.g. `'42332089_NGED - Wales.pdf'`, `'BT.pdf'`, `NaN` for absent maps)
2. `UtilityName` (string, e.g. `'National Grid Electricity Distribution'`, `'SGN'`, `'UKPN'`)
3. `UtilityType` (string, e.g. `'Gas'`, `'Electricity'`, `'Water'`, `'Telecom'`, `'Heat'`, `'Petroleum'`, `'Toilet'`, `'Hospital'`, `'COSHH'`)
4. `Status` (string: `'Yes'`, `'No'`) - indicates whether utility assets/drawings are returned
5. `Warning` (string or `NaN`: upstream claimed warning text, e.g. `'There is HV Cable in this area|'`, `' '`, `NaN`)
6. `Comments` (numeric/float or `NaN`: e.g. `100.0`, `0.0`, `NaN`)

### Analysis of Index Values
- **Row count per index:** Typically 55–60 utility rows per index file.
- **`Status` column meaning:** 
  - `'Yes'`: An actual map document is returned and expected to be validated.
  - `'No'`: The utility reported no assets in the search zone / no document provided.
- **`FileName` column:** Populated when `Status == 'Yes'`. May contain whitespace or `NaN` when `Status == 'No'`.
- **`Warning` column:** Upstream AI output claim. Contains upstream warning text or is blank/whitespace/`NaN` if upstream detected no warning.

---

## 5. Map PDF Characteristics

- **Vector Density:** High vector density in modern utility maps (e.g. SGN, UKPN, Cadent, WWU, GTC) containing thousands of drawing commands (paths, strokes, line widths, dash patterns).
- **Supporting / Non-Map Documents Discovered:**
  - Booklets: `NGED Safety Look Out Look Up Booklet.pdf` (1.05 MB, multi-page safety booklet)
  - Guidance Notes: `NGED Webmap Letter and Guidance Notes.pdf`
  - Avoidance of Danger: `NGED Avoidance of Danger.pdf` (1.71 MB)
  - Letters: `WWU No Assets Affected Letter.pdf`
  - Enquiry confirmations: `LSBUD-260722-42332089.PDF`
- **File Classification Requirement:** These reference documents must be classified as `REFERENCE` or `SAFETY_REFERENCE` and must NOT enter the map-validation pipeline as maps.

---
