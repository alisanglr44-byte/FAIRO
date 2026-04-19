"""
AlertMatcher — runs on a schedule, checks live deals against user alerts,
sends Telegram notifications when a deal beats a user's budget.
"""
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)


class AlertMatcher:
    def __init__(self, db, scanner):
        self.db = db
        self.scanner = scanner

    async def run_scan(self, bot=None):
        """Called by the scheduler every 15 minutes."""
        logger.info(f"🔍 Running alert scan at {datetime.now().strftime('%H:%M')}")

        # Get all active alerts
        alerts = await self.db.get_all_active_alerts()
        if not alerts:
            logger.info("No active alerts.")
            return

        # Get current hot deals (already scanned)
        hot_deals = await self.scanner.get_hot_deals(limit=50)

        matched = 0
        for alert in alerts:
            user_id = alert["user_id"]
            route_key = alert["route_key"]  # e.g. "LHR-DXB"
            budget_pp = float(alert["budget_pp"])

            for deal in hot_deals:
                if deal["route_key"] == route_key and deal["price_pp"] <= budget_pp:
                    # Check we haven't already notified this user for this deal today
                    already_sent = await self.db.already_notified(user_id, deal["route_key"], deal["dep_date"])
                    if already_sent:
                        continue

                    # Send notification
                    if bot:
                        try:
                            sym = alert.get("currency_sym", "£")
                            msg = self._format_alert(deal, sym, budget_pp)
                            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                            kb = InlineKeyboardMarkup([[
                                InlineKeyboardButton("👉 Book now", url=deal["affiliate_link"]),
                                InlineKeyboardButton("🔕 Stop alert", callback_data=f"stop_alert_{alert['id']}"),
                            ]])
                            await bot.send_message(user_id, msg, parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)
                            await self.db.log_notification(user_id, deal["route_key"], deal["dep_date"])
                            matched += 1
                        except Exception as e:
                            logger.error(f"Failed to notify user {user_id}: {e}")

        logger.info(f"✅ Alert scan complete. {matched} notifications sent.")

    async def run_hunter_scan(self, bot=None):
        """Update all active Deal Hunters."""
        hunts = await self.db.get_all_active_hunts()
        if not hunts:
            return

        for hunt in hunts:
            user_id = hunt["user_id"]
            destination = hunt["destination"]
            budget_pp = float(hunt["budget_pp"])
            sym = hunt.get("currency_sym", "£")

            # Search for deals to this destination
            deals = await self.scanner.search(destination, budget_pp=budget_pp * 1.5)
            if not deals:
                continue

            best = deals[0]
            prev_best = hunt.get("best_price_pp", 9999)

            if best["price_pp"] < prev_best:
                await self.db.update_hunt_best(hunt["id"], best)

                if bot and best["price_pp"] <= budget_pp:
                    msg = (
                        f"🎯 *Hunt update — {destination}*\n\n"
                        f"Found a deal below your {sym}{budget_pp} budget!\n\n"
                        f"✈️ {best['route']}\n"
                        f"📅 {best['dep_date']} → {best['ret_date']}\n"
                        f"💰 *{sym}{best['price_pp']} pp* — {best['deal_label']}\n\n"
                        f"[👉 Book now]({best['affiliate_link']})"
                    )
                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                    kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton("👉 Book now", url=best["affiliate_link"]),
                        InlineKeyboardButton("⏸ Pause hunt", callback_data=f"pause_hunt_{hunt['id']}"),
                    ]])
                    try:
                        await bot.send_message(user_id, msg, parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)
                    except Exception as e:
                        logger.error(f"Hunter notify failed for user {user_id}: {e}")

    def _format_alert(self, deal: dict, sym: str, budget_pp: float) -> str:
        save_pct = deal["saving_pct"]
        return (
            f"🔔 *Alert triggered!*\n\n"
            f"✈️ *{deal['route']}*\n"
            f"🏷 {deal['deal_label']} — *−{save_pct}%*\n"
            f"📅 {deal['dep_date']} → {deal['ret_date']}\n"
            f"✈️ {deal.get('airline','')}\n\n"
            f"💰 *{sym}{deal['price_pp']} pp* ~~{sym}{deal['was_pp']}~~\n"
            f"_(Your budget: {sym}{budget_pp} pp)_\n\n"
            f"[👉 Book now — deal may not last!]({deal['affiliate_link']})"
        )
