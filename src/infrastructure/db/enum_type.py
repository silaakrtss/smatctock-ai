from enum import Enum
from typing import Any

from sqlalchemy import String
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class StrEnumType(TypeDecorator[Enum]):
    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[Enum], length: int = 32) -> None:
        self._enum_cls = enum_cls
        super().__init__(length)

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, self._enum_cls):
            return str(value.value)
        if isinstance(value, str):
            return str(self._enum_cls(value).value)
        raise TypeError(f"Cannot bind {value!r} as {self._enum_cls.__name__}")

    def process_result_value(self, value: Any, dialect: Dialect) -> Enum | None:
        if value is None:
            return None
        return self._enum_cls(value)
