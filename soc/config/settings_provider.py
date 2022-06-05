from typing import Any, Type, TypeVar

from bevy import Inject
from bevy.providers import TypeProvider
from bevy.providers.injection_priority_helpers import high_priority

from soc.config import BaseSettingsModel, Config


T = TypeVar("T", bound=BaseSettingsModel)


class SettingsProvider(TypeProvider):
    config: Config = Inject

    def create(self, obj: Type[T], *args, add: bool = False, **kwargs) -> T:
        bound_type = self.bind_to_context(obj, self.bevy)
        model = self.config.get(bound_type, obj.__config_key__)
        if add:
            self.add(model, use_as=obj)

        return model

    def supports(self, obj: Type[BaseSettingsModel] | Any) -> bool:
        return isinstance(obj, type) and issubclass(obj, BaseSettingsModel)

    create_and_insert = high_priority
