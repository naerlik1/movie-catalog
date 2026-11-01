# Ubuntu Server VM на MacBook

Для практики используется отдельная Ubuntu Server 24.04 LTS ARM64, запущенная через Lima и Apple Virtualization Framework. У неё 2 ядра, 3 ГБ оперативной памяти и виртуальный диск 24 ГБ. Конфигурация находится в `vm/ubuntu.yaml`.

Внутри Ubuntu работает собственный Docker Engine и три контейнера проекта: PostgreSQL, Django и nginx. Docker Desktop на Mac нужен для прежней локальной копии; для работы уже настроенной VM он не требуется.

## Обычный запуск

1. Дважды нажмите **`Запустить VM.command`** в папке проекта.
2. Дождитесь сообщения «Ubuntu VM готова».
3. Откроется **http://localhost:8084**.

Этот запуск использует уже скачанные образы. Интернет для обычного показа на самом Mac не нужен. Если локальная копия проекта запущена через Docker Desktop, скрипт остановит её контейнеры, чтобы освободить порт 8084. Её тома сохраняются.

Файл **`Остановить VM.command`** корректно выключает Ubuntu. Данные находятся на её виртуальном диске и сохраняются. Файл **`SSH в VM.command`** открывает терминал Ubuntu от пользователя `student`; вход выполняется по SSH-ключу.

То же самое из Terminal на Mac:

```bash
bash scripts/vm.sh start
bash scripts/vm.sh status
bash scripts/vm.sh ssh
bash scripts/vm.sh stop
```

Состояние машины и ключи SSH находятся в `~/.movie-catalog-vm/state`, программа Lima — в `~/.movie-catalog-vm/tools`. Удаление папки с состоянием VM удалит её виртуальный диск и данные.

## Команды внутри Ubuntu

После SSH-входа:

```bash
cat /etc/os-release
uname -m
ip -4 addr show lima0
cd ~/movie-catalog
docker compose ps
curl http://localhost:8084/health
docker compose logs --tail=30 app
```

Рабочая папка проекта в Ubuntu — `/home/student/movie-catalog`. `.env` создан отдельно для этой машины; пароль БД и ключ Django не опубликованы в GitHub. Пользовательские записи и постеры перенесены из локальной копии проекта. Дальнейшие изменения сохраняются в том экземпляре, с которым вы работаете.

Контейнеры используют опубликованные образы `naerlik/movie-catalog-backend:1.0` и `naerlik/movie-catalog-frontend:1.0`. Их ARM64-варианты выбираются автоматически.

## Доступ из локальной сети

В VM nginx работает на порту **8084**. Lima пробрасывает порт **8084 Mac → 8084 VM** на сетевые интерфейсы Mac. С другого компьютера в той же сети нужно открыть `http://IP_MAC:8084`. Текущий адрес выводит `Запустить VM.command`.

При смене Wi-Fi повторно выполните этот запуск: он добавит текущий адрес Mac в настройки Django и обновит контейнеры. Сами данные при этом сохраняются. На втором компьютере используйте ту же обычную Wi-Fi сеть; гостевая сеть может запрещать соединения между устройствами.

Проверка с самого Mac и проверка со второго физического компьютера — отдельные проверки. Успешный запрос на Mac не подтверждает доступ со второго компьютера.

## Проверка перезагрузки Ubuntu

В SSH-терминале запишите идентификатор загрузки, проверьте данные и выполните:

```bash
cat /proc/sys/kernel/random/boot_id
cd ~/movie-catalog
docker compose ps
sudo reboot
```

SSH-соединение закроется. Подождите около минуты и снова откройте `SSH в VM.command`. Проверьте новый `boot_id`, `docker compose ps`, `/health`, фильмы, отзывы и постеры. `restart: unless-stopped` и автоматически запускаемый Docker восстанавливают контейнеры после загрузки Ubuntu.

## Повторная установка на другом Mac с Apple Silicon

Официальные инструкции: [Lima](https://lima-vm.io/docs/installation/), [Docker Engine для Ubuntu](https://docs.docker.com/engine/install/ubuntu/). Для повторения использована Lima 2.2.1.

В Terminal на Mac, из корня проекта:

Если локальная копия проекта уже работает в Docker Desktop, сначала остановите её через `Остановить.command`, чтобы освободить порт 8084.

```bash
vm_root="$HOME/.movie-catalog-vm"
mkdir -p "$vm_root/tools"
curl -fL https://github.com/lima-vm/lima/releases/download/v2.2.1/lima-2.2.1-Darwin-arm64.tar.gz -o "$vm_root/lima.tar.gz"
echo "9e9eacce88f37e185c346bad73aa6136f738d8cdf8c3bb23cd42b071824bc66e  $vm_root/lima.tar.gz" | shasum -a 256 -c -
tar -xzf "$vm_root/lima.tar.gz" -C "$vm_root/tools"
export LIMA_HOME="$vm_root/state"
"$vm_root/tools/bin/limactl" start --name=movies --tty=false vm/ubuntu.yaml
"$vm_root/tools/bin/limactl" shell --workdir /home/student movies bash -s < vm/install-docker.sh
```

Затем откройте SSH и выполните внутри Ubuntu:

```bash
git clone https://github.com/naerlik1/movie-catalog.git ~/movie-catalog
cd ~/movie-catalog
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
openssl rand -hex 32
nano .env
```

Впишите две разные случайные строки в `DJANGO_SECRET_KEY` и `DB_PASSWORD`, а образы задайте так:

```dotenv
BACKEND_IMAGE=naerlik/movie-catalog-backend:1.0
FRONTEND_IMAGE=naerlik/movie-catalog-frontend:1.0
```

Далее в Ubuntu:

```bash
docker compose pull
docker compose up -d --no-build --wait
docker compose exec app python manage.py seed_demo
```

Введите демонстрационные пароли из README. На Mac выполните `bash scripts/vm.sh start`: скрипт настроит адреса и откроет приложение. Полная инструкция для Ubuntu на других гипервизорах находится в `DEPLOY.md`.
