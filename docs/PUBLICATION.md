# Публикация проекта

## GitHub

Исходники и документация: [naerlik1/movie-catalog](https://github.com/naerlik1/movie-catalog), публичный репозиторий, ветка `main`.

```bash
git clone https://github.com/naerlik1/movie-catalog.git
cd movie-catalog
```

В репозитории есть `.env.example`, миграции, тесты, Dockerfile обоих приложений, Docker Compose и пять скриншотов. Реальный `.env`, зависимости, загруженные пользователем постеры и данные БД исключены.

## Развёрнутый экземпляр Ubuntu VM

Ubuntu Server 24.04 LTS ARM64 работает на MacBook через Lima. Адрес на самом Mac: **http://localhost:8084**. Адрес для другого компьютера в текущей локальной сети: **http://192.168.1.3:8084** (NAT: порт Mac 8084 → порт VM 8084). Внешний интернет-доступ не настраивался; для этой проверки компьютеры должны находиться в одной сети.

Тестовые аккаунты приведены в README. Пользовательские записи и все 15 постеров перенесены из локального экземпляра. Запуск, SSH, остановка и повторная установка — в [VM.md](VM.md).

Пользователь подтвердил открытие сайта с телефона в той же Wi-Fi сети. Проверка именно со второго компьютера пока не подтверждена.

## Docker Hub

Опубликованы два публичных репозитория, тег версии — `1.0`:

- Backend: https://hub.docker.com/r/naerlik/movie-catalog-backend
- Frontend: https://hub.docker.com/r/naerlik/movie-catalog-frontend

Оба образа содержат варианты `linux/amd64` и `linux/arm64`: один и тот же тег подходит для x86 Ubuntu VM и ARM, включая MacBook с Apple Silicon. Docker выбирает архитектуру автоматически.

```bash
docker pull naerlik/movie-catalog-backend:1.0
docker pull naerlik/movie-catalog-frontend:1.0
```

Для запуска опубликованных образов в `.env` задайте:

```dotenv
BACKEND_IMAGE=naerlik/movie-catalog-backend:1.0
FRONTEND_IMAGE=naerlik/movie-catalog-frontend:1.0
```

Затем:

```bash
docker compose pull
docker compose up -d --no-build
```

Публичность проверена запросами к Docker Hub без авторизации. Для обоих тегов подтверждены обе архитектуры.

Контрольные суммы списков образов:

```text
backend  sha256:170c56e6930ab88c44be2e8b15c91c168e0b7a2086b3042320251f17302d4651
frontend sha256:83fa13a3fea31493b3e327af3c630753111458a249afc5598d4e24858f042d83
```

Файл `.env`, реальные пароли БД, ключ Django, загруженные пользователем файлы и данные PostgreSQL в образы не включены. Их задают и сохраняют отдельно на машине запуска.
