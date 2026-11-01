from django.db import IntegrityError
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class InvalidFileType(APIException):
    status_code = 415
    default_detail = "Разрешены только изображения JPG, PNG и WEBP."


class FileTooLarge(APIException):
    status_code = 413
    default_detail = "Размер постера не должен превышать 5 МБ."


def api_exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        return Response({"errors": {"non_field_errors": "Такая запись уже существует."}}, status=400)
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict) and "detail" in data:
        errors = {"non_field_errors": str(data["detail"])}
    elif isinstance(data, dict):
        errors = {key: " ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                  for key, value in data.items()}
    else:
        errors = {"non_field_errors": str(data)}
    response.data = {"errors": errors}
    return response
