from typing import List, Optional
from .base import BaseProviderValidator
from src.legends import resolve_legend
from src.warnings import master_warning_catalogue
from src.domain.document import Document
from src.domain.warning import WarningDefinition
from src.domain.legend import LegendProfile

class GenericProviderValidator(BaseProviderValidator):
    def can_handle(self, utility_name: str) -> bool:
        return True

    def get_warning_definitions(self) -> List[WarningDefinition]:
        return master_warning_catalogue.get_definitions_for_provider(self.provider_name)

    def resolve_legend(self, document: Document) -> Optional[LegendProfile]:
        return resolve_legend(self.provider_name)

class ProviderRegistry:
    def __init__(self):
        self._validators: List[BaseProviderValidator] = []

    def register(self, validator: BaseProviderValidator):
        self._validators.append(validator)

    def get_validator(self, provider_name: str) -> BaseProviderValidator:
        for v in self._validators:
            if v.can_handle(provider_name):
                return v
        return GenericProviderValidator(provider_name)

provider_registry = ProviderRegistry()
