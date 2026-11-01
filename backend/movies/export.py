from datetime import date
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from rest_framework.exceptions import ValidationError


def excel_text(value):
    text = str(value or "")
    # Также удаляем недопустимые для XML управляющие символы.
    text = "".join(c for c in text if ord(c) >= 32 or c in "\t\n\r")
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text


def export_movies(queryset):
    if queryset.count() > 10000:
        raise ValidationError({"export": "Найдено больше 10 000 фильмов. Уточните поиск или фильтры."})
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Данные"
    sheet.append(["ID", "Название", "Год", "Описание", "Постер", "Средний рейтинг", "Число отзывов", "Создан", "Обновлён"])
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="334155")
    for movie in queryset:
        poster = getattr(movie, "poster", None)
        sheet.append([
            movie.id, excel_text(movie.title), movie.year, excel_text(movie.description),
            excel_text(poster.original_name if poster else ""),
            round(movie.average_rating, 2) if movie.average_rating is not None else None,
            movie.reviews_count, timezone.localtime(movie.created_at).date(),
            timezone.localtime(movie.updated_at).date(),
        ])
        for cell in sheet[sheet.max_row][7:9]:
            cell.number_format = "DD.MM.YYYY"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        width = min(65, max(len(str(cell.value or "")) for cell in column) + 2)
        sheet.column_dimensions[column[0].column_letter].width = max(12, width)
        for cell in column[1:]:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="movies_{date.today().isoformat()}.xlsx"'
    return response
