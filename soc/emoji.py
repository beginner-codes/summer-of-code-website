from collections.abc import Mapping

from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method

from soc.config.config import Config


class Emoji(Bevy, Mapping):
    @bevy_method
    def __init__(self, settings: Config = Inject):
        print("GOT EMOJI")
        self.emoji = settings.get(dict, "emoji")

    def __getitem__(self, item):
        return self.emoji[item]

    def __iter__(self):
        return iter(self.emoji)

    def __len__(self):
        return len(self.emoji)

    def __hash__(self):
        return id(self)
