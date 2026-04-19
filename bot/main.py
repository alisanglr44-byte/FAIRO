"""
Fairo Telegram Bot — main entry point
Uses python-telegram-bot v20 (async)
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from config import Config
from scanner.deal_scanner import DealScanner
from scanner.alert_matcher import AlertMatcher
from db.models import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database(Config.DATABASE_URL)
scanner = DealScanner(Config.RAPIDAPI_KEY)
matcher = AlertMatcher(db, scanner)


def deal_message(deal: dict, sym: str = "£") -> str:
    save_pct = deal["saving_pct"]
    urgency = "🔴" if deal.get("seats_left", 99) < 5 else "🟡" if deal.get("seats_left", 99) < 15 else "🟢"
    if deal["type"] == "flight":
        return (
            f"✈️ *{deal['route']}*\n"
            f"🏷 {deal['deal_label']}  •  {urgency}\n"
            f"📅 Dep: {deal['dep_date']}  →  Ret: {deal['ret_date']}\n"
            f"✈️ {deal['airline']}  •  {deal['duration']}\n\n"
            f"💰 *{sym}{deal['price_pp']} pp* ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*\n\n"
            f"[👉 Book now]({deal['affiliate_link']})"
        )
    elif deal["type"] == "hotel":
        return (
            f"🏨 *{deal['name']}*  —  {deal['city']}\n"
            f"🏷 {deal['deal_label']}  •  {deal['stars']}⭐\n"
            f"📅 Check in: {deal['dep_date']}  →  Out: {deal['ret_date']}  •  {deal['nights']} nights\n\n"
            f"💰 *{sym}{deal['price_pp']} pp* ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*\n\n"
            f"[👉 Book now]({deal['affiliate_link']})"
        )
    else:
        return (
            f"📦 *{deal['route']}* — Package\n"
            f"🏷 {deal['deal_label']}\n"
            f"📅 {deal['dep_date']}  →  {deal['ret_date']}  •  {deal.get('nights',7)} nights\n\n"
            f"💰 *{sym}{deal['price_pp']} pp* ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*\n\n"
            f"[👉 Book now]({deal['affiliate_link']})"
        )


def main_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    labels = {
        "en": ["🔍 Search", "🔥 Hot deals", "🔔 My alerts", "🎯 Hunter", "⚙️ Settings"],
        "tr": ["🔍 Ara", "🔥 Sıcak fırsatlar", "🔔 Uyarılarım", "🎯 Avcı", "⚙️ Ayarlar"],
        "ar": ["🔍 بحث", "🔥 صفقات ساخنة", "🔔 تنبيهاتي", "🎯 صياد", "⚙️ إعدادات"],
        "hi": ["🔍 खोजें", "🔥 गर्म डील", "🔔 मेरे अलर्ट", "🎯 हंटर", "⚙️ सेटिंग्स"],
        "es": ["🔍 Buscar", "🔥 Ofertas", "🔔 Mis alertas", "🎯 Cazador", "⚙️ Ajustes"],
        "fr": ["🔍 Rechercher", "🔥 Offres", "🔔 Mes alertes", "🎯 Chasseur", "⚙️ Paramètres"],
        "de": ["🔍 Suchen", "🔥 Angebote", "🔔 Meine Alarme", "🎯 Jäger", "⚙️ Einstellungen"],
    }
    l = labels.get(lang, labels["en"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(l[0], callback_data="search"),
         InlineKeyboardButton(l[1], callback_data="hot")],
        [InlineKeyboardButton(l[2], callback_data="alerts"),
         InlineKeyboardButton(l[3], callback_data="hunter")],
        [InlineKeyboardButton(l[4], callback_data="settings")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.upsert_user(user.id, user.username, user.language_code or "en")
    lang = await db.get_user_lang(user.id)
    greetings = {
        "en": f"☀️ Welcome to *Fairo*, {user.first_name}!\n\nTravel prices, finally fair. I scan flights, hotels and packages 24/7 and alert you the moment a deal drops below your budget.\n\n*What do you want to do?*",
        "tr": f"☀️ *Fairo*'ya hoş geldiniz, {user.first_name}!\n\nSeyahat fiyatları, sonunda adil. Uçuşları, otelleri ve paketleri 7/24 tarıyorum.\n\n*Ne yapmak istersiniz?*",
        "ar": f"☀️ مرحباً بك في *فارو*، {user.first_name}!\n\nأسعار سفر عادلة أخيراً. أفحص الرحلات والفنادق والباقات على مدار الساعة.\n\n*ماذا تريد أن تفعل؟*",
        "hi": f"☀️ *Fairo* में आपका स्वागत है, {user.first_name}!\n\nयात्रा की कीमतें, आखिरकार उचित। मैं 24/7 उड़ानें, होटल और पैकेज स्कैन करता हूं।\n\n*आप क्या करना चाहते हैं?*",
        "es": f"☀️ Bienvenido a *Fairo*, {user.first_name}!\n\nPrecios de viaje, finalmente justos. Escaneo vuelos, hoteles y paquetes 24/7.\n\n*¿Qué quieres hacer?*",
        "fr": f"☀️ Bienvenue sur *Fairo*, {user.first_name}!\n\nDes prix de voyage enfin justes. Je scanne les vols, hôtels et forfaits 24h/24.\n\n*Que voulez-vous faire ?*",
        "de": f"☀️ Willkommen bei *Fairo*, {user.first_name}!\n\nReisepreise, endlich fair. Ich scanne Flüge, Hotels und Pakete rund um die Uhr.\n\n*Was möchten Sie tun?*",
    }
    text = greetings.get(lang, greetings["en"])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard(lang))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "☀️ *How Fairo works*\n\n"
        "🔍 *Search* — tell me where you want to go and your budget pp. I scan flights, hotels and packages.\n\n"
        "🔥 *Hot deals* — the best deals live right now. Error fares, flash sales, last-minute.\n\n"
        "🔔 *Alerts* — save a route and I watch it 24/7. Instant ping the moment a deal appears.\n\n"
        "🎯 *Hunter* — continuous mission to a destination. I scan every 15 min and update you live.\n\n"
        "⚙️ *Settings* — change language, home city and currency.\n\n"
        "💸 *100% free* — Fairo earns a small affiliate commission when you book, at zero extra cost to you.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )


async def hot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    prefs = await db.get_user_prefs(user_id)
    sym = prefs.get("currency_sym", "£")
    await update.message.reply_text("🔥 Scanning for hot deals right now...")
    deals = await scanner.get_hot_deals(limit=5)
    if not deals:
        await update.message.reply_text("No hot deals right now — check back in 15 minutes!")
        return
    for deal in deals:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("👉 Book now", url=deal["affiliate_link"]),
            InlineKeyboardButton("🔔 Alert me", callback_data=f"alert_{deal['route_key']}"),
        ]])
        await update.message.reply_text(deal_message(deal, sym), parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✈️ Flights", callback_data="search_flights"),
         InlineKeyboardButton("🏨 Hotels", callback_data="search_hotels")],
        [InlineKeyboardButton("📦 Package", callback_data="search_package"),
         InlineKeyboardButton("⚡ Mix (all)", callback_data="search_mix")],
    ])
    await update.message.reply_text(
        "🔍 *What are you looking for?*\n\n⚡ *Mix* shows flights, hotels and packages together sorted by biggest saving.",
        parse_mode="Markdown", reply_markup=kb
    )


async def alerts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    alerts = await db.get_user_alerts(user_id)
    if not alerts:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add alert", callback_data="add_alert")]])
        await update.message.reply_text(
            "🔔 *No alerts yet.*\n\nAdd a route and I'll watch it 24/7 — alerting you instantly when a deal drops below your budget.",
            parse_mode="Markdown", reply_markup=kb
        )
        return
    text = "🔔 *Your alerts:*\n\n"
    kb_rows = []
    for alert in alerts:
        status = "🟢" if alert["active"] else "⚫"
        text += f"{status} {alert['route']} — under {alert['currency_sym']}{alert['budget_pp']} pp\n"
        kb_rows.append([
            InlineKeyboardButton(f"{'Pause' if alert['active'] else 'Resume'}", callback_data=f"toggle_alert_{alert['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"del_alert_{alert['id']}"),
        ])
    kb_rows.append([InlineKeyboardButton("➕ Add new alert", callback_data="add_alert")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb_rows))


async def hunter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    hunts = await db.get_user_hunts(user_id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Start a new hunt", callback_data="new_hunt")]])
    if not hunts:
        await update.message.reply_text(
            "🎯 *Deal Hunter*\n\nSet me on a mission. Pick a destination and budget — I scan every 15 minutes and alert you the moment the best deal appears.\n\nNo hunt running yet.",
            parse_mode="Markdown", reply_markup=kb
        )
        return
    text = "🎯 *Your active hunts:*\n\n"
    for hunt in hunts:
        status = "🔍 Scanning..." if hunt["status"] == "searching" else "✅ Deal found!"
        text += f"{status} *{hunt['destination']}* — under {hunt['currency_sym']}{hunt['budget_pp']} pp\n\n"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Language", callback_data="set_lang"),
         InlineKeyboardButton("💱 Currency", callback_data="set_currency")],
        [InlineKeyboardButton("📍 Home city", callback_data="set_city")],
    ])
    await update.message.reply_text("⚙️ *Settings*", parse_mode="Markdown", reply_markup=kb)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "hot":
        prefs = await db.get_user_prefs(user_id)
        sym = prefs.get("currency_sym", "£")
        await query.message.reply_text("🔥 Fetching hot deals...")
        deals = await scanner.get_hot_deals(limit=5)
        for deal in deals:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("👉 Book now", url=deal["affiliate_link"])]])
            await query.message.reply_text(deal_message(deal, sym), parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)

    elif data == "search":
        await search_cmd(query, context)
    elif data == "alerts":
        await alerts_cmd(query, context)
    elif data == "hunter":
        await hunter_cmd(query, context)
    elif data == "settings":
        await settings_cmd(query, context)

    elif data == "set_lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
            [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
             InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
            [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
             InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr")],
            [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
             InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_it")],
            [InlineKeyboardButton("🇵🇹 Português", callback_data="lang_pt"),
             InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
        ])
        await query.message.reply_text("🌐 Choose your language:", reply_markup=kb)

    elif data.startswith("lang_"):
        lang = data.replace("lang_", "")
        await db.set_user_lang(user_id, lang)
        await query.message.reply_text("✅ Language updated!", reply_markup=main_keyboard(lang))

    elif data == "set_currency":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 GBP £", callback_data="cur_GBP_£"),
             InlineKeyboardButton("🇺🇸 USD $", callback_data="cur_USD_$")],
            [InlineKeyboardButton("🇪🇺 EUR €", callback_data="cur_EUR_€"),
             InlineKeyboardButton("🇹🇷 TRY ₺", callback_data="cur_TRY_₺")],
            [InlineKeyboardButton("🇮🇳 INR ₹", callback_data="cur_INR_₹"),
             InlineKeyboardButton("🇦🇪 AED د.إ", callback_data="cur_AED_د.إ")],
            [InlineKeyboardButton("🇦🇺 AUD A$", callback_data="cur_AUD_A$"),
             InlineKeyboardButton("🇨🇦 CAD C$", callback_data="cur_CAD_C$")],
        ])
        await query.message.reply_text("💱 Choose your currency:", reply_markup=kb)

    elif data.startswith("cur_"):
        parts = data.split("_", 2)
        curr_code, curr_sym = parts[1], parts[2]
        await db.set_user_currency(user_id, curr_code, curr_sym)
        await query.message.reply_text(f"✅ Currency set to {curr_sym}")

    elif data == "add_alert":
        context.user_data["state"] = "awaiting_alert_route"
        await query.message.reply_text(
            "🔔 *New alert*\n\nSend me the route, e.g:\n`London → Dubai`\nor\n`LHR → DXB`",
            parse_mode="Markdown"
        )

    elif data == "new_hunt":
        context.user_data["state"] = "awaiting_hunt_dest"
        await query.message.reply_text(
            "🎯 *New hunt*\n\nWhere do you want to go?\n\nExamples:\n`Dubai`\n`Tenerife`\n`Anywhere warm`",
            parse_mode="Markdown"
        )

    elif data.startswith("toggle_alert_"):
        alert_id = int(data.replace("toggle_alert_", ""))
        await db.toggle_alert(user_id, alert_id)
        await alerts_cmd(query, context)

    elif data.startswith("del_alert_"):
        alert_id = int(data.replace("del_alert_", ""))
        await db.delete_alert(user_id, alert_id)
        await query.message.reply_text("🗑 Alert deleted.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = context.user_data.get("state")

    if state == "awaiting_alert_route":
        context.user_data["alert_route"] = text
        context.user_data["state"] = "awaiting_alert_budget"
        await update.message.reply_text(
            f"✅ Route: *{text}*\n\nMax budget per person? (e.g. `150`)",
            parse_mode="Markdown"
        )

    elif state == "awaiting_alert_budget":
        try:
            budget = float(text.replace("£","").replace("$","").replace("€","").strip())
            route = context.user_data.get("alert_route", "")
            prefs = await db.get_user_prefs(user_id)
            await db.create_alert(user_id, route, budget, prefs.get("currency","GBP"), prefs.get("currency_sym","£"))
            context.user_data["state"] = None
            await update.message.reply_text(
                f"🔔 *Alert set!*\n\n{route} — under {prefs.get('currency_sym','£')}{budget} pp\n\nRunning 24/7. I'll ping you the moment a deal appears.",
                parse_mode="Markdown", reply_markup=main_keyboard()
            )
        except ValueError:
            await update.message.reply_text("Please send just a number, e.g. `150`", parse_mode="Markdown")

    elif state == "awaiting_hunt_dest":
        context.user_data["hunt_dest"] = text
        context.user_data["state"] = "awaiting_hunt_budget"
        await update.message.reply_text(
            f"🎯 Destination: *{text}*\n\nMax budget per person? (e.g. `200`, or `0` for no limit)",
            parse_mode="Markdown"
        )

    elif state == "awaiting_hunt_budget":
        try:
            budget = float(text.replace("£","").replace("$","").replace("€","").strip())
            dest = context.user_data.get("hunt_dest", "Anywhere")
            prefs = await db.get_user_prefs(user_id)
            await db.create_hunt(user_id, dest, budget, prefs.get("currency","GBP"), prefs.get("currency_sym","£"))
            context.user_data["state"] = None
            await update.message.reply_text(
                f"🎯 *Hunt started!*\n\n📍 {dest}\n💰 Under {prefs.get('currency_sym','£')}{budget if budget > 0 else '∞'} pp\n⏱ Scanning every 15 minutes\n\nI'll alert you when I find the best deal.",
                parse_mode="Markdown", reply_markup=main_keyboard()
            )
        except ValueError:
            await update.message.reply_text("Please send just a number, e.g. `200`", parse_mode="Markdown")

    else:
        await update.message.reply_text(f"🔍 Searching for *{text}*...", parse_mode="Markdown")
        prefs = await db.get_user_prefs(user_id)
        deals = await scanner.search(text, budget_pp=prefs.get("budget_pp", 500))
        if deals:
            sym = prefs.get("currency_sym", "£")
            for deal in deals[:3]:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("👉 Book now", url=deal["affiliate_link"])]])
                await update.message.reply_text(deal_message(deal, sym), parse_mode="Markdown", reply_markup=kb, disable_web_page_preview=True)
        else:
            await update.message.reply_text(
                "No deals found right now. Want me to set an alert and ping you when one appears?",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔔 Set alert", callback_data="add_alert")]])
            )


def main():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("hot", hot_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("alerts", alerts_cmd))
    app.add_handler(CommandHandler("hunter", hunter_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("🚀 Fairo bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
