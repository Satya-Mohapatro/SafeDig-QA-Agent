from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from src.domain.document import Document
from src.domain.warning import WarningDefinition
from src.domain.legend import LegendProfile
from src.domain.aoi import AOI
from src.domain.detection import DetectedCandidate
from src.domain.evidence import EvidenceItem

class BaseProviderValidator(ABC):
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def can_handle(self, utility_name: str) -> bool:
        pass

    @abstractmethod
    def get_warning_definitions(self) -> List[WarningDefinition]:
        pass

    @abstractmethod
    def resolve_legend(self, document: Document) -> Optional[LegendProfile]:
        pass
