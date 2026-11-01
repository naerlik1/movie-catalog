import io
import re
import warnings
from pathlib import Path
from django.utils.http import parse_header_parameters
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from config.exceptions import FileTooLarge, InvalidFileType


class PosterParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        body = stream.read(6 * 1024 * 1024 + 1)
        if len(body) > 6 * 1024 * 1024:
            raise FileTooLarge()
        for header in re.findall(br'(?im)^content-disposition:[^\r\n]*(?:\r?\n[ \t][^\r\n]*)*', body):
            _, parameters = parse_header_parameters(header.decode("latin1"))
            name = parameters.get("filename", "")
            if "/" in name or "\\" in name or name in (".", ".."):
                raise ValidationError({"file": "Имя файла не должно содержать путь."})
        return super().parse(io.BytesIO(body), media_type, parser_context)


def validate_poster(file):
    if file.size > 5 * 1024 * 1024:
        raise FileTooLarge({"file": "Размер постера не должен превышать 5 МБ."})
    suffix = Path(file.name).suffix.lower()
    allowed = {".jpg": ("JPEG", "image/jpeg"), ".jpeg": ("JPEG", "image/jpeg"),
               ".png": ("PNG", "image/png"), ".webp": ("WEBP", "image/webp")}
    if suffix not in allowed or file.content_type != allowed[suffix][1]:
        raise InvalidFileType({"file": "Разрешены JPG, PNG и WEBP с соответствующим MIME-типом."})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(file) as image:
                if image.format != allowed[suffix][0]:
                    raise InvalidFileType({"file": "Содержимое файла не соответствует расширению."})
                image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise InvalidFileType({"file": "Не удалось прочитать изображение."})
    finally:
        file.seek(0)
    return suffix, allowed[suffix][1]
