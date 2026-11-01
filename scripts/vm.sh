#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
vm_root="${MOVIE_VM_HOME:-$HOME/.movie-catalog-vm}"
export LIMA_HOME="$vm_root/state"
lima="$vm_root/tools/bin/limactl"
action="${1:-start}"

if [[ ! -x "$lima" || ! -f "$LIMA_HOME/movies/lima.yaml" ]]; then
    echo "Ubuntu VM ещё не установлена. Инструкция: docs/VM.md"
    exit 1
fi

case "$action" in
    stop)
        "$lima" stop movies
        echo "Ubuntu VM остановлена. Данные сохранены."
        ;;
    status)
        "$lima" list movies
        "$lima" shell --workdir /home/student/movie-catalog movies docker compose ps
        ;;
    ssh)
        exec ssh -F "$LIMA_HOME/movies/ssh.config" lima-movies
        ;;
    start)
        # Локальная копия и VM используют один порт 8084.
        docker_bin="$(command -v docker || true)"
        if [[ -z "$docker_bin" && -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
            docker_bin=/Applications/Docker.app/Contents/Resources/bin/docker
        fi
        if [[ -n "$docker_bin" && -f "$project_dir/.env" ]] && "$docker_bin" info >/dev/null 2>&1; then
            export PATH="$(dirname "$docker_bin"):$PATH"
            local_containers="$("$docker_bin" compose --project-directory "$project_dir" ps --status running -q)"
            if [[ -n "$local_containers" ]]; then
                echo "Останавливаю локальную копию проекта, чтобы освободить порт 8084."
                "$docker_bin" compose --project-directory "$project_dir" stop
            fi
        fi

        "$lima" start --tty=false movies
        mac_ip="$(ipconfig getifaddr en0 2>/dev/null || true)"
        "$lima" shell --workdir /home/student movies python3 - "$mac_ip" < "$project_dir/vm/set-hosts.py"
        "$lima" shell --workdir /home/student/movie-catalog movies \
            docker compose up -d --no-build --pull never --wait --wait-timeout 120
        curl --fail --silent --show-error http://localhost:8084/health
        printf '\n\nUbuntu VM готова: http://localhost:8084\n'
        if [[ -n "$mac_ip" ]]; then
            printf 'С другого устройства в той же сети: http://%s:8084\n' "$mac_ip"
        fi
        if [[ "${2:-}" != "--no-browser" ]]; then
            open http://localhost:8084
        fi
        ;;
    *)
        echo "Использование: vm.sh start|stop|status|ssh [--no-browser]"
        exit 1
        ;;
esac
