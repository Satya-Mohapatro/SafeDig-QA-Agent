from typing import Optional
from src.domain.legend import LegendProfile
from .registry import master_legend_registry
from .detector import detect_dynamic_legend
from src.config.logging import logger

def resolve_legend(
    provider_name: str,
    has_embedded_legend: bool = False,
    pdf_path: Optional[str] = None,
    page_num: int = 1,
    output_crop_dir: Optional[str] = None,
    document_id: Optional[str] = None
) -> Optional[LegendProfile]:
    """Resolve authoritative legend profile using dynamic on-map detection with registry fallback."""
    if pdf_path:
        try:
            profile = detect_dynamic_legend(
                pdf_path=pdf_path,
                provider_name=provider_name,
                page_num=page_num,
                output_crop_dir=output_crop_dir,
                document_id=document_id
            )
            if profile and profile.features:
                logger.info(f"Dynamically resolved {len(profile.features)} legend features for '{provider_name}'")
                return profile
        except Exception as e:
            logger.warning(f"Dynamic legend resolution failed for '{provider_name}': {e}. Falling back to registry.")

    profile = master_legend_registry.get_profile(provider_name)
    if profile:
        logger.info(f"Resolved static legend profile '{profile.legend_id}' (v{profile.version}) for provider '{provider_name}'")
        return profile
        
    logger.warning(f"No authoritative legend profile found for provider '{provider_name}' (LEGEND_UNAVAILABLE).")
    return None
