import cv2
import numpy as np
from typing import Tuple

def create_color_mask(
    image_bgr: np.ndarray,
    target_rgb: Tuple[int, int, int],
    tolerance: int = 40
) -> np.ndarray:
    """Create a high-fidelity binary mask for a target RGB color with red wrap-around support."""
    tr, tg, tb = target_rgb
    target_bgr = np.uint8([[[tb, tg, tr]]])
    target_hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)[0][0]
    
    h, s, v = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])
    
    h_tol = max(10, int(tolerance * 0.4))
    s_tol = max(40, tolerance)
    v_tol = max(40, tolerance)
    
    hsv_img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    
    # Check if hue wraps around 0/180 (especially critical for pure Red)
    if h - h_tol < 0:
        # Band 1: 0 to h + h_tol
        lower1 = np.array([0, max(40, s - s_tol), max(40, v - v_tol)])
        upper1 = np.array([h + h_tol, 255, 255])
        mask1 = cv2.inRange(hsv_img, lower1, upper1)
        
        # Band 2: 180 + (h - h_tol) to 179
        lower2 = np.array([180 + (h - h_tol), max(40, s - s_tol), max(40, v - v_tol)])
        upper2 = np.array([179, 255, 255])
        mask2 = cv2.inRange(hsv_img, lower2, upper2)
        return cv2.bitwise_or(mask1, mask2)
    elif h + h_tol > 179:
        # Band 1: h - h_tol to 179
        lower1 = np.array([h - h_tol, max(40, s - s_tol), max(40, v - v_tol)])
        upper1 = np.array([179, 255, 255])
        mask1 = cv2.inRange(hsv_img, lower1, upper1)
        
        # Band 2: 0 to (h + h_tol - 180)
        lower2 = np.array([0, max(40, s - s_tol), max(40, v - v_tol)])
        upper2 = np.array([h + h_tol - 180, 255, 255])
        mask2 = cv2.inRange(hsv_img, lower2, upper2)
        return cv2.bitwise_or(mask1, mask2)
    else:
        lower_hsv = np.array([max(0, h - h_tol), max(40, s - s_tol), max(40, v - v_tol)])
        upper_hsv = np.array([min(179, h + h_tol), 255, 255])
        return cv2.inRange(hsv_img, lower_hsv, upper_hsv)
