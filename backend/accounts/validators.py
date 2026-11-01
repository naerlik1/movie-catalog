import re
from django.core.exceptions import ValidationError


class StudentPasswordValidator:
    def validate(self, password, user=None):
        if not (8 <= len(password) <= 64 and re.search(r"[A-Za-zА-Яа-яЁё]", password)
                and re.search(r"[0-9]", password)):
            raise ValidationError(self.get_help_text())

    def get_help_text(self):
        return "Пароль: от 8 до 64 символов, минимум одна буква и одна цифра"
