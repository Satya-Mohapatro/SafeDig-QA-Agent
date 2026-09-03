import cv2
import numpy as np
from typing import List, Dict, Any

def find_line_contours(mask: np.ndarray, min_area: float = 50.0) -> List[Dict[str, Any]]:
    # Morphological line closing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    results = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            results.append({
                "area": area,
                "bbox": [x, y, x + w, y + h],
                "contour": cnt
            })
    return results
