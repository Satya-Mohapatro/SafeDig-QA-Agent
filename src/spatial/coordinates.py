from typing import Tuple

class CoordinateTransformer:
    @staticmethod
    def pdf_to_pixel(x_pt: float, y_pt: float, dpi: int = 300) -> Tuple[int, int]:
        scale = dpi / 72.0
        return int(round(x_pt * scale)), int(round(y_pt * scale))

    @staticmethod
    def pixel_to_pdf(x_px: int, y_px: int, dpi: int = 300) -> Tuple[float, float]:
        scale = 72.0 / dpi
        return float(x_px * scale), float(y_px * scale)

coordinate_transformer = CoordinateTransformer()
