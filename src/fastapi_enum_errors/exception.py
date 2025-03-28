import http
from typing import Any


class JSONHTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        if json_body is None:
            json_body = {"detail": http.HTTPStatus(status_code).phrase, "status": status_code}
        self.status_code = status_code
        self.json_body = json_body
        self.headers = headers

    def __repr__(self) -> str:
        # JSONHTTPException(status_code=400, json_body={"detail": "some error", ...})
        return f"{self.__class__.__name__}(status_code={self.status_code!r}, json_body={self.json_body!r})"
