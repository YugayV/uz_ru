#!/bin/bash
# Запускаем приложение с указанием полного пути Python-модуля
uvicorn uz_ru.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug
