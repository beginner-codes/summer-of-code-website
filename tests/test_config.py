from io import BytesIO

from bevy import Context
from bevy.function_provider import FunctionProvider
from pydantic import Field

from soc.config import Config, BaseSettingsModel


def populated_context(data) -> Context:
    c = Context()
    c.add(
        data,
        as_type=open,
        provider_type=FunctionProvider,
    )
    return c


def test_yaml_loaded():
    c = populated_context(
        lambda path, mode: BytesIO(
            b"Hello: World\npath: " + bytes(path) + b"\nmode: " + mode.encode()
        )
    )
    config = c.get(Config, args=("Test/Path",))
    assert config._data == {"Hello": "World", "path": "Test/Path", "mode": "rb"}


def test_model_population():
    class DataModel(BaseSettingsModel):
        a: int
        b: str

    c = populated_context(lambda *_: BytesIO(b"data:\n  a: 1\n  b: Hello"))
    config = c.get(Config, args=("some/path",))
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
    config = c.get(Config, args=("a.yaml", "b.yaml"))
    data = config.get(DataModel)
    assert data.a == 1
    assert data.b == "Hello"
    assert data.a == 1
    assert data.e.c == 12.3
    assert data.e.d == [1, 2]
