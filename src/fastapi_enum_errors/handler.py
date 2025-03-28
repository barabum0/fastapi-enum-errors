import json

from fastapi.utils import is_body_allowed_for_status_code
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
