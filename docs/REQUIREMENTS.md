# Проверка требований варианта 25

Источник — предоставленный файл «задание 30 вариантов.pages», общая часть и строка «Каталог фильмов». Инструкции установки и деплоя из документа использованы как требования к результату, а не как разрешение менять внешние аккаунты.

| Требование | Где реализовано / как проверить |
| --- | --- |
| Python 3.12, Django 5, DRF, классы | `backend/Dockerfile`, `requirements.txt`, `accounts/views.py`, `movies/views.py` |
| React 18, Vite, Router, REST JSON | `frontend/package.json`, `src/main.jsx`, `src/api.js` |
| PostgreSQL 16, psycopg 3, отдельный контейнер | `docker-compose.yml`, `config/settings.py`; SQLite отсутствует |
| JWT 24 часа, безопасные пароли | `SIMPLE_JWT`, Django PBKDF2, `StudentPasswordValidator` |
| Выход и 401 после него | Клиент удаляет токен, сервер хранит отозванный jti; API-тест |
| Уникальный email без учёта регистра | `User.save`, ограничение `Lower(email)`, RegisterSerializer |
| username и пароль по правилам | Валидаторы моделей и сериализаторов, `frontend/src/validation.js` |
| Ошибки под полями и единый JSON | `config/exceptions.py`, компоненты `FieldError`, `ErrorMessage` |
| 10 входов / минуту / IP | `LoginThrottle`, заголовки nginx, один worker gunicorn; API-тест |
| Movie: title, year, description, poster | `Movie`, связанная запись `MovieFile` под именем `poster` |
| Фильмы добавляет админ | `MoviePermission`, `ProtectedRoute admin`; сервер не доверяет роли из тела запроса |
| Изменяет и удаляет владелец | `MoviePermission`, `PosterUploadView`, `PosterDeleteView` |
| Каталог публичный | GET списка, карточки и отзывов разрешены гостю; записи и файлы меняет владелец-администратор |
| CRUD, подтверждение удаления | API на generic views, `/items/new`, `/items/:id`, `/items/:id/edit`, ConfirmDialog |
| Review: movie, rating 1–10, text | Модель и ReviewSerializer; оценка дополнительно ограничена CHECK в PostgreSQL |
| Один отзыв на фильм от пользователя | Предварительная проверка и UniqueConstraint(movie, owner) |
| Дополнение пользователя: отзыв после просмотра | Личная модель `Watched`, серверная проверка при создании и изменении отзыва; миграция сохраняет старые отзывы |
| Средний рейтинг обновляется | `AVG(reviews__rating)` в запросах списка и карточки; тест добавления, изменения, удаления |
| Favorite, личное избранное | UniqueConstraint(movie, owner), фильтр `scope=favorites`, всегда текущий пользователь |
| Поиск, фильтры, сортировка, пагинация | `movies/filters.py`, `CatalogPagination`, форма списка; один фильтр для Excel и списка |
| Дополнение пользователя: поиск при вводе | Задержка 300 мс через `useEffect`, `setTimeout`, `clearTimeout`, сброс страницы при новом поиске |
| Постеры JPG/PNG/WEBP, 5 МБ | `movies/uploads.py`, клиентская проверка; тест MIME, расширения, содержимого и размера |
| 415/413, nginx 16m | Исключения API и обработчик 413 в nginx |
| UUID, оригинальное имя, MIME, размер, дата | Таблица `files`, API возвращает метаданные |
| Запрет `../x` | Проверка исходных filename в multipart до очистки Django |
| Публичные файлы `/media/` | nginx alias только к `uploads/public/`; приватных файлов вариант 25 не требует |
| CASCADE и удаление файла с диска | ForeignKey/OneToOne с Django CASCADE, post_delete + on_commit; API-тест |
| Excel: авторизация и личная подборка | По уточнению преподавателя клиент выгружает только своё избранное; сервер фильтрует `is_favorite=True`, админу доступен общий каталог; API-тест |
| Excel: фильтры, типы, оформление, лимит, формулы | `movies/export.py`; проверка книги через openpyxl в тестах |
| Только память для Excel | BytesIO, без временного файла |
| Страница загрузки, ошибки, пустые состояния | React-компоненты и страницы |
| Данные и файлы переживают restart | Именованные тома pgdata, uploads; локальная проверка, VM по инструкции |
| Три контейнера, внешний порт 8084 | `docker-compose.yml`; наружу опубликован только nginx |
| health и автоматические миграции/статика | `/health`, healthcheck, `backend/entrypoint.sh` |
| Удобный локальный запуск на MacBook | Три `.command`-файла и `scripts/project.sh`; использование готовых образов при повторном запуске |
| `.env.example`, `.gitignore`, README | В корне; .env не входит в git и архив сдачи |
| 3–5 скриншотов | `docs/screenshots/` |
| GitHub и два личных репозитория образов | Публичные ссылки и команды скачивания — в `PUBLICATION.md`; образы для AMD64 и ARM64 |
| Ubuntu VM, доступ по IP, reboot VM | Инструкция подготовлена в `DEPLOY.md`; развёртывание и окончательная проверка ожидают создания VM |

Уточнение преподавателя: обычный пользователь не добавляет фильмы; его экспорт доступен в разделе «Избранное» и содержит личную подборку. Правила отражены в README и проверках API. Сводный лист Excel нужен только семи другим темам, поэтому у варианта 25 его нет.
