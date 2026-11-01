#!/bin/bash
project_dir="$(cd "$(dirname "$0")" && pwd)"
bash "$project_dir/scripts/project.sh" stop
result=$?
if [[ -t 0 ]]; then read -r -p "Нажмите Enter, чтобы закрыть это окно…"; fi
exit "$result"
