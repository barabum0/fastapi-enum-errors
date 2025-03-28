import json

from fastapi.utils import is_body_allowed_for_status_code
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fastapi_enum_errors.exception import JSONHTTPException


async def jsonhttp_exception_handler(request: Request, exc: JSONHTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return JSONResponse(
        json.loads(json.dumps(exc.json_body, ensure_ascii=False, default=str)),
        status_code=exc.status_code,
        headers=headers,
    )


def errorenum_prepare_app(app: Starlette) -> None:
    """Configure the application for fastapi-enum-errors.
    :param app: The Starlette/FastAPI application instance (typically FastAPI/APIRouter object)
    """
    app.add_exception_handler(JSONHTTPException, jsonhttp_exception_handler)  # type: ignore[arg-type]
