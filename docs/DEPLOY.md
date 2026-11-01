# Развёртывание на Ubuntu Server

Выполняйте команды под обычным пользователем с `sudo`. Подготовьте Ubuntu Server 22.04/24.04 LTS: 2 vCPU, 2 ГБ RAM, 20 ГБ диска. Для доступа из локальной сети используйте Bridge; при NAT пробросьте 8084 хоста на 8084 VM и 22 хоста на 22 VM. Приложение по заданию работает на 8084, поэтому открывать только порт 80 недостаточно.

На текущем MacBook Ubuntu VM уже настроена через Lima: инструкция запуска и фактические адреса — в [VM.md](VM.md) и [PUBLICATION.md](PUBLICATION.md). SSH подключается через порт Mac 22225 → 22 VM. Ниже приведён общий порядок развёртывания на новой Ubuntu VM.

## 1. Docker и SSH

```bash
sudo apt update
sudo apt install -y ca-certificates curl git ufw openssh-server
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker "$USER"
```

Переподключитесь по SSH, затем:

```bash
docker --version
docker compose version
sudo ufw allow OpenSSH
sudo ufw allow 8084/tcp
sudo ufw enable
sudo ufw status
```

Не публикуйте 5432 и 8000. В Compose у БД и backend нет секции `ports`.

## 2. Репозиторий GitHub

Исходники размещены в публичном репозитории [naerlik1/movie-catalog](https://github.com/naerlik1/movie-catalog), ветка `main`. На VM достаточно клонировать его по команде из раздела 4. Для скачивания вход в GitHub не требуется.

`.env`, `uploads` и зависимости исключены через `.gitignore`. Не добавляйте их принудительно.

## 3. Два личных репозитория Docker-образов

Образы уже опубликованы в публичных репозиториях [backend](https://hub.docker.com/r/naerlik/movie-catalog-backend) и [frontend](https://hub.docker.com/r/naerlik/movie-catalog-frontend). Тег `1.0` содержит обе архитектуры: `linux/amd64` и `linux/arm64`. Docker выберет подходящую для VM автоматически. Для скачивания вход в Docker Hub не требуется.

При обновлении кода выполните `docker login` под владельцем репозиториев и соберите новую версию с новым тегом, например `1.1`:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t naerlik/movie-catalog-backend:1.1 --push ./backend
docker buildx build --platform linux/amd64,linux/arm64 -t naerlik/movie-catalog-frontend:1.1 --push ./frontend
```

Ссылки и контрольные суммы опубликованной версии — в [PUBLICATION.md](PUBLICATION.md).

## 4. Настройки на VM

```bash
git clone https://github.com/naerlik1/movie-catalog.git ~/movie-catalog
cd ~/movie-catalog
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
openssl rand -hex 32
nano .env
```

Впишите две разные случайные строки в `DJANGO_SECRET_KEY`, `DB_PASSWORD`. Сохраните `DB_HOST=db`, `DB_PORT=5432`, `MEDIA_ROOT=/app/uploads`. Настройте:

```dotenv
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,app,IP_VM
CSRF_TRUSTED_ORIGINS=http://IP_VM:8084
APP_PORT=8084
BACKEND_IMAGE=naerlik/movie-catalog-backend:1.0
FRONTEND_IMAGE=naerlik/movie-catalog-frontend:1.0
```

Замените `IP_VM` фактическим IP из `ip a`.

## 5. Запуск опубликованных образов

```bash
docker compose pull
docker compose up -d --no-build
docker compose ps
curl http://localhost:8084/health
docker compose logs --tail=50 app
```

В `ps` три сервиса: `db`, `app`, `nginx`. Состояние — running/healthy; health возвращает `{"status":"ok","database":"ok"}`. Миграции и collectstatic выполняет entrypoint backend.

Для демонстрации:

```bash
docker compose exec app python manage.py seed_demo
```

Задайте тестовые пароли и укажите их в README сдаваемой копии. Либо создайте администратора через `createsuperuser`, зарегистрируйте обычного пользователя через интерфейс и добавьте собственные фильмы.

Откройте с другого компьютера **http://IP_VM:8084**. Проверьте регистрацию, вход, отзыв, избранное, создание фильма администратором, постер и Excel.

## 6. Сохранность данных

Загрузите постер и сохраните несколько записей. Затем:

```bash
docker compose restart
docker compose ps
curl http://localhost:8084/health
```

После восстановления healthy откройте те же записи и постер. Затем перезагрузите VM:

```bash
sudo reboot
```

Переподключитесь по SSH и снова проверьте `docker compose ps`, `/health`, записи и изображение. `restart: unless-stopped` запускает контейнеры после загрузки Docker. Тома `pgdata` и `uploads` переживают перезапуск и пересборку. Не применяйте `down -v` к нужным данным.

## 7. Обновление

Соберите и опубликуйте оба образа с новым одинаковым тегом, например `1.1`. На VM выполните `git pull`, обновите теги в `.env`, затем:

```bash
docker compose pull
docker compose up -d --no-build
```

## 8. Что приложить к сдаче

- Ссылку на GitHub с исходниками.
- Ссылки на личные репозитории backend- и frontend-образов.
- Реальный адрес `http://IP_VM:8084`, доступный проверяющему.
- Тестовый email и пароль в README.
- 3–5 скриншотов, например регистрация, каталог, карточка с отзывами, избранное, добавление фильма.

На локальной машине можно подтвердить сборку и работу в Docker. Доступ из другой сети и сохранность после перезагрузки самой VM проверяются уже на вашей Ubuntu VM.
