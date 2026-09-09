from typing import Optional
from src.domain.legend import LegendProfile
from .registry import master_legend_registry
from src.config.logging import logger

def resolve_legend(provider_name: str, has_embedded_legend: bool = False) -> Optional[LegendProfile]:
    profile = master_legend_registry.get_profile(provider_name)
    if profile:
        logger.info(f"Resolved legend profile '{profile.legend_id}' (v{profile.version}) for provider '{provider_name}'")
        return profile
        
    logger.warning(f"No authoritative legend profile found for provider '{provider_name}' (LEGEND_UNAVAILABLE).")
    return None
