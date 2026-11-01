#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"
action="${1:-start}"
open_browser=1
if [[ "${2:-}" == "--no-browser" ]]; then
    open_browser=0
fi
case "$action" in
    start|stop|rebuild) ;;
    *) echo "Использование: project.sh start|stop|rebuild [--no-browser]"; exit 1 ;;
esac

if command -v docker >/dev/null 2>&1; then
    docker_bin="$(command -v docker)"
elif [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
    docker_bin="/Applications/Docker.app/Contents/Resources/bin/docker"
else
    echo "Не найден Docker. Для запуска нужен установленный Docker Desktop."
    exit 1
fi
export PATH="$(dirname "$docker_bin"):$PATH"

compose() {
    "$docker_bin" compose "$@"
}

if ! "$docker_bin" info >/dev/null 2>&1; then
    if [[ "$action" == "stop" ]]; then
        echo "Нет соединения с Docker. Если Docker Desktop закрыт, проект уже не работает."
        exit 1
    fi
    if [[ "$(uname -s)" == "Darwin" && -d /Applications/Docker.app ]]; then
        echo "Открываю Docker Desktop. Ожидаю готовности…"
        open -a Docker
    else
        echo "Docker не запущен. Запустите его и повторите."
        exit 1
    fi
    docker_ready=0
    for ((attempt=0; attempt<120; attempt++)); do
        if "$docker_bin" info >/dev/null 2>&1; then
            docker_ready=1
            break
        fi
        sleep 1
    done
    if [[ "$docker_ready" == "0" ]]; then
        echo "Docker ещё не готов. Дождитесь его запуска и повторите."
        exit 1
    fi
fi

if [[ ! -f .env ]]; then
    if [[ "$action" == "stop" ]]; then
        echo "Проект ещё не настроен: файла .env нет."
        exit 1
    fi
    if "$docker_bin" volume inspect movie-catalog_pgdata >/dev/null 2>&1; then
        echo "База проекта уже существует, но файла .env нет."
        echo "Восстановите .env из исходной папки проекта: в нём пароль этой базы."
        exit 1
    fi
    echo "Создаю локальный .env со случайными ключом и паролем БД."
    django_key="$(openssl rand -hex 32)"
    db_password="$(openssl rand -hex 24)"
    umask 077
    while IFS= read -r line || [[ -n "$line" ]]; do
        case "$line" in
            DJANGO_SECRET_KEY=*) printf 'DJANGO_SECRET_KEY=%s\n' "$django_key" ;;
            DB_PASSWORD=*) printf 'DB_PASSWORD=%s\n' "$db_password" ;;
            *) printf '%s\n' "$line" ;;
        esac
    done < .env.example > .env
    chmod 600 .env
    unset django_key db_password
fi

case "$action" in
    stop)
        compose stop
        echo "Проект остановлен. База данных и постеры сохранены."
        exit 0
        ;;
esac

images_missing=0
while IFS= read -r image; do
    if ! "$docker_bin" image inspect "$image" >/dev/null 2>&1; then
        images_missing=1
    fi
done < <(compose config --images)

if [[ "$images_missing" == "1" || "$action" == "rebuild" ]]; then
    echo "Собираю проект. Для первой сборки или обновления нужен интернет."
    compose build
    if ! "$docker_bin" image inspect postgres:16-alpine >/dev/null 2>&1; then
        compose pull db
    fi
fi

# На обычном повторном запуске не обращаемся к реестру Docker-образов.
compose up -d --no-build --pull never --wait --wait-timeout 90
catalog_port="$(awk -F= '/^APP_PORT=/{print $2; exit}' .env | tr -d '\r')"
catalog_port="${catalog_port:-8084}"
if [[ ! "$catalog_port" =~ ^[0-9]+$ ]]; then
    echo "APP_PORT в .env должен быть числом, например 8084."
    exit 1
fi
catalog_url="http://localhost:$catalog_port"
curl --fail --silent --show-error "$catalog_url/health"
printf '\n\nКаталог готов: %s\n' "$catalog_url"
echo "Тестовые аккаунты указаны в README.md."
if [[ "$open_browser" == "1" && "$(uname -s)" == "Darwin" ]]; then
    open "$catalog_url"
fi
