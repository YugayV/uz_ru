import asyncio
import logging
from tg_bot.bot import start_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        pass
