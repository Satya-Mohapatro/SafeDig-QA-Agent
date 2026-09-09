import cv2
import numpy as np
from typing import List, Tuple

def match_symbol_template(
    image_gray: np.ndarray,
    template_gray: np.ndarray,
    threshold: float = 0.8
) -> List[Tuple[int, int, int, int, float]]:
    res = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    h, w = template_gray.shape[:2]
    matches = []
    for pt in zip(*loc[::-1]):
        score = float(res[pt[1], pt[0]])
        matches.append((pt[0], pt[1], pt[0] + w, pt[1] + h, score))
    return matches
