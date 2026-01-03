#!/bin/bash
python -u run_bot.py &
exec uvicorn main:app --host 0.0.0.0 --port $PORT
