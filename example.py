from enum import auto

from pydantic import Field

from fastapi_enum_errors import ErrorEnum, ErrorResponse, classproperty


class NotSoImportantErrorDetails(ErrorResponse):
    some_ids: list[int] = Field(examples=[[123, 456, 789]])


class SomeErrors(ErrorEnum):
    SOME_VERY_IMPORTANT_ERROR = (auto(), 404)
    """THIS ERROR IS VERY VERY IMPORTANT"""

    NOT_SO_IMPORTANT_ERROR = (auto(), 500)
    """This error is not very important, but it has some additional details."""

    @classproperty
    def error_response_models(cls) -> dict:
        return {
            cls.NOT_SO_IMPORTANT_ERROR: NotSoImportantErrorDetails,
        }


print(SomeErrors.__members__)  # noqa: T201
# {'SOME_VERY_IMPORTANT_ERROR': <SomeErrors.SOME_VERY_IMPORTANT_ERROR: error='some_very_important_error', code=404>}

print(SomeErrors.build_md_table_for_all_errors())  # noqa: T201
# | Error Code                  | Description                                                           | Status code                   |
# |-----------------------------|-----------------------------------------------------------------------|-------------------------------|
# | `some_very_important_error` | THIS ERROR IS VERY VERY IMPORTANT                                     | **404** Not Found             |
# | `not_so_important_error`    | This error is not very important, but it has some additional details. | **500** Internal Server Error |

print(SomeErrors.build_responses(SomeErrors.SOME_VERY_IMPORTANT_ERROR))  # noqa: T201
# {
#    "404":{
#       "description":"Not Found\n- THIS ERROR IS VERY VERY IMPORTANT",
#       "content":{
#          "application/json":{
#             "schema":{
#                "type":"object",
#                "properties":{
#                   "detail":{
#                      "type":"string",
#                      "enum":[
#                         "THIS ERROR IS VERY VERY IMPORTANT"
#                      ]
#                   },
#                   "status_code":{
#                      "type":"integer",
#                      "enum":[
#                         404
#                      ]
#                   },
#                   "error_code":{
#                      "type":"string",
#                      "enum":[
#                         "some_very_important_error"
#                      ]
#                   }
#                },
#                "required":[
#                   "detail",
#                   "status_code",
#                   "error_code"
#                ]
#             },
#             "examples":{
#                "SOME_VERY_IMPORTANT_ERROR":{
#                   "value":{
#                      "detail":"THIS ERROR IS VERY VERY IMPORTANT",
#                      "status_code":404,
#                      "error_code":"some_very_important_error"
#                   },
#                   "summary":"THIS ERROR IS VERY VERY IMPORTANT"
#                }
#             }
#          }
#       }
#    }
# }
