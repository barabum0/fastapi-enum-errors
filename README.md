# FastAPI Enum Errors

---

[![Stable Version](https://img.shields.io/pypi/v/fastapi-enum-errors?color=blue)](https://pypi.org/project/fastapi-enum-errors/)
[![Downloads](https://img.shields.io/pypi/dm/fastapi-enum-errors)](https://pypistats.org/packages/fastapi-enum-errors)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

A library for defining and handling HTTP errors in your FastAPI applications using Python enums. It lets you create
structured error definitions that automatically generate standardized JSON responses, API documentation, and even
detailed Markdown tables for error summaries.

## Features

- **Enum-Based Error Definitions:** Define HTTP errors as enum members with associated error codes and descriptions.
- **Automatic JSON Response Generation:** Each error can build its own JSON body (optionally enhanced with extra
  details).
- **Custom Exception Conversion:** Easily convert enum errors into HTTP exceptions for FastAPI.
- **FastAPI Responses Schema:** Build OpenAPI response definitions from your enum errors, with schema properties and
  examples.
- **Documentation Utilities:** Generate Markdown tables summarizing all defined errors.
- **Automatic Docstring Integration:** Extract human-friendly error details from docstrings defined right after enum
  members.

## Installation

Install the package via pip:

```bash
pip install fastapi-enum-errors
```

> **Note:** This project requires [FastAPI](https://fastapi.tiangolo.com/), [httpx](https://www.python-httpx.org/),
> and [Pydantic](https://docs.pydantic.dev/) as peer dependencies.

## Quick Start

Define your error responses and errors by extending the base classes provided by the library.

### 1. Define a Custom Error Response Model

You can extend the built-in `ErrorResponse` model to add additional details to your error responses:

```python
from pydantic import Field
from fastapi_enum_errors.models import ErrorResponse


class NotSoImportantErrorDetails(ErrorResponse):
    some_ids: list[int] = Field(
        examples=[[123, 456, 789]],
        description="List of relevant IDs for the error context."
    )
```

### 2. Define Your Error Enum

Extend `ErrorEnum` to declare your project's errors. Use `auto()` for automatic error code generation and specify the
HTTP status code for each error. The docstring for each member serves as the error description.

```python
from enum import auto
from fastapi_enum_errors import ErrorEnum, classproperty


class SomeErrors(ErrorEnum):
    SOME_VERY_IMPORTANT_ERROR = (auto(), 404)
    """THIS ERROR IS VERY VERY IMPORTANT"""

    NOT_SO_IMPORTANT_ERROR = (auto(), 500)
    """This error is not very important, but it has some additional details."""

    @classproperty
    def error_response_models(cls) -> dict:
        # Map specific errors to their response models.
        return {
            cls.NOT_SO_IMPORTANT_ERROR: NotSoImportantErrorDetails,
        }
```

### 3. Using the Enum in Your Application

The library automatically configures your application by including the built‑in helper function `errorenum_prepare_app`.
You just need to call it to ensure your FastAPI (or Starlette) application has the correct exception handler.

#### a. Converting an Error to an Exception

Below is an example that shows how to raise an error:

```python
from fastapi import FastAPI
from fastapi_enum_errors import errorenum_prepare_app

app = FastAPI()
errorenum_prepare_app(app)


@app.get("/example")
async def example():
    # Raise an enum error.
    raise SomeErrors.SOME_VERY_IMPORTANT_ERROR.as_exception()

@app.get("/example_2")
async def example_2():
    # Raise an enum error with additional fields.
    raise SomeErrors.NOT_SO_IMPORTANT_ERROR.as_exception(some_ids=[1, 2, 3])

# When these endpoints are hit, FastAPI will respond with a properly formatted JSON error body.
```

#### b. Asserting API Responses in Tests

Use the `assert_response` method to verify that the HTTP response from your API matches the expected error format:

```python
import httpx

# Assert basic error.
response = httpx.get("http://localhost:8000/example")
SomeErrors.SOME_VERY_IMPORTANT_ERROR.assert_response(response)

# Assert basic error and check additional fields.
response = httpx.get("http://localhost:8000/example_2")
SomeErrors.SOME_VERY_IMPORTANT_ERROR.assert_response(response, some_ids=[1, 2, 3])
```

#### c. Generating API Response Documentation

Automatically build the OpenAPI response specifications for an endpoint by calling:

```python
from fastapi import FastAPI
from fastapi_enum_errors import errorenum_prepare_app

app = FastAPI()
errorenum_prepare_app(app)


@app.get(
    "/example",
    responses=SomeErrors.build_responses(
        SomeErrors.SOME_VERY_IMPORTANT_ERROR,
    ),
)
async def example():
    # Raise an enum error.
    raise SomeErrors.SOME_VERY_IMPORTANT_ERROR.as_exception()

@app.get(
    "/example_2",
    responses=SomeErrors.build_responses(
        SomeErrors.NOT_SO_IMPORTANT_ERROR,
    ),
)
async def example_2():
    # Raise an enum error with additional fields.
    raise SomeErrors.NOT_SO_IMPORTANT_ERROR.as_exception(some_ids=[1, 2, 3])
```

This returns a dictionary mapping HTTP status codes to response details, including:

- A description combining the HTTP status phrase and error details.
- A JSON schema for the error response.
- Examples for documentation.

#### d. Generating a Markdown Table Summary

Generate a Markdown table summarizing all errors defined in your enum:

```python
table_md = SomeErrors.build_md_table_for_all_errors()
print(table_md)
```

Example output:

| Error Code                  | Description                                                           | Status code                   |
|-----------------------------|-----------------------------------------------------------------------|-------------------------------|
| `some_very_important_error` | THIS ERROR IS VERY VERY IMPORTANT                                     | **404** Not Found             |
| `not_so_important_error`    | This error is not very important, but it has some additional details. | **500** Internal Server Error |l

Then, you can insert this table right into your documentation!

## Contributing

Contributions are welcome! If you find any bugs or have feature requests, please open an issue or submit a pull request
on GitHub.

## License

Distributed under the MIT License. See `LICENSE` for more information.
