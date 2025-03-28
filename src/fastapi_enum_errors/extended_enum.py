import inspect
from enum import Enum
from functools import cache
from typing import Any


class ExtendedEnum(Enum):
    @cache
    def _get_docstring(self) -> str | None:
        sourcelines = [l.strip() for l in inspect.getsourcelines(self.__class__)[0]]
        search_str = f"{self.name} = "

        found_str = next(filter(lambda x: search_str in x, sourcelines), None)
        if found_str is None:
            return None

        found_index = sourcelines.index(found_str)
        if found_index == len(sourcelines) - 1:
            return None

        found_doc = sourcelines[found_index + 1]
        if not (found_doc.startswith('"""') and found_doc.endswith('"""')):
            return None

        return found_doc.removesuffix('"""').removeprefix('"""')

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__doc__ = self._get_docstring()
