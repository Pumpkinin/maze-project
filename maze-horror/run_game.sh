#!/usr/bin/env bash
# Запуск игры из корня репозитория (использует движок из maze-studio).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/maze-horror"
python3 main.py "${1:-level_01}"
