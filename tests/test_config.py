from io import BytesIO

from bevy import Bevy, Context, Detect, Inject
from bevy.providers.function_provider import FunctionProvider

from soc.config import Config, BaseSettingsModel
from soc.config.settings_provider import SettingsProvider


def populated_context(open_override) -> Context:
    c = Context()
    c.add_provider(FunctionProvider)
    c.add(open_override, use_as=open)
    return c


def test_yaml_loaded():
    c = populated_context(
        lambda path, mode: BytesIO(
            b"Hello: World\npath: " + bytes(path) + b"\nmode: " + mode.encode()
        )
    )
    config = c.create(Config, "Test/Path")
    assert config._data == {"Hello": "World", "path": "Test/Path", "mode": "rb"}


def test_model_population():
    class DataModel(BaseSettingsModel):
        a: int
        b: str

    c = populated_context(lambda *_: BytesIO(b"data:\n  a: 1\n  b: Hello"))
    config = c.create(Config, "some/path")
    data = config.get(DataModel, "data")
    assert data.a == 1
    assert data.b == "Hello"


def test_multiple_files():
    class SubData(BaseSettingsModel):
        c: float
        d: list[int]

    class DataModel(BaseSettingsModel):
        a: int
        b: str
        e: SubData

    def open_mock(path, _):
        files = {
            "a.yaml": b"a: 1\nb: Hello",
            "b.yaml": b"e:\n  c: 12.3\n  d:\n  - 1\n  - 2"
        }
        return BytesIO(files[str(path)])

    c = populated_context(open_mock)
    config = c.create(Config, "a.yaml", "b.yaml")
    data = config.get(DataModel)
    assert data.a == 1
    assert data.b == "Hello"
    assert data.a == 1
    assert data.e.c == 12.3
    assert data.e.d == [1, 2]


def test_populated_settings_injection():
    class SectionModel(BaseSettingsModel):
        __config_key__ = "section"

        foo: str

    class Test(Bevy[Detect.ALL]):
        section: SectionModel

    def open_mock(path, _):
        files = {
            "a.yaml": b"section:\n  foo: bar",
        }
        return BytesIO(files[str(path)])

    c = populated_context(open_mock)
    c.add_provider(SettingsProvider)
    c.create(Config, "a.yaml", add_to_context=True)
    test: Test = c.create(Test)
    assert test.section.foo == "bar"

