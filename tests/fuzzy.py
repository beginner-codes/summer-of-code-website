from typing import Any, Generic, Literal, overload, Type, TypeVar


ExpectedType = TypeVar("ExpectedType")


class FuzzyValue(Generic[ExpectedType]):
    def __init__(self, expected_type: Type[ExpectedType]):
        self.expected_type = expected_type

    @overload
    def __eq__(self, other: ExpectedType) -> Literal[True]:
        ...

    @overload
    def __eq__(self, other: Any) -> Literal[False]:
        ...

    def __eq__(self, other: ExpectedType | Any) -> bool:
        return isinstance(other, self.expected_type)

    def __repr__(self):
        return f"Any[{self.expected_type.__name__}]"
