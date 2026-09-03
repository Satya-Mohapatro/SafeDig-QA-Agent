# Legend Registry & Profile Specification

**Document:** `docs/legend_spec.md`  
**Version:** 1.0.0  
**Status:** Approved Master Specification  

---

## 1. Legend Profile Model

```json
{
  "legend_id": "LGD-SGN-V1",
  "provider": "SGN",
  "version": "1.2.0",
  "effective_date": "2026-01-01",
  "source_document": "SGN_Legend_Specification_2026.pdf",
  "features": [
    {
      "feature_id": "SGN_HP_GAS",
      "warning_code": "SGN_HIGH_PRESSURE_GAS",
      "geometry_type": "LINE",
      "color_signature": {
        "rgb": [255, 0, 0],
        "hsv_range": [[0, 150, 150], [10, 255, 255]],
        "tolerance": 15
      },
      "stroke": {
        "min_width_pt": 1.5,
        "max_width_pt": 3.5,
        "dash_pattern": []
      },
      "text_labels": ["HP", "HIGH PRESSURE"]
    }
  ]
}
```

---

## 2. Legend Resolution Hierarchy
1. Embedded Authoritative Provider Legend on the map page.
2. Approved External Provider Legend document in the job folder.
3. Approved Master Legend Profile in system registry.
4. If unresolved -> `LEGEND_UNAVAILABLE` (Blocks `AUTO_CLEAR`).

---
