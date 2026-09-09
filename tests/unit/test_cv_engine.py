import numpy as np
import pytest
from src.cv import create_color_mask, find_line_contours, match_symbol_template

def test_color_mask():
    # Create red BGR image (0, 0, 255)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[20:80, 20:80] = [0, 0, 255]
    
    mask = create_color_mask(img, target_rgb=(255, 0, 0), tolerance=40)
    assert mask is not None
    assert np.sum(mask) > 0
    
    contours = find_line_contours(mask, min_area=10.0)
    assert len(contours) >= 1
    assert contours[0]["bbox"][0] == 20
