#!/bin/bash
# Запускаем приложение из папки app/
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug
