import getpass
import math
import sys
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont
from accounts.models import User
from accounts.validators import StudentPasswordValidator
from movies.models import Favorite, Movie, MovieFile, Review, Watched


DEMO_MOVIES = [
    ("Интерстеллар", 2014, "Команда исследователей отправляется сквозь червоточину на поиски нового дома для человечества.", "INTERSTELLAR", (25, 42, 62)),
    ("Начало", 2010, "Специалист по проникновению в сны получает задание внедрить идею в сознание наследника корпорации.", "INCEPTION", (54, 68, 75)),
    ("Матрица", 1999, "Программист Нео узнаёт, что привычный мир скрывает совсем другую реальность.", "THE MATRIX", (23, 64, 51)),
    ("Шоу Трумана", 1998, "Обычный человек начинает замечать странности в своём идеально устроенном мире.", "THE TRUMAN SHOW", (45, 96, 116)),
    ("Унесённые призраками", 2001, "Девочка Тихиро попадает в мир духов и ищет способ спасти своих родителей.", "SPIRITED AWAY", (92, 49, 62)),
    ("ВАЛЛ·И", 2008, "Маленький робот, оставшийся на опустевшей Земле, отправляется в большое космическое путешествие.", "WALL-E", (103, 71, 42)),
    ("Прибытие", 2016, "Лингвист пытается понять язык загадочных гостей, прибывших на Землю.", "ARRIVAL", (59, 69, 70)),
    ("Остров собак", 2018, "Мальчик отправляется на остров в поисках своего пса и находит верных друзей.", "ISLE OF DOGS", (118, 57, 42)),
    ("Марсианин", 2015, "Астронавт остаётся один на Марсе и использует знания и находчивость, чтобы выжить.", "THE MARTIAN", (126, 66, 36)),
    ("Душа", 2020, "Учитель музыки оказывается в необычном месте и по-новому смотрит на смысл жизни.", "SOUL", (51, 74, 106)),
    ("Человек-паук: Через вселенные", 2018, "Майлз Моралес знакомится с героями из других измерений и учится быть Человеком-пауком.", "SPIDER-VERSE", (86, 43, 77)),
    ("Король Лев", 1994, "Львёнок Симба взрослеет, находит друзей и возвращается домой, чтобы принять ответственность.", "THE LION KING", (121, 88, 35)),
    ("Головоломка", 2015, "Эмоции девочки Райли пытаются помочь ей справиться с переездом и переменами.", "INSIDE OUT", (56, 87, 86)),
    ("Назад в будущее", 1985, "Подросток случайно отправляется в прошлое на машине времени и пытается вернуться домой.", "BACK TO THE FUTURE", (49, 56, 92)),
]


def make_demo_poster(index, title, year, color, path):
    # Это собственные учебные обложки, а не официальные постеры фильмов.
    image = Image.new("RGB", (600, 800))
    pixels = image.load()
    for y in range(800):
        shade = .48 + .7 * (1 - y / 800)
        for x in range(600):
            pixels[x, y] = tuple(min(255, int(c * shade)) for c in color)
    draw = ImageDraw.Draw(image)
    regular = ImageFont.load_default(size=17)
    title_font = ImageFont.load_default(size=38)
    number_font = ImageFont.load_default(size=19)
    draw.text((45, 42), "CINEMA COLLECTION", font=regular, fill="#d0c6ba")
    draw.text((45, 72), f"{index + 1:02d} / {year}", font=number_font, fill="#d0c6ba")
    cx, cy = 300, 345
    for radius in (105, 135, 165):
        draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline="#a0a2a0", width=2)
    angle = index * .55
    dx, dy = int(math.cos(angle)*135), int(math.sin(angle)*135)
    draw.ellipse((cx+dx-23, cy+dy-23, cx+dx+23, cy+dy+23), fill="#d5a46d")
    draw.polygon([(270, 305), (270, 385), (340, 345)], fill="#d5a46d")
    draw.line((45, 604, 555, 604), fill="#99958e", width=1)
    lines = []
    line = ""
    for word in title.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=title_font) > 510 and line:
            lines.append(line); line = word
        else:
            line = candidate
    lines.append(line)
    for i, line in enumerate(lines):
        draw.text((45, 635 + i*46), line, font=title_font, fill="#f3eee7")
    draw.text((45, 758), "STUDENT PROJECT / DEMO POSTER", font=regular, fill="#b0aaa1")
    image.save(path, "PNG")


class Command(BaseCommand):
    help = "Добавить демонстрационные фильмы, двух пользователей и собственные учебные постеры."

    def add_arguments(self, parser):
        parser.add_argument("--passwords-stdin", action="store_true", help="Прочитать два пароля из stdin вместо скрытого ввода")

    def handle(self, *args, **options):
        if User.objects.filter(email__in=["admin@example.test", "student@example.test"]).exists():
            raise CommandError("Демо-пользователи уже существуют. Повторное заполнение отменено: существующие данные не меняются.")
        if options["passwords_stdin"]:
            admin_password = sys.stdin.readline().rstrip("\r\n")
            user_password = sys.stdin.readline().rstrip("\r\n")
        else:
            admin_password = getpass.getpass("Пароль demo-администратора: ")
            user_password = getpass.getpass("Пароль demo-пользователя: ")
        validator = StudentPasswordValidator()
        validator.validate(admin_password)
        validator.validate(user_password)
        directory = Path(settings.MEDIA_ROOT) / "public"
        directory.mkdir(parents=True, exist_ok=True)
        created_files = []
        try:
            with transaction.atomic():
                admin = User.objects.create_superuser(username="admin", email="admin@example.test", password=admin_password)
                student = User.objects.create_user(username="student", email="student@example.test", password=user_password)
                for index, (title, year, description, english_title, color) in enumerate(DEMO_MOVIES):
                    movie = Movie.objects.create(owner=admin, title=title, year=year, description=description)
                    stored_name = f"{uuid4()}.png"
                    path = directory / stored_name
                    created_files.append(path)
                    make_demo_poster(index, english_title, year, color, path)
                    MovieFile.objects.create(movie=movie, original_name=f"demo-{index+1}.png", stored_name=stored_name,
                                             mime="image/png", size_bytes=path.stat().st_size)
                    if index < 6:
                        Watched.objects.create(movie=movie, owner=student)
                        Watched.objects.create(movie=movie, owner=admin)
                        Review.objects.create(movie=movie, owner=student, rating=[10, 9, 9, 8, 10, 9][index],
                                              text="Интересная история и запоминающаяся атмосфера. С удовольствием посмотрю ещё раз.")
                        Review.objects.create(movie=movie, owner=admin, rating=[9, 8, 10, 9, 9, 8][index],
                                              text="Хороший фильм для вечернего просмотра. Особенно понравились герои и музыка.")
                    if index in (0, 2, 4):
                        Favorite.objects.create(owner=student, movie=movie)
        except Exception:
            for path in created_files:
                path.unlink(missing_ok=True)
            raise
        self.stdout.write(self.style.SUCCESS("Созданы 14 фильмов, постеры, отзывы и избранное. Логины: admin@example.test, student@example.test."))
