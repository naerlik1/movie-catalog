#!/bin/bash
cd "$(dirname "$0")"
bash scripts/vm.sh start
read -r -p "Нажмите Enter, чтобы закрыть окно…"
