"""
Background worker — runs the alert scan and hunter scan every 15 minutes.
Started automatically by Railway alongside the bot.
"""
import asyncio
import logging
from telegram.ext import Application
from config import Config
from scanner.deal_scanner import DealScanner
from scanner.alert_matcher import AlertMatcher
from db.models import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker():
    db = Database(Config.DATABASE_URL)
    scanner = DealScanner(Config.RAPIDAPI_KEY)
    matcher = AlertMatcher(db, scanner)

    # Build a bot instance just for sending messages
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    await app.initialize()
    bot = app.bot

    logger.info("🔄 Fairo background worker started")

    while True:
        try:
            logger.info("⏱ Running scheduled scan...")
            await matcher.run_scan(bot=bot)
            await matcher.run_hunter_scan(bot=bot)
            logger.info(f"✅ Scan complete. Sleeping {Config.SCAN_INTERVAL_MINUTES} minutes.")
        except Exception as e:
            logger.error(f"Worker error: {e}")

        await asyncio.sleep(Config.SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(run_worker())
