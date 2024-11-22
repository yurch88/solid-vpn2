#!/bin/bash
set -e

# Проверяем доступность директории с конфигурациями WireGuard
if [ ! -d "$WG_CONFIG_DIR" ]; then
    echo "Error: WireGuard configuration directory $WG_CONFIG_DIR does not exist."
    exit 1
fi

# Запуск Flask-приложения
exec python3 app.py
