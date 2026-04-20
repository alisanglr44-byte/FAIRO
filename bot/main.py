"""
Fairo Telegram Bot — production ready
All 10 languages · Every button wired · Every flow complete
"""
import logging
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

# ── TRANSLATIONS ──────────────────────────────────────────────────────────────
T = {
    "en": {
        "welcome": "☀️ Welcome to *Fairo*, {name}!\n\nTravel prices, finally fair. I scan flights, hotels and packages 24/7 and alert you the moment a deal drops below your budget.\n\n*What do you want to do?*",
        "search": "🔍 Search", "hot": "🔥 Hot deals", "alerts": "🔔 My alerts",
        "hunter": "🎯 Hunter", "settings": "⚙️ Settings", "back": "« Back",
        "help": (
            "☀️ *How Fairo works*\n\n"
            "🔍 *Search* — tell me where you want to go and your budget per person. I scan flights, hotels and packages instantly.\n\n"
            "🔥 *Hot deals* — the best deals live right now. Error fares, flash sales and last-minute steals.\n\n"
            "🔔 *Alerts* — save a route and I watch it 24/7. Instant alert the moment a deal drops below your budget.\n\n"
            "🎯 *Hunter* — the most powerful feature. I scan a destination continuously every 15 minutes until you pause.\n\n"
            "⚙️ *Settings* — change language, home city and currency.\n\n"
            "💸 *100% free* — Fairo earns a small affiliate commission when you book, at zero extra cost to you."
        ),
        "search_prompt": "🔍 *What are you looking for?*\n\n⚡ *Mix* shows flights, hotels and packages together sorted by biggest saving.",
        "flights": "✈️ Flights", "hotels": "🏨 Hotels", "package": "📦 Package", "mix": "⚡ Mix (all)",
        "search_from": "Where are you flying *from*?\n\nSend a city or airport code, e.g. `London` or `LHR`",
        "search_to": "Where do you want to *go*?\n\nSend a city, airport or `Anywhere`",
        "search_budget": "What's your *max budget per person*?\n\nSend a number e.g. `200`, or `any` for no limit",
        "searching": "🔍 Searching for deals on *{query}*...",
        "no_deals": "No deals found right now. Try setting an alert and I'll ping you when one appears!",
        "set_alert_btn": "🔔 Set alert",
        "hot_scanning": "🔥 Scanning for hot deals right now...",
        "no_hot": "No hot deals right now — check back in 15 minutes!",
        "alert_me": "🔔 Alert me", "book_now": "👉 Book now",
        "no_alerts": "🔔 *No alerts yet.*\n\nAdd a route and I'll watch it 24/7 — alerting you the moment a deal drops below your budget.",
        "add_alert": "➕ Add alert", "add_new_alert": "➕ Add new alert",
        "your_alerts": "🔔 *Your alerts:*\n\n",
        "pause": "⏸ Pause", "resume": "▶️ Resume", "delete": "🗑 Delete",
        "alert_deleted": "🗑 Alert deleted.",
        "alert_route_prompt": "🔔 *New alert*\n\nSend me the route you want to watch, e.g:\n`London → Dubai`\nor just the destination:\n`Dubai`",
        "alert_budget_prompt": "✅ Route: *{route}*\n\nWhat's your max budget per person?\nSend a number e.g. `150`",
        "alert_set": "🔔 *Alert set!*\n\n*{route}* — under {sym}{budget} pp\n\n🟢 Running 24/7. I'll ping you the moment a deal appears.",
        "invalid_budget": "Please send just a number, e.g. `150`",
        "no_hunter": "🎯 *Deal Hunter*\n\nSet me on a mission. Pick a destination and budget — I scan every 15 minutes and alert you the moment the best deal appears.\n\nNo hunts running yet.",
        "start_hunt": "🎯 Start a new hunt",
        "your_hunts": "🎯 *Your active hunts:*\n\n",
        "hunt_searching": "🔍 Scanning...", "hunt_found": "✅ Deal found!",
        "hunt_dest_prompt": "🎯 *New hunt*\n\nWhere do you want to go?\n\nExamples:\n• `Dubai`\n• `Tenerife`\n• `Anywhere warm`\n• `Anywhere`",
        "hunt_budget_prompt": "📍 Destination: *{dest}*\n\nMax budget per person?\nSend a number e.g. `200`, or `0` for no limit",
        "hunt_started": "🎯 *Hunt started!*\n\n📍 {dest}\n💰 Under {sym}{budget} pp\n⏱ Scanning every 15 minutes\n\nI'll alert you the moment a deal appears.",
        "hunt_no_limit": "No limit",
        "pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Resume", "stop_hunt": "✕ Stop",
        "settings_menu": "⚙️ *Settings*\n\nWhat would you like to change?",
        "lang_btn": "🌐 Language", "curr_btn": "💱 Currency", "city_btn": "📍 Home city",
        "lang_prompt": "🌐 *Choose your language:*",
        "lang_set": "✅ Language updated!",
        "curr_prompt": "💱 *Choose your currency:*",
        "curr_set": "✅ Currency set to {sym}",
        "city_prompt": "📍 *Home city*\n\nSend your home city or airport code, e.g. `London` or `LHR`\n\nThis sets your default departure point for searches.",
        "city_set": "✅ Home city set to *{city}*",
        "pp": "pp", "nights": "nights", "return_trip": "return", "oneway": "one-way",
        "best_deal": "Best deal found",
        "dep": "Dep", "ret": "Ret", "checkin": "Check in", "checkout": "Check out",
    },
    "es": {
        "welcome": "☀️ ¡Bienvenido a *Fairo*, {name}!\n\nPrecios de viaje, finalmente justos. Escaneo vuelos, hoteles y paquetes 24/7.\n\n*¿Qué quieres hacer?*",
        "search": "🔍 Buscar", "hot": "🔥 Ofertas calientes", "alerts": "🔔 Mis alertas",
        "hunter": "🎯 Cazador", "settings": "⚙️ Ajustes", "back": "« Volver",
        "help": "☀️ *Cómo funciona Fairo*\n\n🔍 *Buscar* — dime dónde quieres ir y tu presupuesto. Escaneo vuelos, hoteles y paquetes.\n\n🔥 *Ofertas calientes* — las mejores ofertas en vivo ahora mismo.\n\n🔔 *Alertas* — guarda una ruta y la vigilo 24/7. Aviso instantáneo cuando aparece una oferta.\n\n🎯 *Cazador* — escaneo continuo cada 15 minutos hasta que lo pauses.\n\n⚙️ *Ajustes* — idioma, ciudad y moneda.\n\n💸 *100% gratis*",
        "search_prompt": "🔍 *¿Qué estás buscando?*\n\n⚡ *Mix* muestra vuelos, hoteles y paquetes juntos ordenados por mayor ahorro.",
        "flights": "✈️ Vuelos", "hotels": "🏨 Hoteles", "package": "📦 Paquete", "mix": "⚡ Mix (todo)",
        "search_from": "¿Desde dónde vuelas?\n\nEnvía una ciudad o código de aeropuerto, ej. `Madrid` o `MAD`",
        "search_to": "¿A dónde quieres ir?\n\nEnvía una ciudad o `Cualquier lugar`",
        "search_budget": "¿Cuál es tu presupuesto máximo por persona?\n\nEnvía un número ej. `200`, o `sin límite`",
        "searching": "🔍 Buscando ofertas para *{query}*...",
        "no_deals": "No hay ofertas ahora. ¡Configura una alerta y te aviso cuando aparezca una!",
        "set_alert_btn": "🔔 Crear alerta",
        "hot_scanning": "🔥 Buscando las mejores ofertas ahora...",
        "no_hot": "No hay ofertas calientes ahora — ¡vuelve en 15 minutos!",
        "alert_me": "🔔 Alertarme", "book_now": "👉 Reservar",
        "no_alerts": "🔔 *Sin alertas aún.*\n\nAgrega una ruta y la vigilo 24/7 — avisándote al instante cuando baje de tu presupuesto.",
        "add_alert": "➕ Agregar alerta", "add_new_alert": "➕ Nueva alerta",
        "your_alerts": "🔔 *Tus alertas:*\n\n",
        "pause": "⏸ Pausar", "resume": "▶️ Reanudar", "delete": "🗑 Borrar",
        "alert_deleted": "🗑 Alerta eliminada.",
        "alert_route_prompt": "🔔 *Nueva alerta*\n\nEnvíame la ruta, ej:\n`Madrid → Dubai`\no simplemente el destino:\n`Dubai`",
        "alert_budget_prompt": "✅ Ruta: *{route}*\n\n¿Presupuesto máximo por persona?\nEnvía un número ej. `150`",
        "alert_set": "🔔 *¡Alerta configurada!*\n\n*{route}* — bajo {sym}{budget} pp\n\n🟢 Funcionando 24/7. Te aviso en cuanto aparezca una oferta.",
        "invalid_budget": "Por favor envía solo un número, ej. `150`",
        "no_hunter": "🎯 *Cazador de Ofertas*\n\nEnvíame en misión. Elige destino y presupuesto — escaneo cada 15 minutos.\n\nSin cacerías activas aún.",
        "start_hunt": "🎯 Nueva caza",
        "your_hunts": "🎯 *Tus cacerías activas:*\n\n",
        "hunt_searching": "🔍 Buscando...", "hunt_found": "✅ ¡Oferta encontrada!",
        "hunt_dest_prompt": "🎯 *Nueva caza*\n\n¿A dónde quieres ir?\n\nEjemplos:\n• `Dubai`\n• `Tenerife`\n• `Cualquier lugar cálido`\n• `Cualquier lugar`",
        "hunt_budget_prompt": "📍 Destino: *{dest}*\n\n¿Presupuesto máximo por persona?\nEnvía un número ej. `200`, o `0` sin límite",
        "hunt_started": "🎯 *¡Cacería iniciada!*\n\n📍 {dest}\n💰 Bajo {sym}{budget} pp\n⏱ Escaneando cada 15 minutos\n\nTe alerto en cuanto aparezca una oferta.",
        "hunt_no_limit": "Sin límite",
        "pause_hunt": "⏸ Pausar", "resume_hunt": "▶️ Reanudar", "stop_hunt": "✕ Detener",
        "settings_menu": "⚙️ *Ajustes*\n\n¿Qué quieres cambiar?",
        "lang_btn": "🌐 Idioma", "curr_btn": "💱 Moneda", "city_btn": "📍 Ciudad origen",
        "lang_prompt": "🌐 *Elige tu idioma:*",
        "lang_set": "✅ ¡Idioma actualizado!",
        "curr_prompt": "💱 *Elige tu moneda:*",
        "curr_set": "✅ Moneda: {sym}",
        "city_prompt": "📍 *Ciudad de origen*\n\nEnvía tu ciudad o aeropuerto, ej. `Madrid`\n\nEsto establece tu punto de salida por defecto.",
        "city_set": "✅ Ciudad establecida: *{city}*",
        "pp": "pp", "nights": "noches", "return_trip": "ida y vuelta", "oneway": "solo ida",
        "best_deal": "Mejor oferta encontrada",
        "dep": "Sal", "ret": "Reg", "checkin": "Entrada", "checkout": "Salida",
    },
    "fr": {
        "welcome": "☀️ Bienvenue sur *Fairo*, {name}!\n\nDes prix de voyage enfin justes. Je scanne les vols, hôtels et forfaits 24h/24.\n\n*Que voulez-vous faire ?*",
        "search": "🔍 Recherche", "hot": "🔥 Offres brûlantes", "alerts": "🔔 Mes alertes",
        "hunter": "🎯 Chasseur", "settings": "⚙️ Paramètres", "back": "« Retour",
        "help": "☀️ *Comment fonctionne Fairo*\n\n🔍 *Recherche* — dites-moi où vous voulez aller et votre budget. Je scanne les vols, hôtels et forfaits.\n\n🔥 *Offres brûlantes* — les meilleures offres en direct maintenant.\n\n🔔 *Alertes* — sauvegardez un trajet et je le surveille 24h/24. Alerte instantanée.\n\n🎯 *Chasseur* — scan continu toutes les 15 minutes jusqu'à ce que vous mettiez en pause.\n\n⚙️ *Paramètres* — langue, ville et devise.\n\n💸 *100% gratuit*",
        "search_prompt": "🔍 *Que cherchez-vous ?*\n\n⚡ *Mix* affiche vols, hôtels et forfaits ensemble triés par plus grande économie.",
        "flights": "✈️ Vols", "hotels": "🏨 Hôtels", "package": "📦 Forfait", "mix": "⚡ Mix (tout)",
        "search_from": "D'où partez-vous ?\n\nEnvoyez une ville ou un code aéroport, ex. `Paris` ou `CDG`",
        "search_to": "Où voulez-vous aller ?\n\nEnvoyez une ville ou `N'importe où`",
        "search_budget": "Votre budget maximum par personne ?\n\nEnvoyez un nombre ex. `200`, ou `illimité`",
        "searching": "🔍 Recherche d'offres pour *{query}*...",
        "no_deals": "Pas d'offres pour l'instant. Créez une alerte et je vous préviendrai !",
        "set_alert_btn": "🔔 Créer une alerte",
        "hot_scanning": "🔥 Recherche des meilleures offres maintenant...",
        "no_hot": "Pas d'offres brûlantes — revenez dans 15 minutes !",
        "alert_me": "🔔 M'alerter", "book_now": "👉 Réserver",
        "no_alerts": "🔔 *Pas d'alertes.*\n\nAjoutez un trajet et je le surveille 24h/24 — alerte instantanée quand une offre apparaît.",
        "add_alert": "➕ Ajouter une alerte", "add_new_alert": "➕ Nouvelle alerte",
        "your_alerts": "🔔 *Vos alertes :*\n\n",
        "pause": "⏸ Pause", "resume": "▶️ Reprendre", "delete": "🗑 Supprimer",
        "alert_deleted": "🗑 Alerte supprimée.",
        "alert_route_prompt": "🔔 *Nouvelle alerte*\n\nEnvoyez le trajet, ex:\n`Paris → Dubaï`\nou juste la destination:\n`Dubaï`",
        "alert_budget_prompt": "✅ Trajet : *{route}*\n\nBudget max par personne ?\nEnvoyez un nombre ex. `150`",
        "alert_set": "🔔 *Alerte créée !*\n\n*{route}* — sous {sym}{budget} pp\n\n🟢 Active 24h/24. Je vous préviens dès qu'une offre apparaît.",
        "invalid_budget": "Envoyez juste un nombre, ex. `150`",
        "no_hunter": "🎯 *Chasseur d'Offres*\n\nEnvoyez-moi en mission. Choisissez une destination et un budget — je scanne toutes les 15 minutes.\n\nPas de chasse active.",
        "start_hunt": "🎯 Nouvelle chasse",
        "your_hunts": "🎯 *Vos chasses actives :*\n\n",
        "hunt_searching": "🔍 Scan...", "hunt_found": "✅ Offerte trouvée !",
        "hunt_dest_prompt": "🎯 *Nouvelle chasse*\n\nOù voulez-vous aller ?\n\nExemples :\n• `Dubaï`\n• `Tenerife`\n• `N'importe où de chaud`\n• `N'importe où`",
        "hunt_budget_prompt": "📍 Destination : *{dest}*\n\nBudget max par personne ?\nEnvoyez un nombre ex. `200`, ou `0` illimité",
        "hunt_started": "🎯 *Chasse lancée !*\n\n📍 {dest}\n💰 Sous {sym}{budget} pp\n⏱ Scan toutes les 15 minutes\n\nJe vous alerte dès qu'une offre apparaît.",
        "hunt_no_limit": "Illimité",
        "pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Reprendre", "stop_hunt": "✕ Arrêter",
        "settings_menu": "⚙️ *Paramètres*\n\nQue voulez-vous modifier ?",
        "lang_btn": "🌐 Langue", "curr_btn": "💱 Devise", "city_btn": "📍 Ville de départ",
        "lang_prompt": "🌐 *Choisissez votre langue :*",
        "lang_set": "✅ Langue mise à jour !",
        "curr_prompt": "💱 *Choisissez votre devise :*",
        "curr_set": "✅ Devise : {sym}",
        "city_prompt": "📍 *Ville de départ*\n\nEnvoyez votre ville ou aéroport, ex. `Paris`\n\nCela définit votre point de départ par défaut.",
        "city_set": "✅ Ville définie : *{city}*",
        "pp": "pp", "nights": "nuits", "return_trip": "aller-retour", "oneway": "aller simple",
        "best_deal": "Meilleure offre trouvée",
        "dep": "Dép", "ret": "Ret", "checkin": "Arrivée", "checkout": "Départ",
    },
    "de": {
        "welcome": "☀️ Willkommen bei *Fairo*, {name}!\n\nReisepreise, endlich fair. Ich scanne Flüge, Hotels und Pakete rund um die Uhr.\n\n*Was möchten Sie tun?*",
        "search": "🔍 Suche", "hot": "🔥 Heiße Angebote", "alerts": "🔔 Meine Alarme",
        "hunter": "🎯 Jäger", "settings": "⚙️ Einstellungen", "back": "« Zurück",
        "help": "☀️ *So funktioniert Fairo*\n\n🔍 *Suche* — sagen Sie mir wohin und Ihr Budget. Ich scanne Flüge, Hotels und Pakete.\n\n🔥 *Heiße Angebote* — die besten Angebote live jetzt.\n\n🔔 *Alarme* — Strecke speichern, ich überwache 24/7. Sofortige Benachrichtigung.\n\n🎯 *Jäger* — kontinuierliches Scannen alle 15 Minuten.\n\n⚙️ *Einstellungen* — Sprache, Stadt und Währung.\n\n💸 *100% kostenlos*",
        "search_prompt": "🔍 *Was suchen Sie?*\n\n⚡ *Mix* zeigt Flüge, Hotels und Pakete zusammen, sortiert nach größter Ersparnis.",
        "flights": "✈️ Flüge", "hotels": "🏨 Hotels", "package": "📦 Paket", "mix": "⚡ Mix (alles)",
        "search_from": "Von wo fliegen Sie?\n\nStadt oder Flughafencode, z.B. `Berlin` oder `BER`",
        "search_to": "Wohin möchten Sie?\n\nStadt oder `Irgendwo`",
        "search_budget": "Maximales Budget pro Person?\n\nZahl eingeben z.B. `200`, oder `unbegrenzt`",
        "searching": "🔍 Suche Angebote für *{query}*...",
        "no_deals": "Keine Angebote gerade. Alarm setzen und ich benachrichtige Sie!",
        "set_alert_btn": "🔔 Alarm setzen",
        "hot_scanning": "🔥 Suche heiße Angebote jetzt...",
        "no_hot": "Keine heißen Angebote — in 15 Minuten nochmal schauen!",
        "alert_me": "🔔 Alarm", "book_now": "👉 Jetzt buchen",
        "no_alerts": "🔔 *Noch keine Alarme.*\n\nStrecke hinzufügen und ich überwache 24/7 — sofortige Benachrichtigung.",
        "add_alert": "➕ Alarm hinzufügen", "add_new_alert": "➕ Neuer Alarm",
        "your_alerts": "🔔 *Ihre Alarme:*\n\n",
        "pause": "⏸ Pause", "resume": "▶️ Fortsetzen", "delete": "🗑 Löschen",
        "alert_deleted": "🗑 Alarm gelöscht.",
        "alert_route_prompt": "🔔 *Neuer Alarm*\n\nStrecke senden, z.B:\n`Berlin → Dubai`\noder nur das Ziel:\n`Dubai`",
        "alert_budget_prompt": "✅ Strecke: *{route}*\n\nMax. Budget pro Person?\nZahl senden z.B. `150`",
        "alert_set": "🔔 *Alarm gesetzt!*\n\n*{route}* — unter {sym}{budget} pp\n\n🟢 Läuft 24/7. Ich benachrichtige Sie sofort wenn ein Angebot erscheint.",
        "invalid_budget": "Bitte nur eine Zahl senden, z.B. `150`",
        "no_hunter": "🎯 *Angebotsjäger*\n\nAuf Mission schicken. Ziel und Budget wählen — ich scanne alle 15 Minuten.\n\nNoch keine aktive Jagd.",
        "start_hunt": "🎯 Neue Jagd",
        "your_hunts": "🎯 *Ihre aktiven Jagden:*\n\n",
        "hunt_searching": "🔍 Suche...", "hunt_found": "✅ Angebot gefunden!",
        "hunt_dest_prompt": "🎯 *Neue Jagd*\n\nWohin möchten Sie?\n\nBeispiele:\n• `Dubai`\n• `Teneriffa`\n• `Irgendwo warm`\n• `Irgendwo`",
        "hunt_budget_prompt": "📍 Ziel: *{dest}*\n\nMax. Budget pro Person?\nZahl senden z.B. `200`, oder `0` unbegrenzt",
        "hunt_started": "🎯 *Jagd gestartet!*\n\n📍 {dest}\n💰 Unter {sym}{budget} pp\n⏱ Scan alle 15 Minuten\n\nIch alarmiere Sie sobald ein Angebot erscheint.",
        "hunt_no_limit": "Unbegrenzt",
        "pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Fortsetzen", "stop_hunt": "✕ Stoppen",
        "settings_menu": "⚙️ *Einstellungen*\n\nWas möchten Sie ändern?",
        "lang_btn": "🌐 Sprache", "curr_btn": "💱 Währung", "city_btn": "📍 Heimatstadt",
        "lang_prompt": "🌐 *Sprache wählen:*",
        "lang_set": "✅ Sprache aktualisiert!",
        "curr_prompt": "💱 *Währung wählen:*",
        "curr_set": "✅ Währung: {sym}",
        "city_prompt": "📍 *Heimatstadt*\n\nStadt oder Flughafencode senden, z.B. `Berlin`\n\nDies setzt Ihren Standard-Abflugort.",
        "city_set": "✅ Heimatstadt: *{city}*",
        "pp": "pp", "nights": "Nächte", "return_trip": "Hin-Rück", "oneway": "Hinfahrt",
        "best_deal": "Bestes Angebot gefunden",
        "dep": "Ab", "ret": "An", "checkin": "Check-in", "checkout": "Check-out",
    },
    "ar": {
        "welcome": "☀️ مرحباً بك في *فارو*، {name}!\n\nأسعار سفر عادلة أخيراً. أفحص الرحلات والفنادق والباقات على مدار الساعة.\n\n*ماذا تريد أن تفعل؟*",
        "search": "🔍 بحث", "hot": "🔥 صفقات ساخنة", "alerts": "🔔 تنبيهاتي",
        "hunter": "🎯 صياد", "settings": "⚙️ إعدادات", "back": "رجوع »",
        "help": "☀️ *كيف يعمل فارو*\n\n🔍 *البحث* — أخبرني أين تريد الذهاب وميزانيتك. أفحص الرحلات والفنادق والباقات.\n\n🔥 *الصفقات الساخنة* — أفضل الصفقات الحية الآن.\n\n🔔 *التنبيهات* — احفظ مساراً وأراقبه 24/7. تنبيه فوري.\n\n🎯 *الصياد* — مسح مستمر كل 15 دقيقة.\n\n⚙️ *الإعدادات* — اللغة والمدينة والعملة.\n\n💸 *مجاني 100%*",
        "search_prompt": "🔍 *ماذا تبحث عن؟*\n\n⚡ *المزيج* يعرض الرحلات والفنادق والباقات معاً مرتبة حسب أكبر توفير.",
        "flights": "✈️ رحلات", "hotels": "🏨 فنادق", "package": "📦 باقة", "mix": "⚡ مزيج (الكل)",
        "search_from": "من أين تسافر؟\n\nأرسل مدينة أو رمز المطار، مثل `دبي` أو `DXB`",
        "search_to": "إلى أين تريد الذهاب؟\n\nأرسل مدينة أو `في أي مكان`",
        "search_budget": "ما هو الحد الأقصى لميزانيتك للشخص؟\n\nأرسل رقماً مثل `200`، أو `بلا حد`",
        "searching": "🔍 البحث عن صفقات لـ *{query}*...",
        "no_deals": "لا توجد صفقات الآن. أضف تنبيهاً وسأخبرك عند ظهور صفقة!",
        "set_alert_btn": "🔔 إضافة تنبيه",
        "hot_scanning": "🔥 البحث عن أفضل الصفقات الآن...",
        "no_hot": "لا توجد صفقات ساخنة الآن — تحقق بعد 15 دقيقة!",
        "alert_me": "🔔 تنبيهي", "book_now": "← احجز الآن",
        "no_alerts": "🔔 *لا تنبيهات بعد.*\n\nأضف مساراً وسأراقبه 24/7 — تنبيه فوري عند ظهور صفقة.",
        "add_alert": "➕ إضافة تنبيه", "add_new_alert": "➕ تنبيه جديد",
        "your_alerts": "🔔 *تنبيهاتك:*\n\n",
        "pause": "⏸ إيقاف", "resume": "▶️ استئناف", "delete": "🗑 حذف",
        "alert_deleted": "🗑 تم حذف التنبيه.",
        "alert_route_prompt": "🔔 *تنبيه جديد*\n\nأرسل المسار، مثل:\n`لندن → دبي`\nأو فقط الوجهة:\n`دبي`",
        "alert_budget_prompt": "✅ المسار: *{route}*\n\nالحد الأقصى للميزانية للشخص؟\nأرسل رقماً مثل `150`",
        "alert_set": "🔔 *تم إعداد التنبيه!*\n\n*{route}* — تحت {sym}{budget} للشخص\n\n🟢 يعمل 24/7. سأخبرك فور ظهور صفقة.",
        "invalid_budget": "يرجى إرسال رقم فقط، مثل `150`",
        "no_hunter": "🎯 *صياد الصفقات*\n\nأرسلني في مهمة. اختر وجهة وميزانية — أفحص كل 15 دقيقة.\n\nلا صيد نشط حالياً.",
        "start_hunt": "🎯 صيد جديد",
        "your_hunts": "🎯 *عمليات الصيد النشطة:*\n\n",
        "hunt_searching": "🔍 جارٍ البحث...", "hunt_found": "✅ صفقة وُجدت!",
        "hunt_dest_prompt": "🎯 *صيد جديد*\n\nأين تريد الذهاب؟\n\nأمثلة:\n• `دبي`\n• `تينيريفي`\n• `في أي مكان دافئ`\n• `في أي مكان`",
        "hunt_budget_prompt": "📍 الوجهة: *{dest}*\n\nالحد الأقصى للميزانية للشخص؟\nأرسل رقماً مثل `200`، أو `0` بلا حد",
        "hunt_started": "🎯 *بدأ الصيد!*\n\n📍 {dest}\n💰 تحت {sym}{budget} للشخص\n⏱ فحص كل 15 دقيقة\n\nسأنبهك فور ظهور صفقة.",
        "hunt_no_limit": "بلا حد",
        "pause_hunt": "⏸ إيقاف", "resume_hunt": "▶️ استئناف", "stop_hunt": "✕ إيقاف نهائي",
        "settings_menu": "⚙️ *الإعدادات*\n\nماذا تريد تغيير؟",
        "lang_btn": "🌐 اللغة", "curr_btn": "💱 العملة", "city_btn": "📍 مدينتك",
        "lang_prompt": "🌐 *اختر لغتك:*",
        "lang_set": "✅ تم تحديث اللغة!",
        "curr_prompt": "💱 *اختر عملتك:*",
        "curr_set": "✅ العملة: {sym}",
        "city_prompt": "📍 *مدينتك*\n\nأرسل مدينتك أو رمز المطار، مثل `دبي`\n\nهذا يحدد نقطة انطلاقك الافتراضية.",
        "city_set": "✅ تم تعيين المدينة: *{city}*",
        "pp": "للشخص", "nights": "ليالٍ", "return_trip": "ذهاب وعودة", "oneway": "ذهاب فقط",
        "best_deal": "أفضل صفقة وُجدت",
        "dep": "ذهاب", "ret": "عودة", "checkin": "الوصول", "checkout": "المغادرة",
    },
    "tr": {
        "welcome": "☀️ *Fairo*'ya hoş geldiniz, {name}!\n\nSeyahat fiyatları, sonunda adil. Uçuşları, otelleri ve paketleri 7/24 tarıyorum.\n\n*Ne yapmak istersiniz?*",
        "search": "🔍 Ara", "hot": "🔥 Sıcak fırsatlar", "alerts": "🔔 Uyarılarım",
        "hunter": "🎯 Avcı", "settings": "⚙️ Ayarlar", "back": "« Geri",
        "help": "☀️ *Fairo nasıl çalışır*\n\n🔍 *Arama* — nereye gitmek istediğinizi ve bütçenizi söyleyin. Uçuşları, otelleri ve paketleri tarıyorum.\n\n🔥 *Sıcak fırsatlar* — şu an en iyi fırsatlar.\n\n🔔 *Uyarılar* — rota kaydedin ve 7/24 takip ediyorum. Anında bildirim.\n\n🎯 *Avcı* — her 15 dakikada sürekli tarama.\n\n⚙️ *Ayarlar* — dil, şehir ve para birimi.\n\n💸 *Tamamen ücretsiz*",
        "search_prompt": "🔍 *Ne arıyorsunuz?*\n\n⚡ *Karışık* uçuşları, otelleri ve paketleri birlikte en büyük tasarrufa göre sıralı gösterir.",
        "flights": "✈️ Uçuşlar", "hotels": "🏨 Oteller", "package": "📦 Paket", "mix": "⚡ Karışık (hepsi)",
        "search_from": "Nereden uçuyorsunuz?\n\nBir şehir veya havalimanı kodu gönderin, örn. `İstanbul` veya `IST`",
        "search_to": "Nereye gitmek istiyorsunuz?\n\nBir şehir veya `Her yer`",
        "search_budget": "Kişi başı maksimum bütçeniz?\n\nBir sayı gönderin örn. `200`, veya `sınırsız`",
        "searching": "🔍 *{query}* için fırsat aranıyor...",
        "no_deals": "Şu an fırsat yok. Uyarı ekleyin, çıktığında haber vereyim!",
        "set_alert_btn": "🔔 Uyarı ekle",
        "hot_scanning": "🔥 Sıcak fırsatlar aranıyor şimdi...",
        "no_hot": "Şu an sıcak fırsat yok — 15 dakika sonra tekrar bakın!",
        "alert_me": "🔔 Uyar", "book_now": "👉 Rezervasyon",
        "no_alerts": "🔔 *Henüz uyarı yok.*\n\nBir rota ekleyin ve 7/24 takip edeyim — anında bildirim.",
        "add_alert": "➕ Uyarı ekle", "add_new_alert": "➕ Yeni uyarı",
        "your_alerts": "🔔 *Uyarılarınız:*\n\n",
        "pause": "⏸ Duraklat", "resume": "▶️ Devam", "delete": "🗑 Sil",
        "alert_deleted": "🗑 Uyarı silindi.",
        "alert_route_prompt": "🔔 *Yeni uyarı*\n\nRotayı gönderin, örn:\n`İstanbul → Dubai`\nveya sadece hedef:\n`Dubai`",
        "alert_budget_prompt": "✅ Rota: *{route}*\n\nKişi başı maksimum bütçe?\nBir sayı gönderin örn. `150`",
        "alert_set": "🔔 *Uyarı oluşturuldu!*\n\n*{route}* — {sym}{budget} pp altı\n\n🟢 7/24 çalışıyor. Bir fırsat çıktığında anında bildiriyorum.",
        "invalid_budget": "Lütfen sadece bir sayı gönderin, örn. `150`",
        "no_hunter": "🎯 *Fırsat Avcısı*\n\nGöreve gönder. Destinasyon ve bütçe seç — her 15 dakikada tarıyorum.\n\nAktif av yok.",
        "start_hunt": "🎯 Yeni av",
        "your_hunts": "🎯 *Aktif avlarınız:*\n\n",
        "hunt_searching": "🔍 Tarıyor...", "hunt_found": "✅ Fırsat bulundu!",
        "hunt_dest_prompt": "🎯 *Yeni av*\n\nNereye gitmek istiyorsunuz?\n\nÖrnekler:\n• `Dubai`\n• `Tenerife`\n• `Her yer sıcak`\n• `Her yer`",
        "hunt_budget_prompt": "📍 Destinasyon: *{dest}*\n\nKişi başı maks. bütçe?\nBir sayı gönderin örn. `200`, veya `0` sınırsız",
        "hunt_started": "🎯 *Av başladı!*\n\n📍 {dest}\n💰 {sym}{budget} pp altı\n⏱ Her 15 dakika taranıyor\n\nBir fırsat çıkar çıkmaz sizi uyarıyorum.",
        "hunt_no_limit": "Sınırsız",
        "pause_hunt": "⏸ Duraklat", "resume_hunt": "▶️ Devam", "stop_hunt": "✕ Durdur",
        "settings_menu": "⚙️ *Ayarlar*\n\nNeyi değiştirmek istersiniz?",
        "lang_btn": "🌐 Dil", "curr_btn": "💱 Para birimi", "city_btn": "📍 Şehriniz",
        "lang_prompt": "🌐 *Dilinizi seçin:*",
        "lang_set": "✅ Dil güncellendi!",
        "curr_prompt": "💱 *Para biriminizi seçin:*",
        "curr_set": "✅ Para birimi: {sym}",
        "city_prompt": "📍 *Şehriniz*\n\nŞehrinizi veya havalimanı kodunu gönderin, örn. `İstanbul`\n\nBu, varsayılan kalkış noktanızı belirler.",
        "city_set": "✅ Şehir belirlendi: *{city}*",
        "pp": "kişi başı", "nights": "gece", "return_trip": "gidiş-dönüş", "oneway": "tek yön",
        "best_deal": "En iyi fırsat bulundu",
        "dep": "Git", "ret": "Dön", "checkin": "Giriş", "checkout": "Çıkış",
    },
    "hi": {
        "welcome": "☀️ *Fairo* में आपका स्वागत है, {name}!\n\nयात्रा की कीमतें, आखिरकार उचित। मैं 24/7 उड़ानें, होटल और पैकेज स्कैन करता हूं।\n\n*आप क्या करना चाहते हैं?*",
        "search": "🔍 खोजें", "hot": "🔥 गर्म डील", "alerts": "🔔 मेरे अलर्ट",
        "hunter": "🎯 हंटर", "settings": "⚙️ सेटिंग्स", "back": "« वापस",
        "help": "☀️ *Fairo कैसे काम करता है*\n\n🔍 *खोज* — बताएं कहाँ जाना है और प्रति व्यक्ति बजट। उड़ानें, होटल और पैकेज स्कैन करता हूं।\n\n🔥 *गर्म डील* — अभी की सबसे अच्छी डील।\n\n🔔 *अलर्ट* — रूट सेव करें और 24/7 देखता रहूंगा। तुरंत अलर्ट।\n\n🎯 *हंटर* — हर 15 मिनट में स्कैन।\n\n⚙️ *सेटिंग्स* — भाषा, शहर और मुद्रा।\n\n💸 *100% मुफ़्त*",
        "search_prompt": "🔍 *आप क्या ढूंढ रहे हैं?*\n\n⚡ *मिश्रित* उड़ानें, होटल और पैकेज एक साथ सबसे बड़ी बचत के क्रम में दिखाता है।",
        "flights": "✈️ उड़ानें", "hotels": "🏨 होटल", "package": "📦 पैकेज", "mix": "⚡ मिश्रित (सब)",
        "search_from": "आप कहाँ से उड़ रहे हैं?\n\nशहर या एयरपोर्ट कोड भेजें, जैसे `दिल्ली` या `DEL`",
        "search_to": "आप कहाँ जाना चाहते हैं?\n\nशहर या `कहीं भी`",
        "search_budget": "प्रति व्यक्ति अधिकतम बजट?\n\nसंख्या भेजें जैसे `200`, या `कोई सीमा नहीं`",
        "searching": "🔍 *{query}* के लिए डील खोज रहा हूं...",
        "no_deals": "अभी कोई डील नहीं। अलर्ट सेट करें और जब मिले बताऊंगा!",
        "set_alert_btn": "🔔 अलर्ट सेट करें",
        "hot_scanning": "🔥 अभी गर्म डील खोज रहा हूं...",
        "no_hot": "अभी कोई गर्म डील नहीं — 15 मिनट बाद देखें!",
        "alert_me": "🔔 अलर्ट करें", "book_now": "👉 अभी बुक करें",
        "no_alerts": "🔔 *अभी कोई अलर्ट नहीं।*\n\nरूट जोड़ें और 24/7 देखता रहूंगा — तुरंत अलर्ट।",
        "add_alert": "➕ अलर्ट जोड़ें", "add_new_alert": "➕ नया अलर्ट",
        "your_alerts": "🔔 *आपके अलर्ट:*\n\n",
        "pause": "⏸ रोकें", "resume": "▶️ जारी रखें", "delete": "🗑 हटाएं",
        "alert_deleted": "🗑 अलर्ट हटा दिया।",
        "alert_route_prompt": "🔔 *नया अलर्ट*\n\nरूट भेजें, जैसे:\n`दिल्ली → दुबई`\nया केवल गंतव्य:\n`दुबई`",
        "alert_budget_prompt": "✅ रूट: *{route}*\n\nप्रति व्यक्ति अधिकतम बजट?\nसंख्या भेजें जैसे `150`",
        "alert_set": "🔔 *अलर्ट सेट हो गया!*\n\n*{route}* — {sym}{budget} से कम\n\n🟢 24/7 चल रहा है। डील आते ही बताऊंगा।",
        "invalid_budget": "कृपया सिर्फ संख्या भेजें, जैसे `150`",
        "no_hunter": "🎯 *डील हंटर*\n\nमुझे मिशन पर भेजें। गंतव्य और बजट चुनें — हर 15 मिनट में स्कैन करता हूं।\n\nकोई सक्रिय हंट नहीं।",
        "start_hunt": "🎯 नई खोज",
        "your_hunts": "🎯 *आपकी सक्रिय खोजें:*\n\n",
        "hunt_searching": "🔍 स्कैन हो रहा है...", "hunt_found": "✅ डील मिली!",
        "hunt_dest_prompt": "🎯 *नई खोज*\n\nआप कहाँ जाना चाहते हैं?\n\nउदाहरण:\n• `दुबई`\n• `थाईलैंड`\n• `कहीं भी गर्म`\n• `कहीं भी`",
        "hunt_budget_prompt": "📍 गंतव्य: *{dest}*\n\nप्रति व्यक्ति अधिकतम बजट?\nसंख्या भेजें जैसे `200`, या `0` कोई सीमा नहीं",
        "hunt_started": "🎯 *खोज शुरू हो गई!*\n\n📍 {dest}\n💰 {sym}{budget} से कम\n⏱ हर 15 मिनट स्कैन\n\nडील मिलते ही अलर्ट करूंगा।",
        "hunt_no_limit": "कोई सीमा नहीं",
        "pause_hunt": "⏸ रोकें", "resume_hunt": "▶️ जारी रखें", "stop_hunt": "✕ बंद करें",
        "settings_menu": "⚙️ *सेटिंग्स*\n\nआप क्या बदलना चाहते हैं?",
        "lang_btn": "🌐 भाषा", "curr_btn": "💱 मुद्रा", "city_btn": "📍 आपका शहर",
        "lang_prompt": "🌐 *अपनी भाषा चुनें:*",
        "lang_set": "✅ भाषा अपडेट हो गई!",
        "curr_prompt": "💱 *अपनी मुद्रा चुनें:*",
        "curr_set": "✅ मुद्रा: {sym}",
        "city_prompt": "📍 *आपका शहर*\n\nअपना शहर या एयरपोर्ट कोड भेजें, जैसे `दिल्ली`\n\nयह आपका डिफ़ॉल्ट प्रस्थान बिंदु सेट करता है।",
        "city_set": "✅ शहर सेट: *{city}*",
        "pp": "प्रति व्यक्ति", "nights": "रातें", "return_trip": "आना-जाना", "oneway": "केवल जाना",
        "best_deal": "सबसे अच्छी डील मिली",
        "dep": "जाना", "ret": "वापसी", "checkin": "चेक इन", "checkout": "चेक आउट",
    },
    "it": {
        "welcome": "☀️ Benvenuto su *Fairo*, {name}!\n\nPrezzi di viaggio finalmente equi. Scansiono voli, hotel e pacchetti 24/7.\n\n*Cosa vuoi fare?*",
        "search": "🔍 Cerca", "hot": "🔥 Offerte calde", "alerts": "🔔 I miei avvisi",
        "hunter": "🎯 Cacciatore", "settings": "⚙️ Impostazioni", "back": "« Indietro",
        "help": "☀️ *Come funziona Fairo*\n\n🔍 *Cerca* — dimmi dove vuoi andare e il tuo budget. Scansiono voli, hotel e pacchetti.\n\n🔥 *Offerte calde* — le migliori offerte in diretta ora.\n\n🔔 *Avvisi* — salva un percorso e lo tengo sotto controllo 24/7. Avviso istantaneo.\n\n🎯 *Cacciatore* — scansione continua ogni 15 minuti.\n\n⚙️ *Impostazioni* — lingua, città e valuta.\n\n💸 *100% gratuito*",
        "search_prompt": "🔍 *Cosa stai cercando?*\n\n⚡ *Mix* mostra voli, hotel e pacchetti insieme ordinati per risparmio maggiore.",
        "flights": "✈️ Voli", "hotels": "🏨 Hotel", "package": "📦 Pacchetto", "mix": "⚡ Mix (tutto)",
        "search_from": "Da dove parti?\n\nInvia una città o codice aeroporto, es. `Roma` o `FCO`",
        "search_to": "Dove vuoi andare?\n\nInvia una città o `Ovunque`",
        "search_budget": "Il tuo budget massimo per persona?\n\nInvia un numero es. `200`, o `illimitato`",
        "searching": "🔍 Cerco offerte per *{query}*...",
        "no_deals": "Nessuna offerta adesso. Crea un avviso e ti avverto quando appare una!",
        "set_alert_btn": "🔔 Crea avviso",
        "hot_scanning": "🔥 Cerco le migliori offerte ora...",
        "no_hot": "Nessuna offerta calda — riprova tra 15 minuti!",
        "alert_me": "🔔 Avvisami", "book_now": "👉 Prenota",
        "no_alerts": "🔔 *Nessun avviso.*\n\nAggiungi un percorso e lo tengo sotto controllo 24/7 — avviso istantaneo.",
        "add_alert": "➕ Aggiungi avviso", "add_new_alert": "➕ Nuovo avviso",
        "your_alerts": "🔔 *I tuoi avvisi:*\n\n",
        "pause": "⏸ Pausa", "resume": "▶️ Riprendi", "delete": "🗑 Elimina",
        "alert_deleted": "🗑 Avviso eliminato.",
        "alert_route_prompt": "🔔 *Nuovo avviso*\n\nInvia il percorso, es:\n`Roma → Dubai`\noppure solo la destinazione:\n`Dubai`",
        "alert_budget_prompt": "✅ Percorso: *{route}*\n\nBudget max per persona?\nInvia un numero es. `150`",
        "alert_set": "🔔 *Avviso creato!*\n\n*{route}* — sotto {sym}{budget} pp\n\n🟢 Attivo 24/7. Ti avverto appena appare un'offerta.",
        "invalid_budget": "Invia solo un numero, es. `150`",
        "no_hunter": "🎯 *Cacciatore di Offerte*\n\nMandami in missione. Scegli destinazione e budget — scansiono ogni 15 minuti.\n\nNessuna caccia attiva.",
        "start_hunt": "🎯 Nuova caccia",
        "your_hunts": "🎯 *Le tue cacce attive:*\n\n",
        "hunt_searching": "🔍 Scansione...", "hunt_found": "✅ Offerta trovata!",
        "hunt_dest_prompt": "🎯 *Nuova caccia*\n\nDove vuoi andare?\n\nEsempi:\n• `Dubai`\n• `Tenerife`\n• `Ovunque caldo`\n• `Ovunque`",
        "hunt_budget_prompt": "📍 Destinazione: *{dest}*\n\nBudget max per persona?\nInvia un numero es. `200`, o `0` illimitato",
        "hunt_started": "🎯 *Caccia avviata!*\n\n📍 {dest}\n💰 Sotto {sym}{budget} pp\n⏱ Scansione ogni 15 minuti\n\nTi avverto appena appare un'offerta.",
        "hunt_no_limit": "Illimitato",
        "pause_hunt": "⏸ Pausa", "resume_hunt": "▶️ Riprendi", "stop_hunt": "✕ Ferma",
        "settings_menu": "⚙️ *Impostazioni*\n\nCosa vuoi modificare?",
        "lang_btn": "🌐 Lingua", "curr_btn": "💱 Valuta", "city_btn": "📍 Città di partenza",
        "lang_prompt": "🌐 *Scegli la tua lingua:*",
        "lang_set": "✅ Lingua aggiornata!",
        "curr_prompt": "💱 *Scegli la tua valuta:*",
        "curr_set": "✅ Valuta: {sym}",
        "city_prompt": "📍 *Città di partenza*\n\nInvia la tua città o aeroporto, es. `Roma`\n\nQuesto imposta il tuo punto di partenza predefinito.",
        "city_set": "✅ Città impostata: *{city}*",
        "pp": "pp", "nights": "notti", "return_trip": "andata e ritorno", "oneway": "solo andata",
        "best_deal": "Miglior offerta trovata",
        "dep": "Part", "ret": "Rit", "checkin": "Check-in", "checkout": "Check-out",
    },
    "pt": {
        "welcome": "☀️ Bem-vindo ao *Fairo*, {name}!\n\nPreços de viagem finalmente justos. Pesquiso voos, hotéis e pacotes 24/7.\n\n*O que quer fazer?*",
        "search": "🔍 Pesquisar", "hot": "🔥 Ofertas quentes", "alerts": "🔔 Os meus alertas",
        "hunter": "🎯 Caçador", "settings": "⚙️ Preferências", "back": "« Voltar",
        "help": "☀️ *Como funciona o Fairo*\n\n🔍 *Pesquisa* — diga-me para onde quer ir e o orçamento. Pesquiso voos, hotéis e pacotes.\n\n🔥 *Ofertas quentes* — as melhores ofertas ao vivo agora.\n\n🔔 *Alertas* — guarde uma rota e monitorizo 24/7. Alerta instantâneo.\n\n🎯 *Caçador* — pesquisa contínua a cada 15 minutos.\n\n⚙️ *Preferências* — língua, cidade e moeda.\n\n💸 *100% gratuito*",
        "search_prompt": "🔍 *O que procura?*\n\n⚡ *Mix* mostra voos, hotéis e pacotes juntos ordenados por maior poupança.",
        "flights": "✈️ Voos", "hotels": "🏨 Hotéis", "package": "📦 Pacote", "mix": "⚡ Mix (tudo)",
        "search_from": "De onde parte?\n\nEnvie uma cidade ou código de aeroporto, ex. `Lisboa` ou `LIS`",
        "search_to": "Para onde quer ir?\n\nEnvie uma cidade ou `Qualquer lugar`",
        "search_budget": "Orçamento máximo por pessoa?\n\nEnvie um número ex. `200`, ou `sem limite`",
        "searching": "🔍 A pesquisar ofertas para *{query}*...",
        "no_deals": "Sem ofertas agora. Crie um alerta e aviso quando aparecer uma!",
        "set_alert_btn": "🔔 Criar alerta",
        "hot_scanning": "🔥 À procura das melhores ofertas agora...",
        "no_hot": "Sem ofertas quentes — volte em 15 minutos!",
        "alert_me": "🔔 Alertar", "book_now": "👉 Reservar",
        "no_alerts": "🔔 *Sem alertas.*\n\nAdicione uma rota e monitorizo 24/7 — alerta instantâneo.",
        "add_alert": "➕ Adicionar alerta", "add_new_alert": "➕ Novo alerta",
        "your_alerts": "🔔 *Os seus alertas:*\n\n",
        "pause": "⏸ Pausar", "resume": "▶️ Retomar", "delete": "🗑 Apagar",
        "alert_deleted": "🗑 Alerta apagado.",
        "alert_route_prompt": "🔔 *Novo alerta*\n\nEnvie a rota, ex:\n`Lisboa → Dubai`\nou apenas o destino:\n`Dubai`",
        "alert_budget_prompt": "✅ Rota: *{route}*\n\nOrçamento máx por pessoa?\nEnvie um número ex. `150`",
        "alert_set": "🔔 *Alerta criado!*\n\n*{route}* — abaixo de {sym}{budget} pp\n\n🟢 Ativo 24/7. Aviso assim que aparecer uma oferta.",
        "invalid_budget": "Envie apenas um número, ex. `150`",
        "no_hunter": "🎯 *Caçador de Ofertas*\n\nEnvie-me numa missão. Escolha destino e orçamento — pesquiso a cada 15 minutos.\n\nSem caçadas ativas.",
        "start_hunt": "🎯 Nova caçada",
        "your_hunts": "🎯 *As suas caçadas ativas:*\n\n",
        "hunt_searching": "🔍 A pesquisar...", "hunt_found": "✅ Oferta encontrada!",
        "hunt_dest_prompt": "🎯 *Nova caçada*\n\nPara onde quer ir?\n\nExemplos:\n• `Dubai`\n• `Tenerife`\n• `Qualquer lugar quente`\n• `Qualquer lugar`",
        "hunt_budget_prompt": "📍 Destino: *{dest}*\n\nOrçamento máx por pessoa?\nEnvie um número ex. `200`, ou `0` sem limite",
        "hunt_started": "🎯 *Caçada iniciada!*\n\n📍 {dest}\n💰 Abaixo de {sym}{budget} pp\n⏱ Pesquisa a cada 15 minutos\n\nAviso assim que aparecer uma oferta.",
        "hunt_no_limit": "Sem limite",
        "pause_hunt": "⏸ Pausar", "resume_hunt": "▶️ Retomar", "stop_hunt": "✕ Parar",
        "settings_menu": "⚙️ *Preferências*\n\nO que quer alterar?",
        "lang_btn": "🌐 Língua", "curr_btn": "💱 Moeda", "city_btn": "📍 Cidade de origem",
        "lang_prompt": "🌐 *Escolha o seu idioma:*",
        "lang_set": "✅ Idioma atualizado!",
        "curr_prompt": "💱 *Escolha a sua moeda:*",
        "curr_set": "✅ Moeda: {sym}",
        "city_prompt": "📍 *Cidade de origem*\n\nEnvie a sua cidade ou aeroporto, ex. `Lisboa`\n\nIsto define o seu ponto de partida por defeito.",
        "city_set": "✅ Cidade definida: *{city}*",
        "pp": "pp", "nights": "noites", "return_trip": "ida e volta", "oneway": "só ida",
        "best_deal": "Melhor oferta encontrada",
        "dep": "Part", "ret": "Reg", "checkin": "Check-in", "checkout": "Check-out",
    },
    "zh": {
        "welcome": "☀️ 欢迎使用 *Fairo*，{name}！\n\n旅行价格，终于公平。我24/7扫描航班、酒店和套餐。\n\n*您想做什么？*",
        "search": "🔍 搜索", "hot": "🔥 热门优惠", "alerts": "🔔 我的提醒",
        "hunter": "🎯 猎手", "settings": "⚙️ 设置", "back": "« 返回",
        "help": "☀️ *Fairo如何工作*\n\n🔍 *搜索* — 告诉我您想去哪里和每人预算。我扫描航班、酒店和套餐。\n\n🔥 *热门优惠* — 当前最佳实时优惠。\n\n🔔 *提醒* — 保存路线，我24/7监控。即时提醒。\n\n🎯 *猎手* — 每15分钟持续扫描。\n\n⚙️ *设置* — 语言、城市和货币。\n\n💸 *完全免费*",
        "search_prompt": "🔍 *您在寻找什么？*\n\n⚡ *混合* 按最大节省排序一起显示航班、酒店和套餐。",
        "flights": "✈️ 航班", "hotels": "🏨 酒店", "package": "📦 套餐", "mix": "⚡ 混合（全部）",
        "search_from": "您从哪里出发？\n\n发送城市或机场代码，例如 `北京` 或 `PEK`",
        "search_to": "您想去哪里？\n\n发送城市或 `任何地方`",
        "search_budget": "每人最高预算？\n\n发送数字例如 `200`，或 `无限制`",
        "searching": "🔍 正在搜索 *{query}* 的优惠...",
        "no_deals": "暂无优惠。设置提醒，有优惠时我会通知您！",
        "set_alert_btn": "🔔 设置提醒",
        "hot_scanning": "🔥 正在搜索热门优惠...",
        "no_hot": "暂无热门优惠 — 15分钟后再查看！",
        "alert_me": "🔔 提醒我", "book_now": "👉 立即预订",
        "no_alerts": "🔔 *暂无提醒。*\n\n添加路线，我24/7监控 — 即时提醒。",
        "add_alert": "➕ 添加提醒", "add_new_alert": "➕ 新提醒",
        "your_alerts": "🔔 *您的提醒：*\n\n",
        "pause": "⏸ 暂停", "resume": "▶️ 恢复", "delete": "🗑 删除",
        "alert_deleted": "🗑 提醒已删除。",
        "alert_route_prompt": "🔔 *新提醒*\n\n发送路线，例如：\n`北京 → 迪拜`\n或仅目的地：\n`迪拜`",
        "alert_budget_prompt": "✅ 路线：*{route}*\n\n每人最高预算？\n发送数字例如 `150`",
        "alert_set": "🔔 *提醒已设置！*\n\n*{route}* — 低于 {sym}{budget}/人\n\n🟢 24/7运行。有优惠立即通知您。",
        "invalid_budget": "请只发送数字，例如 `150`",
        "no_hunter": "🎯 *优惠猎手*\n\n让我执行任务。选择目的地和预算 — 每15分钟扫描一次。\n\n暂无活跃搜猎。",
        "start_hunt": "🎯 开始搜猎",
        "your_hunts": "🎯 *您的活跃搜猎：*\n\n",
        "hunt_searching": "🔍 扫描中...", "hunt_found": "✅ 找到优惠！",
        "hunt_dest_prompt": "🎯 *新搜猎*\n\n您想去哪里？\n\n示例：\n• `迪拜`\n• `泰国`\n• `任何温暖的地方`\n• `任何地方`",
        "hunt_budget_prompt": "📍 目的地：*{dest}*\n\n每人最高预算？\n发送数字例如 `200`，或 `0` 无限制",
        "hunt_started": "🎯 *搜猎已开始！*\n\n📍 {dest}\n💰 低于 {sym}{budget}/人\n⏱ 每15分钟扫描\n\n找到优惠立即通知您。",
        "hunt_no_limit": "无限制",
        "pause_hunt": "⏸ 暂停", "resume_hunt": "▶️ 恢复", "stop_hunt": "✕ 停止",
        "settings_menu": "⚙️ *设置*\n\n您想更改什么？",
        "lang_btn": "🌐 语言", "curr_btn": "💱 货币", "city_btn": "📍 出发城市",
        "lang_prompt": "🌐 *选择您的语言：*",
        "lang_set": "✅ 语言已更新！",
        "curr_prompt": "💱 *选择您的货币：*",
        "curr_set": "✅ 货币：{sym}",
        "city_prompt": "📍 *出发城市*\n\n发送您的城市或机场代码，例如 `北京`\n\n这将设置您的默认出发地。",
        "city_set": "✅ 城市已设置：*{city}*",
        "pp": "每人", "nights": "晚", "return_trip": "往返", "oneway": "单程",
        "best_deal": "找到最佳优惠",
        "dep": "去", "ret": "回", "checkin": "入住", "checkout": "退房",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    text = T.get(lang, T["en"]).get(key) or T["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


# ── KEYBOARDS ─────────────────────────────────────────────────────────────────

def main_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "search"), callback_data="search"),
         InlineKeyboardButton(t(lang, "hot"), callback_data="hot")],
        [InlineKeyboardButton(t(lang, "alerts"), callback_data="alerts"),
         InlineKeyboardButton(t(lang, "hunter"), callback_data="hunter")],
        [InlineKeyboardButton(t(lang, "settings"), callback_data="settings")],
    ])


def search_type_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "flights"), callback_data="stype_flights"),
         InlineKeyboardButton(t(lang, "hotels"), callback_data="stype_hotels")],
        [InlineKeyboardButton(t(lang, "package"), callback_data="stype_package"),
         InlineKeyboardButton(t(lang, "mix"), callback_data="stype_mix")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
    ])


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
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


def curr_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 GBP £", callback_data="cur_GBP_£"),
         InlineKeyboardButton("🇺🇸 USD $", callback_data="cur_USD_$")],
        [InlineKeyboardButton("🇪🇺 EUR €", callback_data="cur_EUR_€"),
         InlineKeyboardButton("🇹🇷 TRY ₺", callback_data="cur_TRY_₺")],
        [InlineKeyboardButton("🇮🇳 INR ₹", callback_data="cur_INR_₹"),
         InlineKeyboardButton("🇦🇪 AED د.إ", callback_data="cur_AED_د.إ")],
        [InlineKeyboardButton("🇦🇺 AUD A$", callback_data="cur_AUD_A$"),
         InlineKeyboardButton("🇨🇦 CAD C$", callback_data="cur_CAD_C$")],
    ])


def settings_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "lang_btn"), callback_data="set_lang"),
         InlineKeyboardButton(t(lang, "curr_btn"), callback_data="set_curr")],
        [InlineKeyboardButton(t(lang, "city_btn"), callback_data="set_city")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
    ])


def deal_kb(lang: str, link: str, route_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang, "book_now"), url=link),
        InlineKeyboardButton(t(lang, "alert_me"), callback_data=f"quickalert_{route_key}"),
    ]])


def alerts_kb(lang: str, alerts: list) -> InlineKeyboardMarkup:
    rows = []
    for alert in alerts:
        sym = alert.get("currency_sym", "£")
        label = t(lang, "pause") if alert["active"] else t(lang, "resume")
        rows.append([
            InlineKeyboardButton(
                f"{'🟢' if alert['active'] else '⚫'} {alert['route'][:25]}",
                callback_data=f"noop"
            ),
        ])
        rows.append([
            InlineKeyboardButton(label, callback_data=f"toggle_alert_{alert['id']}"),
            InlineKeyboardButton(t(lang, "delete"), callback_data=f"del_alert_{alert['id']}"),
        ])
    rows.append([InlineKeyboardButton(t(lang, "add_new_alert"), callback_data="add_alert")])
    rows.append([InlineKeyboardButton(t(lang, "back"), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def hunter_kb(lang: str, hunts: list) -> InlineKeyboardMarkup:
    rows = []
    for hunt in hunts:
        status = t(lang, "hunt_found") if hunt["status"] == "found" else t(lang, "hunt_searching")
        rows.append([InlineKeyboardButton(
            f"{status} {hunt['destination'][:20]}",
            callback_data="noop"
        )])
        is_paused = hunt["status"] == "paused"
        pause_label = t(lang, "resume_hunt") if is_paused else t(lang, "pause_hunt")
        rows.append([
            InlineKeyboardButton(pause_label, callback_data=f"toggle_hunt_{hunt['id']}"),
            InlineKeyboardButton(t(lang, "stop_hunt"), callback_data=f"del_hunt_{hunt['id']}"),
        ])
    rows.append([InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")])
    rows.append([InlineKeyboardButton(t(lang, "back"), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


# ── DEAL FORMATTER ────────────────────────────────────────────────────────────

def deal_msg(deal: dict, sym: str, lang: str) -> str:
    save_pct = deal.get("saving_pct", 0)
    urgency = "🔴" if deal.get("seats_left", 99) < 5 else "🟡" if deal.get("seats_left", 99) < 15 else "🟢"
    if deal["type"] == "flight":
        return (
            f"✈️ *{deal['route']}*\n"
            f"🏷 {deal['deal_label']}  •  {urgency}\n"
            f"📅 {t(lang,'dep')}: {deal['dep_date']}  →  {t(lang,'ret')}: {deal['ret_date']}\n"
            f"✈️ {deal.get('airline','')}  •  {deal.get('duration','')}\n\n"
            f"💰 *{sym}{deal['price_pp']} {t(lang,'pp')}*  ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*"
        )
    elif deal["type"] == "hotel":
        stars = "⭐" * min(int(deal.get("stars", 4)), 5)
        return (
            f"🏨 *{deal.get('name', deal['route'])}*\n"
            f"🏷 {deal['deal_label']}  •  {stars}\n"
            f"📅 {t(lang,'checkin')}: {deal['dep_date']}  →  {t(lang,'checkout')}: {deal['ret_date']}\n"
            f"🌙 {deal.get('nights', 7)} {t(lang,'nights')}\n\n"
            f"💰 *{sym}{deal['price_pp']} {t(lang,'pp')}*  ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*"
        )
    else:
        return (
            f"📦 *{deal['route']}* — Package\n"
            f"🏷 {deal['deal_label']}\n"
            f"📅 {deal['dep_date']}  →  {deal['ret_date']}  •  {deal.get('nights', 7)} {t(lang,'nights')}\n\n"
            f"💰 *{sym}{deal['price_pp']} {t(lang,'pp')}*  ~~{sym}{deal['was_pp']}~~  •  *−{save_pct}%*"
        )


# ── HELPERS ───────────────────────────────────────────────────────────────────

async def get_lang(user_id: int) -> str:
    try:
        return await db.get_user_lang(user_id)
    except Exception:
        return "en"


async def get_prefs(user_id: int) -> dict:
    try:
        return await db.get_user_prefs(user_id)
    except Exception:
        return {"currency": "GBP", "currency_sym": "£", "lang": "en", "budget_pp": 9999}


async def send_deals(reply_fn, deals: list, sym: str, lang: str):
    for deal in deals[:5]:
        try:
            await reply_fn(
                deal_msg(deal, sym, lang),
                parse_mode="Markdown",
                reply_markup=deal_kb(lang, deal["affiliate_link"], deal["route_key"]),
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Send deal error: {e}")


async def show_main(send_fn, lang: str, name: str):
    await send_fn(
        t(lang, "welcome", name=name),
        parse_mode="Markdown",
        reply_markup=main_kb(lang)
    )


# ── COMMANDS ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        await db.upsert_user(user.id, user.username or "", user.language_code or "en")
    except Exception as e:
        logger.error(f"upsert_user error: {e}")
    lang = await get_lang(user.id)
    await update.message.reply_text(
        t(lang, "welcome", name=user.first_name),
        parse_mode="Markdown",
        reply_markup=main_kb(lang)
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "help"), parse_mode="Markdown", reply_markup=main_kb(lang)
    )


async def cmd_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await get_lang(user_id)
    prefs = await get_prefs(user_id)
    sym = prefs.get("currency_sym", "£")
    msg = await update.message.reply_text(t(lang, "hot_scanning"))
    try:
        deals = await scanner.get_hot_deals(limit=5)
        await msg.delete()
        if deals:
            await send_deals(update.message.reply_text, deals, sym, lang)
        else:
            await update.message.reply_text(t(lang, "no_hot"))
    except Exception as e:
        logger.error(f"cmd_hot error: {e}")
        await msg.edit_text(t(lang, "no_hot"))


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "search_prompt"), parse_mode="Markdown",
        reply_markup=search_type_kb(lang)
    )


async def cmd_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await get_lang(user_id)
    try:
        alerts = await db.get_user_alerts(user_id)
    except Exception:
        alerts = []
    if not alerts:
        await update.message.reply_text(
            t(lang, "no_alerts"), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "add_alert"), callback_data="add_alert")],
                [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
            ])
        )
        return
    text = t(lang, "your_alerts")
    for alert in alerts:
        sym = alert.get("currency_sym", "£")
        status = "🟢" if alert["active"] else "⚫"
        text += f"{status} *{alert['route']}* — {sym}{int(alert['budget_pp'])} {t(lang,'pp')}\n"
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=alerts_kb(lang, alerts)
    )


async def cmd_hunter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await get_lang(user_id)
    prefs = await get_prefs(user_id)
    sym = prefs.get("currency_sym", "£")
    try:
        hunts = await db.get_user_hunts(user_id)
    except Exception:
        hunts = []
    if not hunts:
        await update.message.reply_text(
            t(lang, "no_hunter"), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")],
                [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
            ])
        )
        return
    text = t(lang, "your_hunts")
    for hunt in hunts:
        status = t(lang, "hunt_found") if hunt["status"] == "found" else t(lang, "hunt_searching")
        budget_str = f"{sym}{int(hunt['budget_pp'])}" if hunt.get("budget_pp") else t(lang, "hunt_no_limit")
        text += f"{status} *{hunt['destination']}* — {budget_str} {t(lang,'pp')}\n"
        if hunt.get("best_deal"):
            bd = hunt["best_deal"]
            text += f"   └ {t(lang,'best_deal')}: {sym}{bd.get('price_pp','?')} — {bd.get('route','')}\n"
        text += "\n"
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=hunter_kb(lang, hunts)
    )


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "settings_menu"), parse_mode="Markdown",
        reply_markup=settings_kb(lang)
    )


# ── CALLBACK HANDLER ─────────────────────────────────────────────────────────

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    lang = await get_lang(user_id)
    prefs = await get_prefs(user_id)
    sym = prefs.get("currency_sym", "£")

    if data == "noop":
        return

    # ── MAIN ──
    elif data == "back_main":
        await query.message.reply_text(
            t(lang, "welcome", name=query.from_user.first_name),
            parse_mode="Markdown", reply_markup=main_kb(lang)
        )

    # ── HOT DEALS ──
    elif data == "hot":
        msg = await query.message.reply_text(t(lang, "hot_scanning"))
        try:
            deals = await scanner.get_hot_deals(limit=5)
            await msg.delete()
            if deals:
                await send_deals(query.message.reply_text, deals, sym, lang)
            else:
                await query.message.reply_text(t(lang, "no_hot"))
        except Exception as e:
            logger.error(f"hot button error: {e}")
            await msg.edit_text(t(lang, "no_hot"))

    # ── SEARCH ──
    elif data == "search":
        await query.message.reply_text(
            t(lang, "search_prompt"), parse_mode="Markdown",
            reply_markup=search_type_kb(lang)
        )

    elif data.startswith("stype_"):
        stype = data.replace("stype_", "")
        context.user_data["search_type"] = stype
        context.user_data["state"] = "awaiting_search_from"
        await query.message.reply_text(t(lang, "search_from"), parse_mode="Markdown")

    # ── ALERTS ──
    elif data == "alerts":
        try:
            alerts = await db.get_user_alerts(user_id)
        except Exception:
            alerts = []
        if not alerts:
            await query.message.reply_text(
                t(lang, "no_alerts"), parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(lang, "add_alert"), callback_data="add_alert")],
                    [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
                ])
            )
        else:
            text = t(lang, "your_alerts")
            for alert in alerts:
                s = alert.get("currency_sym", "£")
                status = "🟢" if alert["active"] else "⚫"
                text += f"{status} *{alert['route']}* — {s}{int(alert['budget_pp'])} {t(lang,'pp')}\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=alerts_kb(lang, alerts)
            )

    elif data == "add_alert":
        context.user_data["state"] = "awaiting_alert_route"
        await query.message.reply_text(t(lang, "alert_route_prompt"), parse_mode="Markdown")

    elif data.startswith("quickalert_"):
        route_key = data.replace("quickalert_", "")
        route = route_key.replace("-", " → ")
        context.user_data["alert_route"] = route
        context.user_data["state"] = "awaiting_alert_budget"
        await query.message.reply_text(
            t(lang, "alert_budget_prompt", route=route), parse_mode="Markdown"
        )

    elif data.startswith("toggle_alert_"):
        alert_id = int(data.replace("toggle_alert_", ""))
        try:
            await db.toggle_alert(user_id, alert_id)
        except Exception as e:
            logger.error(f"toggle_alert error: {e}")
        try:
            alerts = await db.get_user_alerts(user_id)
            text = t(lang, "your_alerts")
            for alert in alerts:
                s = alert.get("currency_sym", "£")
                status = "🟢" if alert["active"] else "⚫"
                text += f"{status} *{alert['route']}* — {s}{int(alert['budget_pp'])} {t(lang,'pp')}\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=alerts_kb(lang, alerts)
            )
        except Exception as e:
            logger.error(f"refresh alerts error: {e}")

    elif data.startswith("del_alert_"):
        alert_id = int(data.replace("del_alert_", ""))
        try:
            await db.delete_alert(user_id, alert_id)
        except Exception as e:
            logger.error(f"del_alert error: {e}")
        await query.message.reply_text(t(lang, "alert_deleted"))

    # ── HUNTER ──
    elif data == "hunter":
        try:
            hunts = await db.get_user_hunts(user_id)
        except Exception:
            hunts = []
        if not hunts:
            await query.message.reply_text(
                t(lang, "no_hunter"), parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")],
                    [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
                ])
            )
        else:
            text = t(lang, "your_hunts")
            for hunt in hunts:
                status = t(lang, "hunt_found") if hunt["status"] == "found" else t(lang, "hunt_searching")
                budget_str = f"{sym}{int(hunt['budget_pp'])}" if hunt.get("budget_pp") else t(lang, "hunt_no_limit")
                text += f"{status} *{hunt['destination']}* — {budget_str} {t(lang,'pp')}\n"
                if hunt.get("best_deal"):
                    bd = hunt["best_deal"]
                    text += f"   └ {t(lang,'best_deal')}: {sym}{bd.get('price_pp','?')} — {bd.get('route','')}\n"
                text += "\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=hunter_kb(lang, hunts)
            )

    elif data == "new_hunt":
        context.user_data["state"] = "awaiting_hunt_dest"
        await query.message.reply_text(t(lang, "hunt_dest_prompt"), parse_mode="Markdown")

    elif data.startswith("toggle_hunt_"):
        hunt_id = int(data.replace("toggle_hunt_", ""))
        try:
            await db.toggle_hunt(user_id, hunt_id)
        except Exception as e:
            logger.error(f"toggle_hunt error: {e}")
        try:
            hunts = await db.get_user_hunts(user_id)
            await query.message.reply_text(
                t(lang, "your_hunts"), parse_mode="Markdown",
                reply_markup=hunter_kb(lang, hunts)
            )
        except Exception as e:
            logger.error(f"refresh hunts error: {e}")

    elif data.startswith("del_hunt_"):
        hunt_id = int(data.replace("del_hunt_", ""))
        try:
            await db.delete_hunt(user_id, hunt_id)
        except Exception as e:
            logger.error(f"del_hunt error: {e}")
        await query.message.reply_text(t(lang, "no_hunter"), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")],
                [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
            ])
        )

    # ── SETTINGS ──
    elif data == "settings":
        await query.message.reply_text(
            t(lang, "settings_menu"), parse_mode="Markdown",
            reply_markup=settings_kb(lang)
        )

    elif data == "set_lang":
        await query.message.reply_text(t(lang, "lang_prompt"), reply_markup=lang_kb())

    elif data.startswith("lang_"):
        new_lang = data.replace("lang_", "")
        try:
            await db.set_user_lang(user_id, new_lang)
        except Exception as e:
            logger.error(f"set_user_lang error: {e}")
        await query.message.reply_text(
            t(new_lang, "lang_set"), reply_markup=main_kb(new_lang)
        )

    elif data == "set_curr":
        await query.message.reply_text(t(lang, "curr_prompt"), reply_markup=curr_kb())

    elif data.startswith("cur_"):
        parts = data.split("_", 2)
        if len(parts) == 3:
            curr_code, curr_sym = parts[1], parts[2]
            try:
                await db.set_user_currency(user_id, curr_code, curr_sym)
            except Exception as e:
                logger.error(f"set_user_currency error: {e}")
            await query.message.reply_text(
                t(lang, "curr_set", sym=curr_sym),
                reply_markup=main_kb(lang)
            )

    elif data == "set_city":
        context.user_data["state"] = "awaiting_city"
        await query.message.reply_text(t(lang, "city_prompt"), parse_mode="Markdown")


# ── MESSAGE HANDLER ───────────────────────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = context.user_data.get("state")
    lang = await get_lang(user_id)
    prefs = await get_prefs(user_id)
    sym = prefs.get("currency_sym", "£")

    # ── SEARCH FLOW ──
    if state == "awaiting_search_from":
        context.user_data["search_from"] = text
        context.user_data["state"] = "awaiting_search_to"
        await update.message.reply_text(t(lang, "search_to"), parse_mode="Markdown")

    elif state == "awaiting_search_to":
        context.user_data["search_to"] = text
        context.user_data["state"] = "awaiting_search_budget"
        await update.message.reply_text(t(lang, "search_budget"), parse_mode="Markdown")

    elif state == "awaiting_search_budget":
        context.user_data["state"] = None
        origin = context.user_data.get("search_from", "LHR")
        dest = context.user_data.get("search_to", "anywhere")
        budget = 9999.0
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        try:
            if clean.replace(".","").isdigit():
                budget = float(clean)
        except Exception:
            pass
        query_str = f"{origin} → {dest}"
        msg = await update.message.reply_text(
            t(lang, "searching", query=query_str), parse_mode="Markdown"
        )
        try:
            deals = await scanner.search(f"{origin} to {dest}", budget_pp=budget)
            await msg.delete()
            if deals:
                await send_deals(update.message.reply_text, deals, sym, lang)
            else:
                await update.message.reply_text(
                    t(lang, "no_deals"),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(t(lang, "set_alert_btn"), callback_data="add_alert")
                    ]])
                )
        except Exception as e:
            logger.error(f"search flow error: {e}")
            await msg.edit_text(t(lang, "no_deals"))

    # ── ALERT FLOW ──
    elif state == "awaiting_alert_route":
        context.user_data["alert_route"] = text
        context.user_data["state"] = "awaiting_alert_budget"
        await update.message.reply_text(
            t(lang, "alert_budget_prompt", route=text), parse_mode="Markdown"
        )

    elif state == "awaiting_alert_budget":
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        try:
            budget = float(clean)
            route = context.user_data.get("alert_route", "")
            context.user_data["state"] = None
            await db.create_alert(user_id, route, budget, prefs.get("currency","GBP"), sym)
            await update.message.reply_text(
                t(lang, "alert_set", route=route, sym=sym, budget=int(budget)),
                parse_mode="Markdown", reply_markup=main_kb(lang)
            )
        except ValueError:
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"create_alert error: {e}")
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")

    # ── HUNTER FLOW ──
    elif state == "awaiting_hunt_dest":
        context.user_data["hunt_dest"] = text
        context.user_data["state"] = "awaiting_hunt_budget"
        await update.message.reply_text(
            t(lang, "hunt_budget_prompt", dest=text), parse_mode="Markdown"
        )

    elif state == "awaiting_hunt_budget":
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        try:
            budget = float(clean)
            dest = context.user_data.get("hunt_dest", "Anywhere")
            context.user_data["state"] = None
            await db.create_hunt(user_id, dest, budget, prefs.get("currency","GBP"), sym)
            budget_display = int(budget) if budget > 0 else t(lang, "hunt_no_limit")
            sym_display = sym if budget > 0 else ""
            await update.message.reply_text(
                t(lang, "hunt_started", dest=dest, sym=sym_display, budget=budget_display),
                parse_mode="Markdown", reply_markup=main_kb(lang)
            )
        except ValueError:
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"create_hunt error: {e}")
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")

    # ── CITY FLOW ──
    elif state == "awaiting_city":
        context.user_data["state"] = None
        try:
            await db.set_user_city(user_id, text)
        except Exception as e:
            logger.error(f"set_user_city error: {e}")
        await update.message.reply_text(
            t(lang, "city_set", city=text), parse_mode="Markdown",
            reply_markup=main_kb(lang)
        )

    # ── DEFAULT — free text search ──
    else:
        msg = await update.message.reply_text(
            t(lang, "searching", query=text), parse_mode="Markdown"
        )
        try:
            deals = await scanner.search(text, budget_pp=prefs.get("budget_pp", 9999))
            await msg.delete()
            if deals:
                await send_deals(update.message.reply_text, deals, sym, lang)
            else:
                await update.message.reply_text(
                    t(lang, "no_deals"),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(t(lang, "set_alert_btn"), callback_data="add_alert")
                    ]])
                )
        except Exception as e:
            logger.error(f"default message error: {e}")
            await msg.edit_text(t(lang, "no_deals"))


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("hot", cmd_hot))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("alerts", cmd_alerts))
    app.add_handler(CommandHandler("hunter", cmd_hunter))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    logger.info("🚀 Fairo bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
