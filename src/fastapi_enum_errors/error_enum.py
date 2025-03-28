import http
from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache, cached_property
from typing import Any, Self

import httpx

from fastapi_enum_errors.classproperty import classproperty
from fastapi_enum_errors.exception import JSONHTTPException
from fastapi_enum_errors.extended_enum import ExtendedEnum
from fastapi_enum_errors.models import ErrorResponse


@dataclass(frozen=True)
class ErrorEnumMixin:
    error: str
    code: int

    def __hash__(self) -> int:
        return hash(self.error)


class ErrorEnum(ErrorEnumMixin, ExtendedEnum):
    @classproperty
    @abstractmethod
    def error_response_models(cls) -> dict:
        """
        Models that will be used to provide additional information about the error.
        Must be implemented by subclasses.
        """
        return {}

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:
        return name.lower()

    def assert_response(self, response: httpx.Response, **body_kwargs: Any) -> None:
        """
        Check that the given response matches the error.

        Raises:
            AssertionError: If the status code or body do not match expectations.
        """
        if response.status_code != self.code:
            raise AssertionError(f"{response.status_code} != {self.code}, {response.json()}")
        body = response.json()
        if not isinstance(body, dict):
            raise AssertionError(f"Response must be an object. {body}")
        if body != self._as_json_body(**body_kwargs):
            raise AssertionError(f"{body} != {self.error}")

    @cached_property
    def detail(self) -> str | None:
        """Get the error detail taken from the method or docstring (if implemented)."""
        return self._get_docstring()

    def _as_json_body(self, **kwargs: Any) -> dict[str, Any]:
        """
        Build the JSON body for the error response given (optional) extra parameters.
        """
        response_model_cls = self.error_response_models.get(self, ErrorResponse)
        response_model = response_model_cls(detail=self.detail, status_code=self.code, error_code=self.error, **kwargs)
        return response_model.model_dump(mode="json")

    def as_exception(self, **kwargs: Any) -> JSONHTTPException:
        """
        Convert this error into an HTTP exception with a JSON body.
        """
        return JSONHTTPException(
            status_code=self.code,
            json_body=self._as_json_body(**kwargs),
        )

    @classmethod
    def build_responses_from_list(cls, errors: Iterable[Self]) -> dict[int, dict[str, Any]]:
        """
        Build FastAPI responses from a list of errors.

        The method returns a dictionary mapping status codes to the
        corresponding response schema and examples.
        """
        # Use a set to reduce duplicates
        unique_errors = set(errors)
        responses: dict[int, dict[str, Any]] = {error.code: {} for error in unique_errors}

        for code in responses:
            code_errors = [error for error in unique_errors if error.code == code]
            additional_schema: dict[str, Any] = {}

            for error in code_errors:
                schema = cls.error_response_models.get(error)
                if schema:
                    schema_properties = schema.model_json_schema(mode="serialization").get("properties", {})
                    additional_schema |= schema_properties

            responses[code] = {
                "description": (
                    f"{get_initial_status_phrase(code)}\n" + "\n".join(f"- {error.detail}" for error in code_errors)
                ),
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": additional_schema
                            | {
                                "detail": {
                                    "type": "string",
                                    "enum": [error.detail for error in code_errors],
                                },
                                "status_code": {"type": "integer", "enum": [code]},
                                "error_code": {"type": "string", "enum": [error.error for error in code_errors]},
                            },
                            "required": ["detail", "status_code", "error_code"],
                        },
                        "examples": {
                            error.name: {
                                "value": {
                                    **{
                                        prop: value.get("examples", [""])[0]
                                        for prop, value in cls.error_response_models.get(error, ErrorResponse)
                                        .model_json_schema()
                                        .get("properties", {})
                                        .items()
                                    },
                                    "detail": error.detail,
                                    "status_code": code,
                                    "error_code": error.error,
                                },
                                "summary": error.detail,
                            }
                            for error in code_errors
                        },
                    },
                },
            }
        return responses

    @classmethod
    def build_responses(cls, *errors: Self) -> dict[int, dict[str, Any]]:
        """
        Build FastAPI responses from given errors as varargs.
        """
        return cls.build_responses_from_list(errors)

    @classmethod
    def build_md_table_for_all_errors(cls) -> str:
        """
        Build a Markdown table summarizing all errors in the enum.
        """
        header = ("Error Code", "Description", "Status code")
        separator = ("------", "------", "------")
        rows = [header, separator]

        rows.extend(
            (
                f"`{error.error}`",
                error.detail or "Error",
                f"**{error.code}** {get_initial_status_phrase(error.code)}",
            )
            for error in list(cls)
        )

        return "\n".join("|" + "|".join(row) + "|" for row in rows)


@cache
def get_initial_status_phrase(code: int) -> str:
    try:
        return http.HTTPStatus(code).phrase
    except ValueError:
        return "Error"
