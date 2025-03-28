import http
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache, cached_property
from typing import Any, Self

from httpx import Response

from fastapi_enum_errors.classproperty import classproperty
from fastapi_enum_errors.exception import JSONHTTPException
from fastapi_enum_errors.extended_enum import ExtendedEnum
from fastapi_enum_errors.models import ErrorResponse


@dataclass
class ErrorEnumMixin:
    error: str
    code: int

    def __hash__(self) -> int:
        return hash(self.error)


class ErrorEnum(ErrorEnumMixin, ExtendedEnum):
    @classproperty
    @abstractmethod
    def error_response_models(self) -> dict:
        """Models that will be used to provide additional information about the error."""
        return {}

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:
        return name.lower()

    def assert_response(self, response: Response, **body_kwargs: Any) -> None:
        """Check the answer in the test for consistency with the error."""
        if response.status_code != self.code:
            raise AssertionError(f"{response.status_code} != {self.code}, {response.json()}")
        if not isinstance(response.json(), dict):
            raise AssertionError(f"Response must be an object. {response.json()}")
        if response.json() != self._as_json_body(**body_kwargs):
            raise AssertionError(f"{response.json()} != {self.value}")

    @cached_property
    def detail(self) -> str | None:
        """Get detail of an error"""
        return self._get_docstring()

    def _as_json_body(self, **kwargs: Any) -> dict[str, Any]:
        response_model_cls = self.error_response_models.get(self.value, ErrorResponse)
        response_model = response_model_cls(detail=self.detail, status_code=self.code, error_code=self.value, **kwargs)
        return response_model.model_dump(mode="json")

    def as_exception(self, **kwargs: Any) -> JSONHTTPException:
        """Use error as an exception"""
        return JSONHTTPException(
            status_code=self.code,
            json_body=self._as_json_body(**kwargs),
        )

    @classmethod
    def build_responses_from_list(cls, errors: Iterable[Self]) -> dict[int | str, dict[str, Any]]:
        """Build FastAPI responses from list of errors"""
        responses: dict[int | str, dict[str, Any]] = {e.code: {} for e in list(set(errors))}
        for code in responses:
            code_errors: list[Self] = list(filter(lambda e: e.code == code, errors))

            additional_schema: dict[str, Any] = {}
            for error in code_errors:
                schema = cls.error_response_models.get(error.value)
                if not schema:
                    continue
                additional_schema |= schema.model_json_schema(mode="serialization").get("properties", {})
            responses[code] = {
                "description": f"{get_initial_status_phrase(code)}\n{'\n'.join(f'- {c.detail}' for c in code_errors)}",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": additional_schema
                            | {
                                "detail": {"type": "string", "enum": [c.detail for c in code_errors]},
                                "status_code": {"type": "integer", "enum": [code]},
                                "error_code": {"type": "string", "enum": [e.error for e in code_errors]},
                            },
                            "required": ["detail", "status_code", "error_code"],
                        },
                        "examples": {
                            e.name: {
                                "value": {
                                    prop: value.get("examples", [""])[0]
                                    for prop, value in cls.error_response_models.get(e.value, ErrorResponse)
                                    .model_json_schema()
                                    .get("properties", {})
                                    .items()
                                }
                                | {"detail": e.detail, "status_code": code, "error_code": e.error},
                                "summary": e.detail,
                            }
                            for e in code_errors
                        },
                    },
                },
            }

        return responses

    @classmethod
    def build_responses(cls, *errors: Self) -> dict[int | str, dict[str, Any]]:
        return cls.build_responses_from_list(errors)

    @classmethod
    def build_md_table_for_all_errors(cls) -> str:
        """Build Markdown table with all of the errors"""
        rows = [("Error Code", "Description", "Status code"), ("------", "------", "------")]

        rows.extend(
            (f"`{error.error}`", error.detail or "Error", f"**{error.code}** {get_initial_status_phrase(error.code)}")
            for error in list(cls)
        )

        print(rows)

        return "\n".join(f"|{'|'.join(r)}|" for r in rows)


@cache
def get_initial_status_phrase(code: int) -> str:
    try:
        return http.HTTPStatus(code).phrase
    except ValueError:
        return "Error"
