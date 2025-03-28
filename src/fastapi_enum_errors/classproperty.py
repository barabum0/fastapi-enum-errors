from typing import Any


class classproperty(property):
    def __get__(self, owner_self: Any, owner_cls: Any) -> Any:  # type: ignore[override]
        return self.fget(owner_cls)  # type: ignore[misc]
