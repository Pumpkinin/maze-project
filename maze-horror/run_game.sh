#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 main.py "${1:-level_01}"
