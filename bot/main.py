"""
Fairo Telegram Bot — v3 production
Full onboarding · Full search with dates/pax/flexibility · All 10 languages
"""
import logging
from datetime import datetime, timedelta
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
"ob_welcome": "☀️ Welcome to *Fairo*!\n\nTravel prices, finally fair. I scan flights, hotels and packages 24/7.\n\nFirst, let's set you up — it only takes 30 seconds.\n\n*Choose your language:*",
"ob_currency": "💱 *Choose your currency:*",
"ob_city": "📍 *Where do you fly from?*\n\nSend your home city or airport code.\nExample: `London` or `LHR`",
"ob_city_set": "✅ Got it! Home city set to *{city}*.\n\nYou're all set! Here's what I can do:",
"welcome_back": "☀️ Welcome back to *Fairo*, {name}!\n\nWhat would you like to do?",
"main_search": "🔍 Search", "main_hot": "🔥 Hot deals",
"main_alerts": "🔔 My alerts", "main_hunter": "🎯 Hunter",
"main_settings": "⚙️ Settings", "main_help": "❓ Help",
"help_text": (
    "☀️ *How Fairo works*\n\n"
    "🔍 *Search* — step by step: type, destination, dates, passengers, budget. I find the best deals.\n\n"
    "🔥 *Hot deals* — best deals live right now. Error fares, flash sales, last-minute.\n\n"
    "🔔 *Alerts* — save a route and I watch it 24/7. Instant ping when a deal appears.\n\n"
    "🎯 *Hunter* — set me on a mission to a destination. I scan every 15 min and update you live.\n\n"
    "⚙️ *Settings* — change language, home city and currency.\n\n"
    "💸 *100% free* — Fairo earns a small affiliate commission when you book, at zero extra cost to you."
),
"search_type_prompt": "🔍 *Search*\n\nWhat are you looking for?",
"type_flights": "✈️ Flights", "type_hotels": "🏨 Hotels",
"type_package": "📦 Package", "type_mix": "⚡ Mix (all)",
"search_from": "✈️ *Where are you flying from?*\n\nSend a city or airport code.\nExample: `London` or `LHR`",
"search_to": "🌍 *Where do you want to go?*\n\nSend a city, airport or type `Anywhere`",
"search_flex": "📅 *Date flexibility?*",
"flex_exact": "📅 Exact dates", "flex_weekends": "🌅 Weekends",
"flex_school": "🏫 School holidays", "flex_anytime": "⏰ Anytime",
"search_depart": "📅 *Departure date*\n\nSend the date you want to fly out.\nFormat: `DD/MM/YYYY` — e.g. `25/05/2026`",
"search_return": "📅 *Return date*\n\nSend the date you want to fly back.\nFormat: `DD/MM/YYYY` — e.g. `01/06/2026`\n\nOr type `oneway` for a one-way trip.",
"search_checkin": "📅 *Check-in date*\n\nSend the date you want to check in.\nFormat: `DD/MM/YYYY` — e.g. `25/05/2026`",
"search_checkout": "📅 *Check-out date*\n\nSend the date you want to check out.\nFormat: `DD/MM/YYYY` — e.g. `01/06/2026`",
"weekend_pick": "🌅 *Which weekend?*",
"wknd_next": "Next weekend", "wknd_2": "In 2 weeks", "wknd_3": "In 3 weeks", "wknd_4": "In 4 weeks",
"school_pick": "🏫 *Which school holiday?*",
"sch_easter": "🐣 Easter", "sch_may": "🌸 May half term",
"sch_summer": "☀️ Summer", "sch_oct": "🍂 Oct half term",
"anytime_pick": "⏰ *How far ahead?*",
"any_1m": "1 month", "any_3m": "3 months", "any_6m": "6 months", "any_any": "Anytime",
"search_trip": "✈️ *Trip type?*",
"trip_return": "↔️ Return", "trip_oneway": "→ One-way",
"search_adults": "👥 *How many adults?* (16+)",
"search_children": "🧒 *How many children?* (2–15)\n\nType `0` if none.",
"search_budget": "💰 *Max budget per person?*\n\nSend a number e.g. `300`\nOr type `any` for no limit.",
"searching": "🔍 Searching for deals on *{query}*...\n\n_This may take a few seconds_",
"no_deals": "😔 No deals found right now.\n\nTry setting an alert and I'll ping you the moment one appears!",
"set_alert_btn": "🔔 Set alert", "back": "« Back", "skip": "Skip →",
"invalid_date": "❌ Invalid date. Please use DD/MM/YYYY format, e.g. `25/05/2026`",
"invalid_number": "❌ Please send just a number, e.g. `2`",
"invalid_budget": "❌ Please send a number e.g. `300`, or type `any`",
"book_now": "👉 Book now", "alert_me": "🔔 Alert me",
"hot_scanning": "🔥 Scanning for hot deals right now...",
"no_hot": "😔 No hot deals right now — check back in 15 minutes!",
"no_alerts": "🔔 *No alerts yet.*\n\nAdd a route and I'll watch it 24/7.",
"add_alert": "➕ Add alert", "add_new_alert": "➕ Add new alert",
"your_alerts": "🔔 *Your alerts:*\n\n",
"pause": "⏸ Pause", "resume": "▶️ Resume", "delete": "🗑 Delete",
"alert_deleted": "🗑 Alert deleted.",
"alert_route_prompt": "🔔 *New alert*\n\nSend the route you want to watch:\n`London → Dubai`\nor just the destination:\n`Dubai`",
"alert_budget_prompt": "✅ Route: *{route}*\n\nMax budget per person? (e.g. `150`)",
"alert_set": "🔔 *Alert set!*\n\n*{route}* — under {sym}{budget} pp\n\n🟢 Running 24/7. I'll ping you the moment a deal appears.",
"no_hunter": "🎯 *Deal Hunter*\n\nSet me on a mission. I scan a destination every 15 minutes and alert you when the best deal appears.\n\nNo hunts running yet.",
"start_hunt": "🎯 Start a new hunt",
"your_hunts": "🎯 *Your active hunts:*\n\n",
"hunt_searching": "🔍 Scanning...", "hunt_found": "✅ Deal found!",
"hunt_dest_prompt": "🎯 *New hunt*\n\nWhere do you want to go?\n\n• `Dubai`\n• `Tenerife`\n• `Anywhere warm`\n• `Anywhere`",
"hunt_budget_prompt": "📍 Destination: *{dest}*\n\nMax budget per person?\nNumber e.g. `200`, or `0` for no limit",
"hunt_started": "🎯 *Hunt started!*\n\n📍 {dest}\n💰 Under {sym}{budget} pp\n⏱ Scanning every 15 minutes\n\nI'll alert you the moment a deal appears.",
"hunt_no_limit": "No limit",
"pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Resume", "stop_hunt": "✕ Stop",
"best_deal": "Best deal found",
"settings_menu": "⚙️ *Settings*\n\nWhat would you like to change?",
"lang_btn": "🌐 Language", "curr_btn": "💱 Currency", "city_btn": "📍 Home city",
"lang_prompt": "🌐 *Choose your language:*",
"lang_set": "✅ Language updated!",
"curr_prompt": "💱 *Choose your currency:*",
"curr_set": "✅ Currency set to {sym}",
"city_prompt": "📍 *Home city*\n\nSend your home city or airport code.\nExample: `London` or `LHR`",
"city_set": "✅ Home city set to *{city}*",
"pp": "pp", "nights": "nights", "adults": "adult(s)", "children": "child(ren)",
"return_trip": "return", "oneway": "one-way",
"dep": "Dep", "ret": "Ret", "checkin": "Check in", "checkout": "Check out",
},
"es": {
"ob_welcome": "☀️ ¡Bienvenido a *Fairo*!\n\nPrecios de viaje, finalmente justos. Escaneo vuelos, hoteles y paquetes 24/7.\n\nPrimero, vamos a configurarte — solo tarda 30 segundos.\n\n*Elige tu idioma:*",
"ob_currency": "💱 *Elige tu moneda:*",
"ob_city": "📍 *¿Desde dónde vuelas?*\n\nEnvía tu ciudad de origen o código de aeropuerto.\nEjemplo: `Madrid` o `MAD`",
"ob_city_set": "✅ ¡Listo! Ciudad establecida: *{city}*.\n\n¡Todo configurado! Esto es lo que puedo hacer:",
"welcome_back": "☀️ ¡Bienvenido de vuelta a *Fairo*, {name}!\n\n¿Qué quieres hacer?",
"main_search": "🔍 Buscar", "main_hot": "🔥 Ofertas calientes",
"main_alerts": "🔔 Mis alertas", "main_hunter": "🎯 Cazador",
"main_settings": "⚙️ Ajustes", "main_help": "❓ Ayuda",
"help_text": "☀️ *Cómo funciona Fairo*\n\n🔍 *Buscar* — paso a paso: tipo, destino, fechas, pasajeros, presupuesto.\n\n🔥 *Ofertas calientes* — mejores ofertas ahora.\n\n🔔 *Alertas* — guarda una ruta y la vigilo 24/7.\n\n🎯 *Cazador* — misión continua cada 15 minutos.\n\n⚙️ *Ajustes* — idioma, ciudad y moneda.\n\n💸 *100% gratis*",
"search_type_prompt": "🔍 *Buscar*\n\n¿Qué buscas?",
"type_flights": "✈️ Vuelos", "type_hotels": "🏨 Hoteles",
"type_package": "📦 Paquete", "type_mix": "⚡ Mix (todo)",
"search_from": "✈️ *¿Desde dónde vuelas?*\n\nEnvía ciudad o código de aeropuerto.\nEjemplo: `Madrid` o `MAD`",
"search_to": "🌍 *¿A dónde quieres ir?*\n\nCiudad, aeropuerto o escribe `Cualquier lugar`",
"search_flex": "📅 *¿Flexibilidad de fechas?*",
"flex_exact": "📅 Fechas exactas", "flex_weekends": "🌅 Fines de semana",
"flex_school": "🏫 Vacaciones escolares", "flex_anytime": "⏰ Cualquier momento",
"search_depart": "📅 *Fecha de salida*\n\nFormato: `DD/MM/AAAA` — ej. `25/05/2026`",
"search_return": "📅 *Fecha de regreso*\n\nFormato: `DD/MM/AAAA` — ej. `01/06/2026`\n\nO escribe `soloida` para solo ida.",
"search_checkin": "📅 *Fecha de entrada*\n\nFormato: `DD/MM/AAAA` — ej. `25/05/2026`",
"search_checkout": "📅 *Fecha de salida del hotel*\n\nFormato: `DD/MM/AAAA` — ej. `01/06/2026`",
"weekend_pick": "🌅 *¿Qué fin de semana?*",
"wknd_next": "Próximo fin de semana", "wknd_2": "En 2 semanas",
"wknd_3": "En 3 semanas", "wknd_4": "En 4 semanas",
"school_pick": "🏫 *¿Qué vacaciones?*",
"sch_easter": "🐣 Semana Santa", "sch_may": "🌸 Mayo",
"sch_summer": "☀️ Verano", "sch_oct": "🍂 Octubre",
"anytime_pick": "⏰ *¿Con cuánta anticipación?*",
"any_1m": "1 mes", "any_3m": "3 meses", "any_6m": "6 meses", "any_any": "Cualquier momento",
"search_trip": "✈️ *¿Tipo de viaje?*",
"trip_return": "↔️ Ida y vuelta", "trip_oneway": "→ Solo ida",
"search_adults": "👥 *¿Cuántos adultos?* (16+)",
"search_children": "🧒 *¿Cuántos niños?* (2–15)\n\nEscribe `0` si ninguno.",
"search_budget": "💰 *¿Presupuesto máximo por persona?*\n\nNúmero ej. `300` o escribe `sin límite`.",
"searching": "🔍 Buscando ofertas para *{query}*...\n\n_Esto puede tardar unos segundos_",
"no_deals": "😔 No hay ofertas ahora.\n\n¡Crea una alerta y te aviso cuando aparezca una!",
"set_alert_btn": "🔔 Crear alerta", "back": "« Volver", "skip": "Omitir →",
"invalid_date": "❌ Fecha inválida. Usa DD/MM/AAAA, ej. `25/05/2026`",
"invalid_number": "❌ Por favor envía solo un número, ej. `2`",
"invalid_budget": "❌ Envía un número ej. `300`, o escribe `sin límite`",
"book_now": "👉 Reservar", "alert_me": "🔔 Alertarme",
"hot_scanning": "🔥 Buscando las mejores ofertas ahora...",
"no_hot": "😔 No hay ofertas calientes ahora — ¡vuelve en 15 minutos!",
"no_alerts": "🔔 *Sin alertas.*\n\nAgrega una ruta y la vigilo 24/7.",
"add_alert": "➕ Agregar alerta", "add_new_alert": "➕ Nueva alerta",
"your_alerts": "🔔 *Tus alertas:*\n\n",
"pause": "⏸ Pausar", "resume": "▶️ Reanudar", "delete": "🗑 Borrar",
"alert_deleted": "🗑 Alerta eliminada.",
"alert_route_prompt": "🔔 *Nueva alerta*\n\nRuta ej:\n`Madrid → Dubai`\no destino:\n`Dubai`",
"alert_budget_prompt": "✅ Ruta: *{route}*\n\n¿Presupuesto máximo por persona? (ej. `150`)",
"alert_set": "🔔 *¡Alerta configurada!*\n\n*{route}* — bajo {sym}{budget} pp\n\n🟢 Activa 24/7.",
"no_hunter": "🎯 *Cazador de Ofertas*\n\nEnvíame en misión. Escaneo cada 15 minutos.\n\nSin cacerías activas.",
"start_hunt": "🎯 Nueva caza",
"your_hunts": "🎯 *Tus cacerías activas:*\n\n",
"hunt_searching": "🔍 Buscando...", "hunt_found": "✅ ¡Oferta encontrada!",
"hunt_dest_prompt": "🎯 *Nueva caza*\n\n¿A dónde?\n\n• `Dubai`\n• `Tenerife`\n• `Cualquier lugar cálido`",
"hunt_budget_prompt": "📍 Destino: *{dest}*\n\n¿Presupuesto máximo por persona?\nNúmero ej. `200`, o `0` sin límite",
"hunt_started": "🎯 *¡Cacería iniciada!*\n\n📍 {dest}\n💰 Bajo {sym}{budget} pp\n⏱ Cada 15 minutos",
"hunt_no_limit": "Sin límite",
"pause_hunt": "⏸ Pausar", "resume_hunt": "▶️ Reanudar", "stop_hunt": "✕ Detener",
"best_deal": "Mejor oferta encontrada",
"settings_menu": "⚙️ *Ajustes*\n\n¿Qué quieres cambiar?",
"lang_btn": "🌐 Idioma", "curr_btn": "💱 Moneda", "city_btn": "📍 Ciudad",
"lang_prompt": "🌐 *Elige tu idioma:*",
"lang_set": "✅ ¡Idioma actualizado!",
"curr_prompt": "💱 *Elige tu moneda:*",
"curr_set": "✅ Moneda: {sym}",
"city_prompt": "📍 *Ciudad de origen*\n\nCiudad o aeropuerto, ej. `Madrid`",
"city_set": "✅ Ciudad: *{city}*",
"pp": "pp", "nights": "noches", "adults": "adulto(s)", "children": "niño(s)",
"return_trip": "ida y vuelta", "oneway": "solo ida",
"dep": "Sal", "ret": "Reg", "checkin": "Entrada", "checkout": "Salida",
},
"fr": {
"ob_welcome": "☀️ Bienvenue sur *Fairo*!\n\nDes prix de voyage enfin justes. Je scanne les vols, hôtels et forfaits 24h/24.\n\nD'abord, configurons-vous — ça prend 30 secondes.\n\n*Choisissez votre langue :*",
"ob_currency": "💱 *Choisissez votre devise :*",
"ob_city": "📍 *D'où partez-vous ?*\n\nEnvoyez votre ville ou code aéroport.\nExemple : `Paris` ou `CDG`",
"ob_city_set": "✅ Parfait! Ville définie : *{city}*.\n\nTout est prêt! Voici ce que je peux faire :",
"welcome_back": "☀️ Bon retour sur *Fairo*, {name}!\n\nQue voulez-vous faire ?",
"main_search": "🔍 Recherche", "main_hot": "🔥 Offres brûlantes",
"main_alerts": "🔔 Mes alertes", "main_hunter": "🎯 Chasseur",
"main_settings": "⚙️ Paramètres", "main_help": "❓ Aide",
"help_text": "☀️ *Comment fonctionne Fairo*\n\n🔍 *Recherche* — étape par étape: type, destination, dates, passagers, budget.\n\n🔥 *Offres brûlantes* — meilleures offres maintenant.\n\n🔔 *Alertes* — sauvegardez un trajet, je surveille 24h/24.\n\n🎯 *Chasseur* — mission continue toutes les 15 minutes.\n\n⚙️ *Paramètres* — langue, ville et devise.\n\n💸 *100% gratuit*",
"search_type_prompt": "🔍 *Recherche*\n\nQue cherchez-vous ?",
"type_flights": "✈️ Vols", "type_hotels": "🏨 Hôtels",
"type_package": "📦 Forfait", "type_mix": "⚡ Mix (tout)",
"search_from": "✈️ *D'où partez-vous ?*\n\nVille ou code aéroport.\nExemple : `Paris` ou `CDG`",
"search_to": "🌍 *Où voulez-vous aller ?*\n\nVille, aéroport ou tapez `N'importe où`",
"search_flex": "📅 *Flexibilité des dates ?*",
"flex_exact": "📅 Dates exactes", "flex_weekends": "🌅 Week-ends",
"flex_school": "🏫 Vacances scolaires", "flex_anytime": "⏰ N'importe quand",
"search_depart": "📅 *Date de départ*\n\nFormat : `JJ/MM/AAAA` — ex. `25/05/2026`",
"search_return": "📅 *Date de retour*\n\nFormat : `JJ/MM/AAAA` — ex. `01/06/2026`\n\nOu tapez `aller` pour aller simple.",
"search_checkin": "📅 *Date d'arrivée*\n\nFormat : `JJ/MM/AAAA` — ex. `25/05/2026`",
"search_checkout": "📅 *Date de départ*\n\nFormat : `JJ/MM/AAAA` — ex. `01/06/2026`",
"weekend_pick": "🌅 *Quel week-end ?*",
"wknd_next": "Week-end prochain", "wknd_2": "Dans 2 semaines",
"wknd_3": "Dans 3 semaines", "wknd_4": "Dans 4 semaines",
"school_pick": "🏫 *Quelles vacances ?*",
"sch_easter": "🐣 Pâques", "sch_may": "🌸 Pont de mai",
"sch_summer": "☀️ Été", "sch_oct": "🍂 Toussaint",
"anytime_pick": "⏰ *À quelle échéance ?*",
"any_1m": "1 mois", "any_3m": "3 mois", "any_6m": "6 mois", "any_any": "N'importe quand",
"search_trip": "✈️ *Type de voyage ?*",
"trip_return": "↔️ Aller-retour", "trip_oneway": "→ Aller simple",
"search_adults": "👥 *Combien d'adultes ?* (16+)",
"search_children": "🧒 *Combien d'enfants ?* (2–15)\n\nTapez `0` si aucun.",
"search_budget": "💰 *Budget maximum par personne ?*\n\nNombre ex. `300` ou tapez `illimité`.",
"searching": "🔍 Recherche d'offres pour *{query}*...\n\n_Cela peut prendre quelques secondes_",
"no_deals": "😔 Pas d'offres pour l'instant.\n\nCréez une alerte et je vous préviendrai !",
"set_alert_btn": "🔔 Créer une alerte", "back": "« Retour", "skip": "Ignorer →",
"invalid_date": "❌ Date invalide. Utilisez JJ/MM/AAAA ex. `25/05/2026`",
"invalid_number": "❌ Envoyez juste un nombre ex. `2`",
"invalid_budget": "❌ Envoyez un nombre ex. `300`, ou tapez `illimité`",
"book_now": "👉 Réserver", "alert_me": "🔔 M'alerter",
"hot_scanning": "🔥 Recherche des meilleures offres maintenant...",
"no_hot": "😔 Pas d'offres brûlantes — revenez dans 15 minutes !",
"no_alerts": "🔔 *Pas d'alertes.*\n\nAjoutez un trajet, je surveille 24h/24.",
"add_alert": "➕ Ajouter alerte", "add_new_alert": "➕ Nouvelle alerte",
"your_alerts": "🔔 *Vos alertes :*\n\n",
"pause": "⏸ Pause", "resume": "▶️ Reprendre", "delete": "🗑 Supprimer",
"alert_deleted": "🗑 Alerte supprimée.",
"alert_route_prompt": "🔔 *Nouvelle alerte*\n\nTrajet ex:\n`Paris → Dubaï`\nou destination:\n`Dubaï`",
"alert_budget_prompt": "✅ Trajet : *{route}*\n\nBudget max par personne ? (ex. `150`)",
"alert_set": "🔔 *Alerte créée !*\n\n*{route}* — sous {sym}{budget} pp\n\n🟢 Active 24h/24.",
"no_hunter": "🎯 *Chasseur d'Offres*\n\nEnvoyez-moi en mission. Scan toutes les 15 minutes.\n\nPas de chasse active.",
"start_hunt": "🎯 Nouvelle chasse",
"your_hunts": "🎯 *Vos chasses actives :*\n\n",
"hunt_searching": "🔍 Scan...", "hunt_found": "✅ Offerte trouvée !",
"hunt_dest_prompt": "🎯 *Nouvelle chasse*\n\nOù ?\n\n• `Dubaï`\n• `Tenerife`\n• `N'importe où de chaud`",
"hunt_budget_prompt": "📍 Destination : *{dest}*\n\nBudget max par personne ?\nNombre ex. `200`, ou `0` illimité",
"hunt_started": "🎯 *Chasse lancée !*\n\n📍 {dest}\n💰 Sous {sym}{budget} pp\n⏱ Toutes les 15 minutes",
"hunt_no_limit": "Illimité",
"pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Reprendre", "stop_hunt": "✕ Arrêter",
"best_deal": "Meilleure offre trouvée",
"settings_menu": "⚙️ *Paramètres*\n\nQue voulez-vous modifier ?",
"lang_btn": "🌐 Langue", "curr_btn": "💱 Devise", "city_btn": "📍 Ville",
"lang_prompt": "🌐 *Choisissez votre langue :*",
"lang_set": "✅ Langue mise à jour !",
"curr_prompt": "💱 *Choisissez votre devise :*",
"curr_set": "✅ Devise : {sym}",
"city_prompt": "📍 *Ville de départ*\n\nVille ou aéroport, ex. `Paris`",
"city_set": "✅ Ville : *{city}*",
"pp": "pp", "nights": "nuits", "adults": "adulte(s)", "children": "enfant(s)",
"return_trip": "aller-retour", "oneway": "aller simple",
"dep": "Dép", "ret": "Ret", "checkin": "Arrivée", "checkout": "Départ",
},
"de": {
"ob_welcome": "☀️ Willkommen bei *Fairo*!\n\nReisepreise, endlich fair. Ich scanne Flüge, Hotels und Pakete rund um die Uhr.\n\nLassen Sie uns zunächst einrichten — dauert nur 30 Sekunden.\n\n*Wählen Sie Ihre Sprache:*",
"ob_currency": "💱 *Wählen Sie Ihre Währung:*",
"ob_city": "📍 *Von wo fliegen Sie?*\n\nSenden Sie Ihre Heimatstadt oder den Flughafencode.\nBeispiel: `Berlin` oder `BER`",
"ob_city_set": "✅ Verstanden! Heimatstadt: *{city}*.\n\nAlles eingerichtet! Das kann ich tun:",
"welcome_back": "☀️ Willkommen zurück bei *Fairo*, {name}!\n\nWas möchten Sie tun?",
"main_search": "🔍 Suche", "main_hot": "🔥 Heiße Angebote",
"main_alerts": "🔔 Meine Alarme", "main_hunter": "🎯 Jäger",
"main_settings": "⚙️ Einstellungen", "main_help": "❓ Hilfe",
"help_text": "☀️ *So funktioniert Fairo*\n\n🔍 *Suche* — Schritt für Schritt: Typ, Ziel, Daten, Passagiere, Budget.\n\n🔥 *Heiße Angebote* — beste Angebote jetzt.\n\n🔔 *Alarme* — Strecke speichern, ich überwache 24/7.\n\n🎯 *Jäger* — kontinuierlich alle 15 Minuten.\n\n⚙️ *Einstellungen* — Sprache, Stadt und Währung.\n\n💸 *100% kostenlos*",
"search_type_prompt": "🔍 *Suche*\n\nWas suchen Sie?",
"type_flights": "✈️ Flüge", "type_hotels": "🏨 Hotels",
"type_package": "📦 Paket", "type_mix": "⚡ Mix (alles)",
"search_from": "✈️ *Von wo fliegen Sie?*\n\nStadt oder Flughafencode.\nBeispiel: `Berlin` oder `BER`",
"search_to": "🌍 *Wohin möchten Sie?*\n\nStadt, Flughafen oder `Irgendwo`",
"search_flex": "📅 *Datumsflexibilität?*",
"flex_exact": "📅 Genaue Daten", "flex_weekends": "🌅 Wochenenden",
"flex_school": "🏫 Schulferien", "flex_anytime": "⏰ Jederzeit",
"search_depart": "📅 *Abflugdatum*\n\nFormat: `TT.MM.JJJJ` — z.B. `25.05.2026`",
"search_return": "📅 *Rückflugdatum*\n\nFormat: `TT.MM.JJJJ` — z.B. `01.06.2026`\n\nOder tippen Sie `hinfahrt` für nur Hinfahrt.",
"search_checkin": "📅 *Check-in Datum*\n\nFormat: `TT.MM.JJJJ` — z.B. `25.05.2026`",
"search_checkout": "📅 *Check-out Datum*\n\nFormat: `TT.MM.JJJJ` — z.B. `01.06.2026`",
"weekend_pick": "🌅 *Welches Wochenende?*",
"wknd_next": "Nächstes Wochenende", "wknd_2": "In 2 Wochen",
"wknd_3": "In 3 Wochen", "wknd_4": "In 4 Wochen",
"school_pick": "🏫 *Welche Schulferien?*",
"sch_easter": "🐣 Ostern", "sch_may": "🌸 Pfingstferien",
"sch_summer": "☀️ Sommerferien", "sch_oct": "🍂 Herbstferien",
"anytime_pick": "⏰ *Wie weit voraus?*",
"any_1m": "1 Monat", "any_3m": "3 Monate", "any_6m": "6 Monate", "any_any": "Jederzeit",
"search_trip": "✈️ *Reiseart?*",
"trip_return": "↔️ Hin und zurück", "trip_oneway": "→ Nur Hinfahrt",
"search_adults": "👥 *Wie viele Erwachsene?* (16+)",
"search_children": "🧒 *Wie viele Kinder?* (2–15)\n\nTippen Sie `0` wenn keine.",
"search_budget": "💰 *Maximales Budget pro Person?*\n\nZahl z.B. `300` oder `unbegrenzt`.",
"searching": "🔍 Suche Angebote für *{query}*...\n\n_Das kann einige Sekunden dauern_",
"no_deals": "😔 Keine Angebote gerade.\n\nAlarm setzen und ich benachrichtige Sie!",
"set_alert_btn": "🔔 Alarm setzen", "back": "« Zurück", "skip": "Überspringen →",
"invalid_date": "❌ Ungültiges Datum. Bitte TT.MM.JJJJ verwenden z.B. `25.05.2026`",
"invalid_number": "❌ Bitte nur eine Zahl senden z.B. `2`",
"invalid_budget": "❌ Zahl senden z.B. `300`, oder `unbegrenzt`",
"book_now": "👉 Jetzt buchen", "alert_me": "🔔 Alarm",
"hot_scanning": "🔥 Suche heiße Angebote jetzt...",
"no_hot": "😔 Keine heißen Angebote — in 15 Minuten nochmal!",
"no_alerts": "🔔 *Noch keine Alarme.*\n\nStrecke hinzufügen, ich überwache 24/7.",
"add_alert": "➕ Alarm hinzufügen", "add_new_alert": "➕ Neuer Alarm",
"your_alerts": "🔔 *Ihre Alarme:*\n\n",
"pause": "⏸ Pause", "resume": "▶️ Fortsetzen", "delete": "🗑 Löschen",
"alert_deleted": "🗑 Alarm gelöscht.",
"alert_route_prompt": "🔔 *Neuer Alarm*\n\nStrecke z.B.:\n`Berlin → Dubai`\noder Ziel:\n`Dubai`",
"alert_budget_prompt": "✅ Strecke: *{route}*\n\nMax. Budget pro Person? (z.B. `150`)",
"alert_set": "🔔 *Alarm gesetzt!*\n\n*{route}* — unter {sym}{budget} pp\n\n🟢 Läuft 24/7.",
"no_hunter": "🎯 *Angebotsjäger*\n\nAuf Mission schicken. Scan alle 15 Minuten.\n\nNoch keine aktive Jagd.",
"start_hunt": "🎯 Neue Jagd",
"your_hunts": "🎯 *Ihre aktiven Jagden:*\n\n",
"hunt_searching": "🔍 Suche...", "hunt_found": "✅ Angebot gefunden!",
"hunt_dest_prompt": "🎯 *Neue Jagd*\n\nWohin?\n\n• `Dubai`\n• `Teneriffa`\n• `Irgendwo warm`",
"hunt_budget_prompt": "📍 Ziel: *{dest}*\n\nMax. Budget pro Person?\nZahl z.B. `200`, oder `0` unbegrenzt",
"hunt_started": "🎯 *Jagd gestartet!*\n\n📍 {dest}\n💰 Unter {sym}{budget} pp\n⏱ Alle 15 Minuten",
"hunt_no_limit": "Unbegrenzt",
"pause_hunt": "⏸ Pause", "resume_hunt": "▶️ Fortsetzen", "stop_hunt": "✕ Stoppen",
"best_deal": "Bestes Angebot gefunden",
"settings_menu": "⚙️ *Einstellungen*\n\nWas möchten Sie ändern?",
"lang_btn": "🌐 Sprache", "curr_btn": "💱 Währung", "city_btn": "📍 Heimatstadt",
"lang_prompt": "🌐 *Sprache wählen:*",
"lang_set": "✅ Sprache aktualisiert!",
"curr_prompt": "💱 *Währung wählen:*",
"curr_set": "✅ Währung: {sym}",
"city_prompt": "📍 *Heimatstadt*\n\nStadt oder Flughafencode z.B. `Berlin`",
"city_set": "✅ Heimatstadt: *{city}*",
"pp": "pp", "nights": "Nächte", "adults": "Erwachsene", "children": "Kinder",
"return_trip": "Hin-Rück", "oneway": "Hinfahrt",
"dep": "Ab", "ret": "An", "checkin": "Check-in", "checkout": "Check-out",
},
"ar": {
"ob_welcome": "☀️ مرحباً بك في *فارو*!\n\nأسعار سفر عادلة أخيراً. أفحص الرحلات والفنادق والباقات على مدار الساعة.\n\nأولاً، دعنا نعدّك — يستغرق 30 ثانية فقط.\n\n*اختر لغتك:*",
"ob_currency": "💱 *اختر عملتك:*",
"ob_city": "📍 *من أين تسافر؟*\n\nأرسل مدينتك أو رمز المطار.\nمثال: `دبي` أو `DXB`",
"ob_city_set": "✅ تم! المدينة: *{city}*.\n\nكل شيء جاهز! هذا ما يمكنني فعله:",
"welcome_back": "☀️ مرحباً بعودتك إلى *فارو*، {name}!\n\nماذا تريد أن تفعل؟",
"main_search": "🔍 بحث", "main_hot": "🔥 صفقات ساخنة",
"main_alerts": "🔔 تنبيهاتي", "main_hunter": "🎯 صياد",
"main_settings": "⚙️ إعدادات", "main_help": "❓ مساعدة",
"help_text": "☀️ *كيف يعمل فارو*\n\n🔍 *البحث* — خطوة بخطوة: النوع والوجهة والتواريخ والمسافرون والميزانية.\n\n🔥 *الصفقات الساخنة* — أفضل الصفقات الآن.\n\n🔔 *التنبيهات* — احفظ مساراً وأراقبه 24/7.\n\n🎯 *الصياد* — مهمة مستمرة كل 15 دقيقة.\n\n⚙️ *الإعدادات* — اللغة والمدينة والعملة.\n\n💸 *مجاني 100%*",
"search_type_prompt": "🔍 *البحث*\n\nماذا تبحث عن؟",
"type_flights": "✈️ رحلات", "type_hotels": "🏨 فنادق",
"type_package": "📦 باقة", "type_mix": "⚡ مزيج (الكل)",
"search_from": "✈️ *من أين تسافر؟*\n\nمدينة أو رمز المطار.\nمثال: `دبي` أو `DXB`",
"search_to": "🌍 *إلى أين تريد الذهاب؟*\n\nمدينة أو مطار أو اكتب `في أي مكان`",
"search_flex": "📅 *مرونة التواريخ؟*",
"flex_exact": "📅 تواريخ محددة", "flex_weekends": "🌅 عطل نهاية الأسبوع",
"flex_school": "🏫 عطلة مدرسية", "flex_anytime": "⏰ في أي وقت",
"search_depart": "📅 *تاريخ المغادرة*\n\nالتنسيق: `يوم/شهر/سنة` — مثال: `25/05/2026`",
"search_return": "📅 *تاريخ العودة*\n\nالتنسيق: `يوم/شهر/سنة` — مثال: `01/06/2026`\n\nأو اكتب `ذهاب فقط` لرحلة ذهاب.",
"search_checkin": "📅 *تاريخ الوصول*\n\nالتنسيق: `يوم/شهر/سنة` — مثال: `25/05/2026`",
"search_checkout": "📅 *تاريخ المغادرة من الفندق*\n\nالتنسيق: `يوم/شهر/سنة` — مثال: `01/06/2026`",
"weekend_pick": "🌅 *أي نهاية أسبوع؟*",
"wknd_next": "نهاية الأسبوع القادم", "wknd_2": "بعد أسبوعين",
"wknd_3": "بعد 3 أسابيع", "wknd_4": "بعد 4 أسابيع",
"school_pick": "🏫 *أي إجازة؟*",
"sch_easter": "🐣 إجازة الربيع", "sch_may": "🌸 إجازة مايو",
"sch_summer": "☀️ إجازة الصيف", "sch_oct": "🍂 إجازة أكتوبر",
"anytime_pick": "⏰ *كم من الوقت مقدماً؟*",
"any_1m": "شهر واحد", "any_3m": "3 أشهر", "any_6m": "6 أشهر", "any_any": "في أي وقت",
"search_trip": "✈️ *نوع الرحلة؟*",
"trip_return": "↔️ ذهاب وعودة", "trip_oneway": "→ ذهاب فقط",
"search_adults": "👥 *كم عدد البالغين؟* (16+)",
"search_children": "🧒 *كم عدد الأطفال؟* (2–15)\n\nاكتب `0` إذا لم يكن هناك أطفال.",
"search_budget": "💰 *الحد الأقصى للميزانية للشخص؟*\n\nرقم مثل `300` أو اكتب `بلا حد`.",
"searching": "🔍 البحث عن صفقات لـ *{query}*...\n\n_قد يستغرق بضع ثوانٍ_",
"no_deals": "😔 لا توجد صفقات الآن.\n\nأضف تنبيهاً وسأخبرك عند ظهور صفقة!",
"set_alert_btn": "🔔 إضافة تنبيه", "back": "رجوع »", "skip": "تخطي →",
"invalid_date": "❌ تاريخ غير صحيح. استخدم يوم/شهر/سنة مثال: `25/05/2026`",
"invalid_number": "❌ أرسل رقماً فقط مثل `2`",
"invalid_budget": "❌ أرسل رقماً مثل `300`، أو اكتب `بلا حد`",
"book_now": "← احجز الآن", "alert_me": "🔔 تنبيهي",
"hot_scanning": "🔥 البحث عن أفضل الصفقات الآن...",
"no_hot": "😔 لا توجد صفقات ساخنة — تحقق بعد 15 دقيقة!",
"no_alerts": "🔔 *لا تنبيهات بعد.*\n\nأضف مساراً وسأراقبه 24/7.",
"add_alert": "➕ إضافة تنبيه", "add_new_alert": "➕ تنبيه جديد",
"your_alerts": "🔔 *تنبيهاتك:*\n\n",
"pause": "⏸ إيقاف", "resume": "▶️ استئناف", "delete": "🗑 حذف",
"alert_deleted": "🗑 تم حذف التنبيه.",
"alert_route_prompt": "🔔 *تنبيه جديد*\n\nمسار مثل:\n`لندن → دبي`\nأو وجهة:\n`دبي`",
"alert_budget_prompt": "✅ المسار: *{route}*\n\nالحد الأقصى للميزانية للشخص؟ (مثل `150`)",
"alert_set": "🔔 *تم إعداد التنبيه!*\n\n*{route}* — تحت {sym}{budget} للشخص\n\n🟢 يعمل 24/7.",
"no_hunter": "🎯 *صياد الصفقات*\n\nأرسلني في مهمة. فحص كل 15 دقيقة.\n\nلا صيد نشط.",
"start_hunt": "🎯 صيد جديد",
"your_hunts": "🎯 *عمليات الصيد النشطة:*\n\n",
"hunt_searching": "🔍 جارٍ البحث...", "hunt_found": "✅ صفقة وُجدت!",
"hunt_dest_prompt": "🎯 *صيد جديد*\n\nأين؟\n\n• `دبي`\n• `تينيريفي`\n• `في أي مكان دافئ`",
"hunt_budget_prompt": "📍 الوجهة: *{dest}*\n\nالحد الأقصى للميزانية للشخص؟\nرقم مثل `200`، أو `0` بلا حد",
"hunt_started": "🎯 *بدأ الصيد!*\n\n📍 {dest}\n💰 تحت {sym}{budget} للشخص\n⏱ كل 15 دقيقة",
"hunt_no_limit": "بلا حد",
"pause_hunt": "⏸ إيقاف", "resume_hunt": "▶️ استئناف", "stop_hunt": "✕ إيقاف نهائي",
"best_deal": "أفضل صفقة وُجدت",
"settings_menu": "⚙️ *الإعدادات*\n\nماذا تريد تغيير؟",
"lang_btn": "🌐 اللغة", "curr_btn": "💱 العملة", "city_btn": "📍 مدينتك",
"lang_prompt": "🌐 *اختر لغتك:*",
"lang_set": "✅ تم تحديث اللغة!",
"curr_prompt": "💱 *اختر عملتك:*",
"curr_set": "✅ العملة: {sym}",
"city_prompt": "📍 *مدينتك*\n\nمدينة أو رمز المطار مثل `دبي`",
"city_set": "✅ المدينة: *{city}*",
"pp": "للشخص", "nights": "ليالٍ", "adults": "بالغ", "children": "أطفال",
"return_trip": "ذهاب وعودة", "oneway": "ذهاب فقط",
"dep": "ذهاب", "ret": "عودة", "checkin": "الوصول", "checkout": "المغادرة",
},
"tr": {
"ob_welcome": "☀️ *Fairo*'ya hoş geldiniz!\n\nSeyahat fiyatları, sonunda adil. Uçuşları, otelleri ve paketleri 7/24 tarıyorum.\n\nÖnce sizi ayarlayalım — sadece 30 saniye.\n\n*Dilinizi seçin:*",
"ob_currency": "💱 *Para biriminizi seçin:*",
"ob_city": "📍 *Nereden uçuyorsunuz?*\n\nEv şehrinizi veya havalimanı kodunu gönderin.\nÖrnek: `İstanbul` veya `IST`",
"ob_city_set": "✅ Anlaşıldı! Şehir: *{city}*.\n\nHer şey hazır! İşte yapabileceklerim:",
"welcome_back": "☀️ *Fairo*'ya tekrar hoş geldiniz, {name}!\n\nNe yapmak istersiniz?",
"main_search": "🔍 Ara", "main_hot": "🔥 Sıcak fırsatlar",
"main_alerts": "🔔 Uyarılarım", "main_hunter": "🎯 Avcı",
"main_settings": "⚙️ Ayarlar", "main_help": "❓ Yardım",
"help_text": "☀️ *Fairo nasıl çalışır*\n\n🔍 *Arama* — adım adım: tür, hedef, tarihler, yolcular, bütçe.\n\n🔥 *Sıcak fırsatlar* — şu an en iyi fırsatlar.\n\n🔔 *Uyarılar* — rota kaydet, 7/24 takip.\n\n🎯 *Avcı* — her 15 dakikada sürekli tarama.\n\n⚙️ *Ayarlar* — dil, şehir ve para birimi.\n\n💸 *Tamamen ücretsiz*",
"search_type_prompt": "🔍 *Arama*\n\nNe arıyorsunuz?",
"type_flights": "✈️ Uçuşlar", "type_hotels": "🏨 Oteller",
"type_package": "📦 Paket", "type_mix": "⚡ Karışık (hepsi)",
"search_from": "✈️ *Nereden uçuyorsunuz?*\n\nŞehir veya havalimanı kodu.\nÖrnek: `İstanbul` veya `IST`",
"search_to": "🌍 *Nereye gitmek istiyorsunuz?*\n\nŞehir, havalimanı veya `Her yer` yazın",
"search_flex": "📅 *Tarih esnekliği?*",
"flex_exact": "📅 Kesin tarihler", "flex_weekends": "🌅 Hafta sonları",
"flex_school": "🏫 Okul tatili", "flex_anytime": "⏰ Her zaman",
"search_depart": "📅 *Kalkış tarihi*\n\nFormat: `GG/AA/YYYY` — örn. `25/05/2026`",
"search_return": "📅 *Dönüş tarihi*\n\nFormat: `GG/AA/YYYY` — örn. `01/06/2026`\n\nVeya tek yön için `tekyön` yazın.",
"search_checkin": "📅 *Check-in tarihi*\n\nFormat: `GG/AA/YYYY` — örn. `25/05/2026`",
"search_checkout": "📅 *Check-out tarihi*\n\nFormat: `GG/AA/YYYY` — örn. `01/06/2026`",
"weekend_pick": "🌅 *Hangi hafta sonu?*",
"wknd_next": "Gelecek hafta sonu", "wknd_2": "2 hafta sonra",
"wknd_3": "3 hafta sonra", "wknd_4": "4 hafta sonra",
"school_pick": "🏫 *Hangi tatil?*",
"sch_easter": "🐣 Bahar tatili", "sch_may": "🌸 Mayıs tatili",
"sch_summer": "☀️ Yaz tatili", "sch_oct": "🍂 Sonbahar tatili",
"anytime_pick": "⏰ *Ne kadar önceden?*",
"any_1m": "1 ay", "any_3m": "3 ay", "any_6m": "6 ay", "any_any": "Her zaman",
"search_trip": "✈️ *Yolculuk türü?*",
"trip_return": "↔️ Gidiş-Dönüş", "trip_oneway": "→ Tek Yön",
"search_adults": "👥 *Kaç yetişkin?* (16+)",
"search_children": "🧒 *Kaç çocuk?* (2–15)\n\nHiç yoksa `0` yazın.",
"search_budget": "💰 *Kişi başı maksimum bütçe?*\n\nSayı örn. `300` veya `sınırsız` yazın.",
"searching": "🔍 *{query}* için fırsat aranıyor...\n\n_Bu birkaç saniye sürebilir_",
"no_deals": "😔 Şu an fırsat yok.\n\nUyarı ekleyin, çıktığında haber vereyim!",
"set_alert_btn": "🔔 Uyarı ekle", "back": "« Geri", "skip": "Atla →",
"invalid_date": "❌ Geçersiz tarih. GG/AA/YYYY kullanın örn. `25/05/2026`",
"invalid_number": "❌ Lütfen sadece sayı gönderin örn. `2`",
"invalid_budget": "❌ Sayı gönderin örn. `300`, veya `sınırsız` yazın",
"book_now": "👉 Rezervasyon", "alert_me": "🔔 Uyar",
"hot_scanning": "🔥 Sıcak fırsatlar aranıyor...",
"no_hot": "😔 Şu an sıcak fırsat yok — 15 dakika sonra tekrar!",
"no_alerts": "🔔 *Henüz uyarı yok.*\n\nRota ekleyin, 7/24 takip edeyim.",
"add_alert": "➕ Uyarı ekle", "add_new_alert": "➕ Yeni uyarı",
"your_alerts": "🔔 *Uyarılarınız:*\n\n",
"pause": "⏸ Duraklat", "resume": "▶️ Devam", "delete": "🗑 Sil",
"alert_deleted": "🗑 Uyarı silindi.",
"alert_route_prompt": "🔔 *Yeni uyarı*\n\nRota örn.:\n`İstanbul → Dubai`\nveya hedef:\n`Dubai`",
"alert_budget_prompt": "✅ Rota: *{route}*\n\nKişi başı maksimum bütçe? (örn. `150`)",
"alert_set": "🔔 *Uyarı oluşturuldu!*\n\n*{route}* — {sym}{budget} pp altı\n\n🟢 7/24 çalışıyor.",
"no_hunter": "🎯 *Fırsat Avcısı*\n\nGöreve gönder. Her 15 dakikada tarama.\n\nAktif av yok.",
"start_hunt": "🎯 Yeni av",
"your_hunts": "🎯 *Aktif avlarınız:*\n\n",
"hunt_searching": "🔍 Tarıyor...", "hunt_found": "✅ Fırsat bulundu!",
"hunt_dest_prompt": "🎯 *Yeni av*\n\nNereye?\n\n• `Dubai`\n• `Tenerife`\n• `Her yer sıcak`",
"hunt_budget_prompt": "📍 Destinasyon: *{dest}*\n\nKişi başı maks. bütçe?\nSayı örn. `200`, veya `0` sınırsız",
"hunt_started": "🎯 *Av başladı!*\n\n📍 {dest}\n💰 {sym}{budget} pp altı\n⏱ Her 15 dakika",
"hunt_no_limit": "Sınırsız",
"pause_hunt": "⏸ Duraklat", "resume_hunt": "▶️ Devam", "stop_hunt": "✕ Durdur",
"best_deal": "En iyi fırsat bulundu",
"settings_menu": "⚙️ *Ayarlar*\n\nNeyi değiştirmek istersiniz?",
"lang_btn": "🌐 Dil", "curr_btn": "💱 Para birimi", "city_btn": "📍 Şehir",
"lang_prompt": "🌐 *Dilinizi seçin:*",
"lang_set": "✅ Dil güncellendi!",
"curr_prompt": "💱 *Para biriminizi seçin:*",
"curr_set": "✅ Para birimi: {sym}",
"city_prompt": "📍 *Şehriniz*\n\nŞehir veya havalimanı kodu örn. `İstanbul`",
"city_set": "✅ Şehir: *{city}*",
"pp": "kişi başı", "nights": "gece", "adults": "yetişkin", "children": "çocuk",
"return_trip": "gidiş-dönüş", "oneway": "tek yön",
"dep": "Git", "ret": "Dön", "checkin": "Giriş", "checkout": "Çıkış",
},
"hi": {
"ob_welcome": "☀️ *Fairo* में आपका स्वागत है!\n\nयात्रा की कीमतें, आखिरकार उचित। मैं 24/7 उड़ानें, होटल और पैकेज स्कैन करता हूं।\n\nपहले, आपको सेट करते हैं — सिर्फ 30 सेकंड।\n\n*अपनी भाषा चुनें:*",
"ob_currency": "💱 *अपनी मुद्रा चुनें:*",
"ob_city": "📍 *आप कहाँ से उड़ते हैं?*\n\nअपना शहर या एयरपोर्ट कोड भेजें।\nउदाहरण: `दिल्ली` या `DEL`",
"ob_city_set": "✅ समझ गया! शहर सेट: *{city}*।\n\nसब तैयार है! यहाँ है जो मैं कर सकता हूं:",
"welcome_back": "☀️ *Fairo* में वापस स्वागत है, {name}!\n\nआप क्या करना चाहते हैं?",
"main_search": "🔍 खोजें", "main_hot": "🔥 गर्म डील",
"main_alerts": "🔔 मेरे अलर्ट", "main_hunter": "🎯 हंटर",
"main_settings": "⚙️ सेटिंग्स", "main_help": "❓ सहायता",
"help_text": "☀️ *Fairo कैसे काम करता है*\n\n🔍 *खोज* — चरण दर चरण: प्रकार, गंतव्य, तारीखें, यात्री, बजट।\n\n🔥 *गर्म डील* — अभी की सबसे अच्छी डील।\n\n🔔 *अलर्ट* — रूट सेव करें, 24/7 देखता रहूंगा।\n\n🎯 *हंटर* — हर 15 मिनट में स्कैन।\n\n⚙️ *सेटिंग्स* — भाषा, शहर और मुद्रा।\n\n💸 *100% मुफ़्त*",
"search_type_prompt": "🔍 *खोज*\n\nआप क्या ढूंढ रहे हैं?",
"type_flights": "✈️ उड़ानें", "type_hotels": "🏨 होटल",
"type_package": "📦 पैकेज", "type_mix": "⚡ मिश्रित (सब)",
"search_from": "✈️ *आप कहाँ से उड़ रहे हैं?*\n\nशहर या एयरपोर्ट कोड भेजें।\nउदाहरण: `दिल्ली` या `DEL`",
"search_to": "🌍 *आप कहाँ जाना चाहते हैं?*\n\nशहर, एयरपोर्ट या `कहीं भी` लिखें",
"search_flex": "📅 *तारीख में लचीलापन?*",
"flex_exact": "📅 सटीक तारीखें", "flex_weekends": "🌅 सप्ताहांत",
"flex_school": "🏫 स्कूल छुट्टियाँ", "flex_anytime": "⏰ कभी भी",
"search_depart": "📅 *प्रस्थान तारीख*\n\nफॉर्मेट: `DD/MM/YYYY` — जैसे `25/05/2026`",
"search_return": "📅 *वापसी तारीख*\n\nफॉर्मेट: `DD/MM/YYYY` — जैसे `01/06/2026`\n\nया केवल जाने के लिए `oneway` लिखें।",
"search_checkin": "📅 *चेक-इन तारीख*\n\nफॉर्मेट: `DD/MM/YYYY` — जैसे `25/05/2026`",
"search_checkout": "📅 *चेक-आउट तारीख*\n\nफॉर्मेट: `DD/MM/YYYY` — जैसे `01/06/2026`",
"weekend_pick": "🌅 *कौन सा सप्ताहांत?*",
"wknd_next": "अगला सप्ताहांत", "wknd_2": "2 सप्ताह में",
"wknd_3": "3 सप्ताह में", "wknd_4": "4 सप्ताह में",
"school_pick": "🏫 *कौन सी छुट्टी?*",
"sch_easter": "🐣 ईस्टर", "sch_may": "🌸 मई छुट्टी",
"sch_summer": "☀️ गर्मी छुट्टी", "sch_oct": "🍂 अक्टूबर छुट्टी",
"anytime_pick": "⏰ *कितने समय आगे?*",
"any_1m": "1 महीना", "any_3m": "3 महीने", "any_6m": "6 महीने", "any_any": "कभी भी",
"search_trip": "✈️ *यात्रा का प्रकार?*",
"trip_return": "↔️ आना-जाना", "trip_oneway": "→ केवल जाना",
"search_adults": "👥 *कितने वयस्क?* (16+)",
"search_children": "🧒 *कितने बच्चे?* (2–15)\n\nकोई नहीं तो `0` लिखें।",
"search_budget": "💰 *प्रति व्यक्ति अधिकतम बजट?*\n\nसंख्या जैसे `300` या `कोई सीमा नहीं` लिखें।",
"searching": "🔍 *{query}* के लिए डील खोज रहा हूं...\n\n_कुछ सेकंड लग सकते हैं_",
"no_deals": "😔 अभी कोई डील नहीं।\n\nअलर्ट सेट करें और जब मिले बताऊंगा!",
"set_alert_btn": "🔔 अलर्ट सेट करें", "back": "« वापस", "skip": "छोड़ें →",
"invalid_date": "❌ गलत तारीख। DD/MM/YYYY फॉर्मेट उपयोग करें जैसे `25/05/2026`",
"invalid_number": "❌ कृपया सिर्फ संख्या भेजें जैसे `2`",
"invalid_budget": "❌ संख्या भेजें जैसे `300`, या `कोई सीमा नहीं` लिखें",
"book_now": "👉 अभी बुक करें", "alert_me": "🔔 अलर्ट करें",
"hot_scanning": "🔥 अभी गर्म डील खोज रहा हूं...",
"no_hot": "😔 अभी कोई गर्म डील नहीं — 15 मिनट बाद देखें!",
"no_alerts": "🔔 *अभी कोई अलर्ट नहीं।*\n\nरूट जोड़ें, 24/7 देखता रहूंगा।",
"add_alert": "➕ अलर्ट जोड़ें", "add_new_alert": "➕ नया अलर्ट",
"your_alerts": "🔔 *आपके अलर्ट:*\n\n",
"pause": "⏸ रोकें", "resume": "▶️ जारी रखें", "delete": "🗑 हटाएं",
"alert_deleted": "🗑 अलर्ट हटा दिया।",
"alert_route_prompt": "🔔 *नया अलर्ट*\n\nरूट जैसे:\n`दिल्ली → दुबई`\nया गंतव्य:\n`दुबई`",
"alert_budget_prompt": "✅ रूट: *{route}*\n\nप्रति व्यक्ति अधिकतम बजट? (जैसे `150`)",
"alert_set": "🔔 *अलर्ट सेट हो गया!*\n\n*{route}* — {sym}{budget} से कम\n\n🟢 24/7 चल रहा है।",
"no_hunter": "🎯 *डील हंटर*\n\nमुझे मिशन पर भेजें। हर 15 मिनट स्कैन।\n\nकोई सक्रिय हंट नहीं।",
"start_hunt": "🎯 नई खोज",
"your_hunts": "🎯 *आपकी सक्रिय खोजें:*\n\n",
"hunt_searching": "🔍 स्कैन हो रहा है...", "hunt_found": "✅ डील मिली!",
"hunt_dest_prompt": "🎯 *नई खोज*\n\nकहाँ?\n\n• `दुबई`\n• `थाईलैंड`\n• `कहीं भी गर्म`",
"hunt_budget_prompt": "📍 गंतव्य: *{dest}*\n\nप्रति व्यक्ति अधिकतम बजट?\nसंख्या जैसे `200`, या `0` कोई सीमा नहीं",
"hunt_started": "🎯 *खोज शुरू हो गई!*\n\n📍 {dest}\n💰 {sym}{budget} से कम\n⏱ हर 15 मिनट",
"hunt_no_limit": "कोई सीमा नहीं",
"pause_hunt": "⏸ रोकें", "resume_hunt": "▶️ जारी रखें", "stop_hunt": "✕ बंद करें",
"best_deal": "सबसे अच्छी डील मिली",
"settings_menu": "⚙️ *सेटिंग्स*\n\nआप क्या बदलना चाहते हैं?",
"lang_btn": "🌐 भाषा", "curr_btn": "💱 मुद्रा", "city_btn": "📍 शहर",
"lang_prompt": "🌐 *अपनी भाषा चुनें:*",
"lang_set": "✅ भाषा अपडेट हो गई!",
"curr_prompt": "💱 *अपनी मुद्रा चुनें:*",
"curr_set": "✅ मुद्रा: {sym}",
"city_prompt": "📍 *आपका शहर*\n\nशहर या एयरपोर्ट कोड जैसे `दिल्ली`",
"city_set": "✅ शहर: *{city}*",
"pp": "प्रति व्यक्ति", "nights": "रातें", "adults": "वयस्क", "children": "बच्चे",
"return_trip": "आना-जाना", "oneway": "केवल जाना",
"dep": "जाना", "ret": "वापसी", "checkin": "चेक इन", "checkout": "चेक आउट",
},
"it": {
"ob_welcome": "☀️ Benvenuto su *Fairo*!\n\nPrezzi di viaggio finalmente equi. Scansiono voli, hotel e pacchetti 24/7.\n\nPer prima cosa, configuriamoti — richiede solo 30 secondi.\n\n*Scegli la tua lingua:*",
"ob_currency": "💱 *Scegli la tua valuta:*",
"ob_city": "📍 *Da dove parti?*\n\nInvia la tua città o codice aeroporto.\nEsempio: `Roma` o `FCO`",
"ob_city_set": "✅ Capito! Città: *{city}*.\n\nTutto pronto! Ecco cosa posso fare:",
"welcome_back": "☀️ Bentornato su *Fairo*, {name}!\n\nCosa vuoi fare?",
"main_search": "🔍 Cerca", "main_hot": "🔥 Offerte calde",
"main_alerts": "🔔 I miei avvisi", "main_hunter": "🎯 Cacciatore",
"main_settings": "⚙️ Impostazioni", "main_help": "❓ Aiuto",
"help_text": "☀️ *Come funziona Fairo*\n\n🔍 *Cerca* — passo per passo: tipo, destinazione, date, passeggeri, budget.\n\n🔥 *Offerte calde* — migliori offerte ora.\n\n🔔 *Avvisi* — salva un percorso, controllo 24/7.\n\n🎯 *Cacciatore* — missione continua ogni 15 minuti.\n\n⚙️ *Impostazioni* — lingua, città e valuta.\n\n💸 *100% gratuito*",
"search_type_prompt": "🔍 *Cerca*\n\nCosa stai cercando?",
"type_flights": "✈️ Voli", "type_hotels": "🏨 Hotel",
"type_package": "📦 Pacchetto", "type_mix": "⚡ Mix (tutto)",
"search_from": "✈️ *Da dove parti?*\n\nCittà o codice aeroporto.\nEsempio: `Roma` o `FCO`",
"search_to": "🌍 *Dove vuoi andare?*\n\nCittà, aeroporto o scrivi `Ovunque`",
"search_flex": "📅 *Flessibilità delle date?*",
"flex_exact": "📅 Date esatte", "flex_weekends": "🌅 Weekend",
"flex_school": "🏫 Vacanze scolastiche", "flex_anytime": "⏰ Qualsiasi momento",
"search_depart": "📅 *Data di partenza*\n\nFormato: `GG/MM/AAAA` — es. `25/05/2026`",
"search_return": "📅 *Data di ritorno*\n\nFormato: `GG/MM/AAAA` — es. `01/06/2026`\n\nOppure scrivi `solo` per solo andata.",
"search_checkin": "📅 *Data di check-in*\n\nFormato: `GG/MM/AAAA` — es. `25/05/2026`",
"search_checkout": "📅 *Data di check-out*\n\nFormato: `GG/MM/AAAA` — es. `01/06/2026`",
"weekend_pick": "🌅 *Quale weekend?*",
"wknd_next": "Weekend prossimo", "wknd_2": "Tra 2 settimane",
"wknd_3": "Tra 3 settimane", "wknd_4": "Tra 4 settimane",
"school_pick": "🏫 *Quali vacanze?*",
"sch_easter": "🐣 Pasqua", "sch_may": "🌸 Ponti di maggio",
"sch_summer": "☀️ Estate", "sch_oct": "🍂 Autunno",
"anytime_pick": "⏰ *Quanto tempo in anticipo?*",
"any_1m": "1 mese", "any_3m": "3 mesi", "any_6m": "6 mesi", "any_any": "Qualsiasi momento",
"search_trip": "✈️ *Tipo di viaggio?*",
"trip_return": "↔️ Andata e ritorno", "trip_oneway": "→ Solo andata",
"search_adults": "👥 *Quanti adulti?* (16+)",
"search_children": "🧒 *Quanti bambini?* (2–15)\n\nScrivi `0` se nessuno.",
"search_budget": "💰 *Budget massimo per persona?*\n\nNumero es. `300` o scrivi `illimitato`.",
"searching": "🔍 Cerco offerte per *{query}*...\n\n_Potrebbe richiedere qualche secondo_",
"no_deals": "😔 Nessuna offerta adesso.\n\nCrea un avviso e ti avverto quando appare una!",
"set_alert_btn": "🔔 Crea avviso", "back": "« Indietro", "skip": "Salta →",
"invalid_date": "❌ Data non valida. Usa GG/MM/AAAA es. `25/05/2026`",
"invalid_number": "❌ Invia solo un numero es. `2`",
"invalid_budget": "❌ Invia un numero es. `300`, o scrivi `illimitato`",
"book_now": "👉 Prenota", "alert_me": "🔔 Avvisami",
"hot_scanning": "🔥 Cerco le migliori offerte ora...",
"no_hot": "😔 Nessuna offerta calda — riprova tra 15 minuti!",
"no_alerts": "🔔 *Nessun avviso.*\n\nAggiungi un percorso, controllo 24/7.",
"add_alert": "➕ Aggiungi avviso", "add_new_alert": "➕ Nuovo avviso",
"your_alerts": "🔔 *I tuoi avvisi:*\n\n",
"pause": "⏸ Pausa", "resume": "▶️ Riprendi", "delete": "🗑 Elimina",
"alert_deleted": "🗑 Avviso eliminato.",
"alert_route_prompt": "🔔 *Nuovo avviso*\n\nPercorso es.:\n`Roma → Dubai`\no destinazione:\n`Dubai`",
"alert_budget_prompt": "✅ Percorso: *{route}*\n\nBudget max per persona? (es. `150`)",
"alert_set": "🔔 *Avviso creato!*\n\n*{route}* — sotto {sym}{budget} pp\n\n🟢 Attivo 24/7.",
"no_hunter": "🎯 *Cacciatore di Offerte*\n\nMandami in missione. Scansione ogni 15 minuti.\n\nNessuna caccia attiva.",
"start_hunt": "🎯 Nuova caccia",
"your_hunts": "🎯 *Le tue cacce attive:*\n\n",
"hunt_searching": "🔍 Scansione...", "hunt_found": "✅ Offerta trovata!",
"hunt_dest_prompt": "🎯 *Nuova caccia*\n\nDove?\n\n• `Dubai`\n• `Tenerife`\n• `Ovunque caldo`",
"hunt_budget_prompt": "📍 Destinazione: *{dest}*\n\nBudget max per persona?\nNumero es. `200`, o `0` illimitato",
"hunt_started": "🎯 *Caccia avviata!*\n\n📍 {dest}\n💰 Sotto {sym}{budget} pp\n⏱ Ogni 15 minuti",
"hunt_no_limit": "Illimitato",
"pause_hunt": "⏸ Pausa", "resume_hunt": "▶️ Riprendi", "stop_hunt": "✕ Ferma",
"best_deal": "Miglior offerta trovata",
"settings_menu": "⚙️ *Impostazioni*\n\nCosa vuoi modificare?",
"lang_btn": "🌐 Lingua", "curr_btn": "💱 Valuta", "city_btn": "📍 Città",
"lang_prompt": "🌐 *Scegli la tua lingua:*",
"lang_set": "✅ Lingua aggiornata!",
"curr_prompt": "💱 *Scegli la tua valuta:*",
"curr_set": "✅ Valuta: {sym}",
"city_prompt": "📍 *Città di partenza*\n\nCittà o aeroporto es. `Roma`",
"city_set": "✅ Città: *{city}*",
"pp": "pp", "nights": "notti", "adults": "adulto/i", "children": "bambino/i",
"return_trip": "andata e ritorno", "oneway": "solo andata",
"dep": "Part", "ret": "Rit", "checkin": "Check-in", "checkout": "Check-out",
},
"pt": {
"ob_welcome": "☀️ Bem-vindo ao *Fairo*!\n\nPreços de viagem finalmente justos. Pesquiso voos, hotéis e pacotes 24/7.\n\nPrimeiro, vamos configurá-lo — leva apenas 30 segundos.\n\n*Escolha o seu idioma:*",
"ob_currency": "💱 *Escolha a sua moeda:*",
"ob_city": "📍 *De onde parte?*\n\nEnvie a sua cidade ou código de aeroporto.\nExemplo: `Lisboa` ou `LIS`",
"ob_city_set": "✅ Entendido! Cidade: *{city}*.\n\nTudo pronto! Aqui está o que posso fazer:",
"welcome_back": "☀️ Bem-vindo de volta ao *Fairo*, {name}!\n\nO que quer fazer?",
"main_search": "🔍 Pesquisar", "main_hot": "🔥 Ofertas quentes",
"main_alerts": "🔔 Os meus alertas", "main_hunter": "🎯 Caçador",
"main_settings": "⚙️ Preferências", "main_help": "❓ Ajuda",
"help_text": "☀️ *Como funciona o Fairo*\n\n🔍 *Pesquisa* — passo a passo: tipo, destino, datas, passageiros, orçamento.\n\n🔥 *Ofertas quentes* — melhores ofertas agora.\n\n🔔 *Alertas* — guarde uma rota, monitorizo 24/7.\n\n🎯 *Caçador* — missão contínua a cada 15 minutos.\n\n⚙️ *Preferências* — língua, cidade e moeda.\n\n💸 *100% gratuito*",
"search_type_prompt": "🔍 *Pesquisa*\n\nO que procura?",
"type_flights": "✈️ Voos", "type_hotels": "🏨 Hotéis",
"type_package": "📦 Pacote", "type_mix": "⚡ Mix (tudo)",
"search_from": "✈️ *De onde parte?*\n\nCidade ou código de aeroporto.\nExemplo: `Lisboa` ou `LIS`",
"search_to": "🌍 *Para onde quer ir?*\n\nCidade, aeroporto ou escreva `Qualquer lugar`",
"search_flex": "📅 *Flexibilidade de datas?*",
"flex_exact": "📅 Datas exatas", "flex_weekends": "🌅 Fins de semana",
"flex_school": "🏫 Férias escolares", "flex_anytime": "⏰ Qualquer altura",
"search_depart": "📅 *Data de partida*\n\nFormato: `DD/MM/AAAA` — ex. `25/05/2026`",
"search_return": "📅 *Data de regresso*\n\nFormato: `DD/MM/AAAA` — ex. `01/06/2026`\n\nOu escreva `soida` para só ida.",
"search_checkin": "📅 *Data de check-in*\n\nFormato: `DD/MM/AAAA` — ex. `25/05/2026`",
"search_checkout": "📅 *Data de check-out*\n\nFormato: `DD/MM/AAAA` — ex. `01/06/2026`",
"weekend_pick": "🌅 *Qual fim de semana?*",
"wknd_next": "Próximo fim de semana", "wknd_2": "Daqui a 2 semanas",
"wknd_3": "Daqui a 3 semanas", "wknd_4": "Daqui a 4 semanas",
"school_pick": "🏫 *Que férias?*",
"sch_easter": "🐣 Páscoa", "sch_may": "🌸 Feriados de maio",
"sch_summer": "☀️ Verão", "sch_oct": "🍂 Outono",
"anytime_pick": "⏰ *Com que antecedência?*",
"any_1m": "1 mês", "any_3m": "3 meses", "any_6m": "6 meses", "any_any": "Qualquer altura",
"search_trip": "✈️ *Tipo de viagem?*",
"trip_return": "↔️ Ida e volta", "trip_oneway": "→ Só ida",
"search_adults": "👥 *Quantos adultos?* (16+)",
"search_children": "🧒 *Quantas crianças?* (2–15)\n\nEscreva `0` se nenhuma.",
"search_budget": "💰 *Orçamento máximo por pessoa?*\n\nNúmero ex. `300` ou escreva `sem limite`.",
"searching": "🔍 A pesquisar ofertas para *{query}*...\n\n_Pode demorar alguns segundos_",
"no_deals": "😔 Sem ofertas agora.\n\nCrie um alerta e aviso quando aparecer uma!",
"set_alert_btn": "🔔 Criar alerta", "back": "« Voltar", "skip": "Ignorar →",
"invalid_date": "❌ Data inválida. Use DD/MM/AAAA ex. `25/05/2026`",
"invalid_number": "❌ Envie apenas um número ex. `2`",
"invalid_budget": "❌ Envie um número ex. `300`, ou escreva `sem limite`",
"book_now": "👉 Reservar", "alert_me": "🔔 Alertar",
"hot_scanning": "🔥 À procura das melhores ofertas agora...",
"no_hot": "😔 Sem ofertas quentes — volte em 15 minutos!",
"no_alerts": "🔔 *Sem alertas.*\n\nAdicione uma rota, monitorizo 24/7.",
"add_alert": "➕ Adicionar alerta", "add_new_alert": "➕ Novo alerta",
"your_alerts": "🔔 *Os seus alertas:*\n\n",
"pause": "⏸ Pausar", "resume": "▶️ Retomar", "delete": "🗑 Apagar",
"alert_deleted": "🗑 Alerta apagado.",
"alert_route_prompt": "🔔 *Novo alerta*\n\nRota ex.:\n`Lisboa → Dubai`\nou destino:\n`Dubai`",
"alert_budget_prompt": "✅ Rota: *{route}*\n\nOrçamento máx por pessoa? (ex. `150`)",
"alert_set": "🔔 *Alerta criado!*\n\n*{route}* — abaixo de {sym}{budget} pp\n\n🟢 Ativo 24/7.",
"no_hunter": "🎯 *Caçador de Ofertas*\n\nEnvie-me numa missão. Pesquisa a cada 15 minutos.\n\nSem caçadas ativas.",
"start_hunt": "🎯 Nova caçada",
"your_hunts": "🎯 *As suas caçadas ativas:*\n\n",
"hunt_searching": "🔍 A pesquisar...", "hunt_found": "✅ Oferta encontrada!",
"hunt_dest_prompt": "🎯 *Nova caçada*\n\nPara onde?\n\n• `Dubai`\n• `Tenerife`\n• `Qualquer lugar quente`",
"hunt_budget_prompt": "📍 Destino: *{dest}*\n\nOrçamento máx por pessoa?\nNúmero ex. `200`, ou `0` sem limite",
"hunt_started": "🎯 *Caçada iniciada!*\n\n📍 {dest}\n💰 Abaixo de {sym}{budget} pp\n⏱ A cada 15 minutos",
"hunt_no_limit": "Sem limite",
"pause_hunt": "⏸ Pausar", "resume_hunt": "▶️ Retomar", "stop_hunt": "✕ Parar",
"best_deal": "Melhor oferta encontrada",
"settings_menu": "⚙️ *Preferências*\n\nO que quer alterar?",
"lang_btn": "🌐 Língua", "curr_btn": "💱 Moeda", "city_btn": "📍 Cidade",
"lang_prompt": "🌐 *Escolha o seu idioma:*",
"lang_set": "✅ Idioma atualizado!",
"curr_prompt": "💱 *Escolha a sua moeda:*",
"curr_set": "✅ Moeda: {sym}",
"city_prompt": "📍 *Cidade de origem*\n\nCidade ou aeroporto ex. `Lisboa`",
"city_set": "✅ Cidade: *{city}*",
"pp": "pp", "nights": "noites", "adults": "adulto(s)", "children": "criança(s)",
"return_trip": "ida e volta", "oneway": "só ida",
"dep": "Part", "ret": "Reg", "checkin": "Check-in", "checkout": "Check-out",
},
"zh": {
"ob_welcome": "☀️ 欢迎使用 *Fairo*！\n\n旅行价格，终于公平。我24/7扫描航班、酒店和套餐。\n\n首先，让我们为您设置 — 只需30秒。\n\n*选择您的语言：*",
"ob_currency": "💱 *选择您的货币：*",
"ob_city": "📍 *您从哪里出发？*\n\n发送您的城市或机场代码。\n例如：`北京` 或 `PEK`",
"ob_city_set": "✅ 明白了！城市：*{city}*。\n\n一切就绪！以下是我能做的：",
"welcome_back": "☀️ 欢迎回到 *Fairo*，{name}！\n\n您想做什么？",
"main_search": "🔍 搜索", "main_hot": "🔥 热门优惠",
"main_alerts": "🔔 我的提醒", "main_hunter": "🎯 猎手",
"main_settings": "⚙️ 设置", "main_help": "❓ 帮助",
"help_text": "☀️ *Fairo如何工作*\n\n🔍 *搜索* — 逐步进行：类型、目的地、日期、乘客、预算。\n\n🔥 *热门优惠* — 当前最佳优惠。\n\n🔔 *提醒* — 保存路线，我24/7监控。\n\n🎯 *猎手* — 每15分钟持续扫描。\n\n⚙️ *设置* — 语言、城市和货币。\n\n💸 *完全免费*",
"search_type_prompt": "🔍 *搜索*\n\n您在寻找什么？",
"type_flights": "✈️ 航班", "type_hotels": "🏨 酒店",
"type_package": "📦 套餐", "type_mix": "⚡ 混合（全部）",
"search_from": "✈️ *您从哪里出发？*\n\n城市或机场代码。\n例如：`北京` 或 `PEK`",
"search_to": "🌍 *您想去哪里？*\n\n城市、机场或输入 `任何地方`",
"search_flex": "📅 *日期灵活性？*",
"flex_exact": "📅 精确日期", "flex_weekends": "🌅 周末",
"flex_school": "🏫 学校假期", "flex_anytime": "⏰ 任何时间",
"search_depart": "📅 *出发日期*\n\n格式：`DD/MM/YYYY` — 例如 `25/05/2026`",
"search_return": "📅 *返回日期*\n\n格式：`DD/MM/YYYY` — 例如 `01/06/2026`\n\n或输入 `单程` 表示单程。",
"search_checkin": "📅 *入住日期*\n\n格式：`DD/MM/YYYY` — 例如 `25/05/2026`",
"search_checkout": "📅 *退房日期*\n\n格式：`DD/MM/YYYY` — 例如 `01/06/2026`",
"weekend_pick": "🌅 *哪个周末？*",
"wknd_next": "下个周末", "wknd_2": "2周后",
"wknd_3": "3周后", "wknd_4": "4周后",
"school_pick": "🏫 *哪个假期？*",
"sch_easter": "🐣 复活节", "sch_may": "🌸 五月假期",
"sch_summer": "☀️ 暑假", "sch_oct": "🍂 十月假期",
"anytime_pick": "⏰ *提前多久？*",
"any_1m": "1个月", "any_3m": "3个月", "any_6m": "6个月", "any_any": "任何时间",
"search_trip": "✈️ *行程类型？*",
"trip_return": "↔️ 往返", "trip_oneway": "→ 单程",
"search_adults": "👥 *多少成人？* (16+)",
"search_children": "🧒 *多少儿童？* (2–15)\n\n如果没有请输入 `0`。",
"search_budget": "💰 *每人最高预算？*\n\n数字例如 `300` 或输入 `无限制`。",
"searching": "🔍 正在搜索 *{query}* 的优惠...\n\n_可能需要几秒钟_",
"no_deals": "😔 暂无优惠。\n\n设置提醒，有优惠时我会通知您！",
"set_alert_btn": "🔔 设置提醒", "back": "« 返回", "skip": "跳过 →",
"invalid_date": "❌ 日期无效。请使用 DD/MM/YYYY 格式，例如 `25/05/2026`",
"invalid_number": "❌ 请只发送数字，例如 `2`",
"invalid_budget": "❌ 发送数字例如 `300`，或输入 `无限制`",
"book_now": "👉 立即预订", "alert_me": "🔔 提醒我",
"hot_scanning": "🔥 正在搜索热门优惠...",
"no_hot": "😔 暂无热门优惠 — 15分钟后再查看！",
"no_alerts": "🔔 *暂无提醒。*\n\n添加路线，我24/7监控。",
"add_alert": "➕ 添加提醒", "add_new_alert": "➕ 新提醒",
"your_alerts": "🔔 *您的提醒：*\n\n",
"pause": "⏸ 暂停", "resume": "▶️ 恢复", "delete": "🗑 删除",
"alert_deleted": "🗑 提醒已删除。",
"alert_route_prompt": "🔔 *新提醒*\n\n路线例如：\n`北京 → 迪拜`\n或目的地：\n`迪拜`",
"alert_budget_prompt": "✅ 路线：*{route}*\n\n每人最高预算？（例如 `150`）",
"alert_set": "🔔 *提醒已设置！*\n\n*{route}* — 低于 {sym}{budget}/人\n\n🟢 24/7运行。",
"no_hunter": "🎯 *优惠猎手*\n\n让我执行任务。每15分钟扫描。\n\n暂无活跃搜猎。",
"start_hunt": "🎯 开始搜猎",
"your_hunts": "🎯 *您的活跃搜猎：*\n\n",
"hunt_searching": "🔍 扫描中...", "hunt_found": "✅ 找到优惠！",
"hunt_dest_prompt": "🎯 *新搜猎*\n\n去哪里？\n\n• `迪拜`\n• `泰国`\n• `任何温暖的地方`",
"hunt_budget_prompt": "📍 目的地：*{dest}*\n\n每人最高预算？\n数字例如 `200`，或 `0` 无限制",
"hunt_started": "🎯 *搜猎已开始！*\n\n📍 {dest}\n💰 低于 {sym}{budget}/人\n⏱ 每15分钟",
"hunt_no_limit": "无限制",
"pause_hunt": "⏸ 暂停", "resume_hunt": "▶️ 恢复", "stop_hunt": "✕ 停止",
"best_deal": "找到最佳优惠",
"settings_menu": "⚙️ *设置*\n\n您想更改什么？",
"lang_btn": "🌐 语言", "curr_btn": "💱 货币", "city_btn": "📍 城市",
"lang_prompt": "🌐 *选择您的语言：*",
"lang_set": "✅ 语言已更新！",
"curr_prompt": "💱 *选择您的货币：*",
"curr_set": "✅ 货币：{sym}",
"city_prompt": "📍 *出发城市*\n\n城市或机场代码，例如 `北京`",
"city_set": "✅ 城市：*{city}*",
"pp": "每人", "nights": "晚", "adults": "成人", "children": "儿童",
"return_trip": "往返", "oneway": "单程",
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


# ── DATE HELPERS ──────────────────────────────────────────────────────────────

def next_friday() -> datetime:
    today = datetime.now()
    days_ahead = 4 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def weekend_dates(weeks_ahead: int):
    friday = next_friday() + timedelta(weeks=weeks_ahead)
    sunday = friday + timedelta(days=2)
    return friday.strftime("%d/%m/%Y"), sunday.strftime("%d/%m/%Y")


def school_hol_dates(hol: str):
    year = datetime.now().year
    dates = {
        "easter": (f"01/04/{year}", f"14/04/{year}"),
        "may": (f"22/05/{year}", f"26/05/{year}"),
        "summer": (f"22/07/{year}", f"02/09/{year}"),
        "oct": (f"23/10/{year}", f"31/10/{year}"),
    }
    return dates.get(hol, (f"01/07/{year}", f"31/07/{year}"))


def parse_date(text: str) -> str | None:
    """Parse DD/MM/YYYY or DD.MM.YYYY and return YYYY-MM-DD."""
    text = text.strip().replace(".", "/").replace("-", "/")
    try:
        dt = datetime.strptime(text, "%d/%m/%Y")
        if dt < datetime.now():
            return None
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


# ── KEYBOARDS ─────────────────────────────────────────────────────────────────

def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="ob_lang_en"),
         InlineKeyboardButton("🇪🇸 Español", callback_data="ob_lang_es")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="ob_lang_fr"),
         InlineKeyboardButton("🇩🇪 Deutsch", callback_data="ob_lang_de")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="ob_lang_ar"),
         InlineKeyboardButton("🇹🇷 Türkçe", callback_data="ob_lang_tr")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="ob_lang_hi"),
         InlineKeyboardButton("🇮🇹 Italiano", callback_data="ob_lang_it")],
        [InlineKeyboardButton("🇵🇹 Português", callback_data="ob_lang_pt"),
         InlineKeyboardButton("🇨🇳 中文", callback_data="ob_lang_zh")],
    ])


def curr_kb(prefix: str = "ob_curr") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 GBP £", callback_data=f"{prefix}_GBP_£"),
         InlineKeyboardButton("🇺🇸 USD $", callback_data=f"{prefix}_USD_$")],
        [InlineKeyboardButton("🇪🇺 EUR €", callback_data=f"{prefix}_EUR_€"),
         InlineKeyboardButton("🇹🇷 TRY ₺", callback_data=f"{prefix}_TRY_₺")],
        [InlineKeyboardButton("🇮🇳 INR ₹", callback_data=f"{prefix}_INR_₹"),
         InlineKeyboardButton("🇦🇪 AED د.إ", callback_data=f"{prefix}_AED_د.إ")],
        [InlineKeyboardButton("🇦🇺 AUD A$", callback_data=f"{prefix}_AUD_A$"),
         InlineKeyboardButton("🇨🇦 CAD C$", callback_data=f"{prefix}_CAD_C$")],
    ])


def settings_lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
         InlineKeyboardButton("🇪🇸 Español", callback_data="set_lang_es")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="set_lang_fr"),
         InlineKeyboardButton("🇩🇪 Deutsch", callback_data="set_lang_de")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
         InlineKeyboardButton("🇹🇷 Türkçe", callback_data="set_lang_tr")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="set_lang_hi"),
         InlineKeyboardButton("🇮🇹 Italiano", callback_data="set_lang_it")],
        [InlineKeyboardButton("🇵🇹 Português", callback_data="set_lang_pt"),
         InlineKeyboardButton("🇨🇳 中文", callback_data="set_lang_zh")],
    ])


def main_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "main_search"), callback_data="search"),
         InlineKeyboardButton(t(lang, "main_hot"), callback_data="hot")],
        [InlineKeyboardButton(t(lang, "main_alerts"), callback_data="alerts"),
         InlineKeyboardButton(t(lang, "main_hunter"), callback_data="hunter")],
        [InlineKeyboardButton(t(lang, "main_settings"), callback_data="settings"),
         InlineKeyboardButton(t(lang, "main_help"), callback_data="help")],
    ])


def search_type_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "type_flights"), callback_data="stype_flights"),
         InlineKeyboardButton(t(lang, "type_hotels"), callback_data="stype_hotels")],
        [InlineKeyboardButton(t(lang, "type_package"), callback_data="stype_package"),
         InlineKeyboardButton(t(lang, "type_mix"), callback_data="stype_mix")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
    ])


def flex_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "flex_exact"), callback_data="flex_exact"),
         InlineKeyboardButton(t(lang, "flex_weekends"), callback_data="flex_weekends")],
        [InlineKeyboardButton(t(lang, "flex_school"), callback_data="flex_school"),
         InlineKeyboardButton(t(lang, "flex_anytime"), callback_data="flex_anytime")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="search")],
    ])


def weekend_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "wknd_next"), callback_data="wknd_0"),
         InlineKeyboardButton(t(lang, "wknd_2"), callback_data="wknd_1")],
        [InlineKeyboardButton(t(lang, "wknd_3"), callback_data="wknd_2"),
         InlineKeyboardButton(t(lang, "wknd_4"), callback_data="wknd_3")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_flex")],
    ])


def school_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "sch_easter"), callback_data="sch_easter"),
         InlineKeyboardButton(t(lang, "sch_may"), callback_data="sch_may")],
        [InlineKeyboardButton(t(lang, "sch_summer"), callback_data="sch_summer"),
         InlineKeyboardButton(t(lang, "sch_oct"), callback_data="sch_oct")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_flex")],
    ])


def anytime_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "any_1m"), callback_data="any_1m"),
         InlineKeyboardButton(t(lang, "any_3m"), callback_data="any_3m")],
        [InlineKeyboardButton(t(lang, "any_6m"), callback_data="any_6m"),
         InlineKeyboardButton(t(lang, "any_any"), callback_data="any_any")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_flex")],
    ])


def trip_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "trip_return"), callback_data="trip_return"),
         InlineKeyboardButton(t(lang, "trip_oneway"), callback_data="trip_oneway")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_flex")],
    ])


def adults_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(str(i), callback_data=f"adults_{i}") for i in range(1, 5)],
            [InlineKeyboardButton(str(i), callback_data=f"adults_{i}") for i in range(5, 9)]]
    return InlineKeyboardMarkup(rows)


def children_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(str(i), callback_data=f"children_{i}") for i in range(0, 5)],
            [InlineKeyboardButton(str(i), callback_data=f"children_{i}") for i in range(5, 9)]]
    return InlineKeyboardMarkup(rows)


def deal_kb(lang: str, link: str, route_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang, "book_now"), url=link),
        InlineKeyboardButton(t(lang, "alert_me"), callback_data=f"quickalert_{route_key}"),
    ]])


def alerts_list_kb(lang: str, alerts: list) -> InlineKeyboardMarkup:
    rows = []
    for alert in alerts:
        label = t(lang, "pause") if alert["active"] else t(lang, "resume")
        rows.append([
            InlineKeyboardButton(
                f"{'🟢' if alert['active'] else '⚫'} {alert['route'][:28]}",
                callback_data="noop"
            ),
        ])
        rows.append([
            InlineKeyboardButton(label, callback_data=f"toggle_alert_{alert['id']}"),
            InlineKeyboardButton(t(lang, "delete"), callback_data=f"del_alert_{alert['id']}"),
        ])
    rows.append([InlineKeyboardButton(t(lang, "add_new_alert"), callback_data="add_alert")])
    rows.append([InlineKeyboardButton(t(lang, "back"), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def hunter_list_kb(lang: str, hunts: list) -> InlineKeyboardMarkup:
    rows = []
    for hunt in hunts:
        status = t(lang, "hunt_found") if hunt["status"] == "found" else t(lang, "hunt_searching")
        rows.append([InlineKeyboardButton(
            f"{status} {hunt['destination'][:22]}", callback_data="noop"
        )])
        is_paused = hunt["status"] == "paused"
        rows.append([
            InlineKeyboardButton(
                t(lang, "resume_hunt") if is_paused else t(lang, "pause_hunt"),
                callback_data=f"toggle_hunt_{hunt['id']}"
            ),
            InlineKeyboardButton(t(lang, "stop_hunt"), callback_data=f"del_hunt_{hunt['id']}"),
        ])
    rows.append([InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")])
    rows.append([InlineKeyboardButton(t(lang, "back"), callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def settings_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "lang_btn"), callback_data="set_lang"),
         InlineKeyboardButton(t(lang, "curr_btn"), callback_data="set_curr")],
        [InlineKeyboardButton(t(lang, "city_btn"), callback_data="set_city")],
        [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
    ])


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

async def get_lang(uid: int) -> str:
    try:
        return await db.get_user_lang(uid)
    except Exception:
        return "en"


async def get_prefs(uid: int) -> dict:
    try:
        return await db.get_user_prefs(uid)
    except Exception:
        return {"currency": "GBP", "currency_sym": "£", "lang": "en"}


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
            logger.error(f"send deal error: {e}")


async def is_new_user(uid: int) -> bool:
    try:
        prefs = await db.get_user_prefs(uid)
        return prefs.get("home_city", "London") == "London" and prefs.get("currency_sym", "£") == "£"
    except Exception:
        return True


# ── COMMANDS ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        await db.upsert_user(user.id, user.username or "", user.language_code or "en")
    except Exception as e:
        logger.error(f"upsert error: {e}")

    # Always show onboarding on /start so user can reset preferences
    context.user_data["state"] = "ob_lang"
    await update.message.reply_text(
        T["en"]["ob_welcome"],  # Always show in English first
        parse_mode="Markdown",
        reply_markup=lang_kb()
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "help_text"), parse_mode="Markdown", reply_markup=main_kb(lang)
    )


async def cmd_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = await get_lang(uid)
    prefs = await get_prefs(uid)
    sym = prefs.get("currency_sym", "£")
    msg = await update.message.reply_text(t(lang, "hot_scanning"))
    try:
        deals = await scanner.get_hot_deals(limit=5)
        await msg.delete()
        if deals:
            await send_deals(update.message.reply_text, deals, sym, lang)
        else:
            await update.message.reply_text(t(lang, "no_hot"), reply_markup=main_kb(lang))
    except Exception as e:
        logger.error(f"hot error: {e}")
        await msg.edit_text(t(lang, "no_hot"))


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "search_type_prompt"), parse_mode="Markdown",
        reply_markup=search_type_kb(lang)
    )


async def cmd_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = await get_lang(uid)
    try:
        alerts = await db.get_user_alerts(uid)
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
    for a in alerts:
        sym = a.get("currency_sym", "£")
        status = "🟢" if a["active"] else "⚫"
        text += f"{status} *{a['route']}* — {sym}{int(a['budget_pp'])} {t(lang,'pp')}\n"
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=alerts_list_kb(lang, alerts)
    )


async def cmd_hunter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = await get_lang(uid)
    prefs = await get_prefs(uid)
    sym = prefs.get("currency_sym", "£")
    try:
        hunts = await db.get_user_hunts(uid)
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
    for h in hunts:
        status = t(lang, "hunt_found") if h["status"] == "found" else t(lang, "hunt_searching")
        budget = f"{sym}{int(h['budget_pp'])}" if h.get("budget_pp") else t(lang, "hunt_no_limit")
        text += f"{status} *{h['destination']}* — {budget} {t(lang,'pp')}\n"
        if h.get("best_deal"):
            bd = h["best_deal"]
            text += f"   └ {t(lang,'best_deal')}: {sym}{bd.get('price_pp','?')} — {bd.get('route','')}\n"
        text += "\n"
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=hunter_list_kb(lang, hunts)
    )


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "settings_menu"), parse_mode="Markdown", reply_markup=settings_kb(lang)
    )


# ── CALLBACK HANDLER ─────────────────────────────────────────────────────────

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id
    lang = await get_lang(uid)
    prefs = await get_prefs(uid)
    sym = prefs.get("currency_sym", "£")

    if data == "noop":
        return

    # ── ONBOARDING ──
    elif data.startswith("ob_lang_"):
        new_lang = data.replace("ob_lang_", "")
        try:
            await db.set_user_lang(uid, new_lang)
        except Exception as e:
            logger.error(f"set lang error: {e}")
        context.user_data["ob_lang"] = new_lang
        context.user_data["state"] = "ob_curr"
        await query.message.reply_text(
            t(new_lang, "ob_currency"), reply_markup=curr_kb("ob_curr")
        )

    elif data.startswith("ob_curr_"):
        parts = data.split("_", 3)
        if len(parts) == 4:
            curr_code, curr_sym = parts[2], parts[3]
            try:
                await db.set_user_currency(uid, curr_code, curr_sym)
            except Exception as e:
                logger.error(f"set curr error: {e}")
            context.user_data["ob_sym"] = curr_sym
            context.user_data["state"] = "ob_city"
            ob_lang = context.user_data.get("ob_lang", lang)
            await query.message.reply_text(
                t(ob_lang, "ob_city"), parse_mode="Markdown"
            )

    # ── MAIN ──
    elif data == "back_main":
        await query.message.reply_text(
            t(lang, "welcome_back", name=query.from_user.first_name),
            parse_mode="Markdown", reply_markup=main_kb(lang)
        )

    elif data == "help":
        await query.message.reply_text(
            t(lang, "help_text"), parse_mode="Markdown", reply_markup=main_kb(lang)
        )

    # ── HOT ──
    elif data == "hot":
        msg = await query.message.reply_text(t(lang, "hot_scanning"))
        try:
            deals = await scanner.get_hot_deals(limit=5)
            await msg.delete()
            if deals:
                await send_deals(query.message.reply_text, deals, sym, lang)
            else:
                await query.message.reply_text(t(lang, "no_hot"), reply_markup=main_kb(lang))
        except Exception as e:
            logger.error(f"hot btn error: {e}")
            await msg.edit_text(t(lang, "no_hot"))

    # ── SEARCH ──
    elif data == "search":
        context.user_data.pop("search", None)
        await query.message.reply_text(
            t(lang, "search_type_prompt"), parse_mode="Markdown",
            reply_markup=search_type_kb(lang)
        )

    elif data.startswith("stype_"):
        stype = data.replace("stype_", "")
        context.user_data["search"] = {"type": stype}
        context.user_data["state"] = "search_from"
        is_hotel = stype == "hotels"
        prompt_key = "search_from"
        await query.message.reply_text(t(lang, prompt_key), parse_mode="Markdown")

    elif data == "back_flex":
        context.user_data["state"] = "search_flex"
        await query.message.reply_text(t(lang, "search_flex"), reply_markup=flex_kb(lang))

    elif data == "flex_exact":
        context.user_data.setdefault("search", {})["flex"] = "exact"
        stype = context.user_data.get("search", {}).get("type", "flights")
        if stype == "hotels":
            context.user_data["state"] = "search_checkin"
            await query.message.reply_text(t(lang, "search_checkin"), parse_mode="Markdown")
        else:
            context.user_data["state"] = "search_depart"
            await query.message.reply_text(t(lang, "search_depart"), parse_mode="Markdown")

    elif data == "flex_weekends":
        context.user_data.setdefault("search", {})["flex"] = "weekends"
        await query.message.reply_text(t(lang, "weekend_pick"), reply_markup=weekend_kb(lang))

    elif data == "flex_school":
        context.user_data.setdefault("search", {})["flex"] = "school"
        await query.message.reply_text(t(lang, "school_pick"), reply_markup=school_kb(lang))

    elif data == "flex_anytime":
        context.user_data.setdefault("search", {})["flex"] = "anytime"
        await query.message.reply_text(t(lang, "anytime_pick"), reply_markup=anytime_kb(lang))

    elif data.startswith("wknd_"):
        weeks = int(data.replace("wknd_", ""))
        dep, ret = weekend_dates(weeks)
        context.user_data.setdefault("search", {}).update({"dep_date": dep, "ret_date": ret})
        # Go to trip type if flights, otherwise to pax
        stype = context.user_data.get("search", {}).get("type", "flights")
        if stype in ["flights", "mix", "package"]:
            context.user_data["state"] = "search_trip"
            await query.message.reply_text(t(lang, "search_trip"), reply_markup=trip_kb(lang))
        else:
            context.user_data["state"] = "search_adults"
            await query.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif data.startswith("sch_"):
        hol = data.replace("sch_", "")
        dep, ret = school_hol_dates(hol)
        context.user_data.setdefault("search", {}).update({"dep_date": dep, "ret_date": ret})
        stype = context.user_data.get("search", {}).get("type", "flights")
        if stype in ["flights", "mix", "package"]:
            context.user_data["state"] = "search_trip"
            await query.message.reply_text(t(lang, "search_trip"), reply_markup=trip_kb(lang))
        else:
            context.user_data["state"] = "search_adults"
            await query.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif data.startswith("any_"):
        period = data.replace("any_", "")
        today = datetime.now()
        if period == "1m":
            dep = today.strftime("%d/%m/%Y")
            ret = (today + timedelta(days=30)).strftime("%d/%m/%Y")
        elif period == "3m":
            dep = today.strftime("%d/%m/%Y")
            ret = (today + timedelta(days=90)).strftime("%d/%m/%Y")
        elif period == "6m":
            dep = today.strftime("%d/%m/%Y")
            ret = (today + timedelta(days=180)).strftime("%d/%m/%Y")
        else:
            dep = today.strftime("%d/%m/%Y")
            ret = (today + timedelta(days=365)).strftime("%d/%m/%Y")
        context.user_data.setdefault("search", {}).update({"dep_date": dep, "ret_date": ret})
        stype = context.user_data.get("search", {}).get("type", "flights")
        if stype in ["flights", "mix", "package"]:
            context.user_data["state"] = "search_trip"
            await query.message.reply_text(t(lang, "search_trip"), reply_markup=trip_kb(lang))
        else:
            context.user_data["state"] = "search_adults"
            await query.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif data in ["trip_return", "trip_oneway"]:
        context.user_data.setdefault("search", {})["trip"] = data.replace("trip_", "")
        context.user_data["state"] = "search_adults"
        await query.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif data.startswith("adults_"):
        n = int(data.replace("adults_", ""))
        context.user_data.setdefault("search", {})["adults"] = n
        context.user_data["state"] = "search_children"
        await query.message.reply_text(t(lang, "search_children"), reply_markup=children_kb(lang))

    elif data.startswith("children_"):
        n = int(data.replace("children_", ""))
        context.user_data.setdefault("search", {})["children"] = n
        context.user_data["state"] = "search_budget"
        await query.message.reply_text(t(lang, "search_budget"), parse_mode="Markdown")

    # ── ALERTS ──
    elif data == "alerts":
        try:
            alerts = await db.get_user_alerts(uid)
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
            for a in alerts:
                s = a.get("currency_sym", "£")
                status = "🟢" if a["active"] else "⚫"
                text += f"{status} *{a['route']}* — {s}{int(a['budget_pp'])} {t(lang,'pp')}\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=alerts_list_kb(lang, alerts)
            )

    elif data == "add_alert":
        context.user_data["state"] = "alert_route"
        await query.message.reply_text(t(lang, "alert_route_prompt"), parse_mode="Markdown")

    elif data.startswith("quickalert_"):
        route_key = data.replace("quickalert_", "")
        context.user_data["alert_route"] = route_key.replace("-", " → ")
        context.user_data["state"] = "alert_budget"
        await query.message.reply_text(
            t(lang, "alert_budget_prompt", route=route_key.replace("-", " → ")),
            parse_mode="Markdown"
        )

    elif data.startswith("toggle_alert_"):
        aid = int(data.replace("toggle_alert_", ""))
        try:
            await db.toggle_alert(uid, aid)
        except Exception as e:
            logger.error(f"toggle alert: {e}")
        try:
            alerts = await db.get_user_alerts(uid)
            text = t(lang, "your_alerts")
            for a in alerts:
                s = a.get("currency_sym", "£")
                status = "🟢" if a["active"] else "⚫"
                text += f"{status} *{a['route']}* — {s}{int(a['budget_pp'])} {t(lang,'pp')}\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=alerts_list_kb(lang, alerts)
            )
        except Exception as e:
            logger.error(f"refresh alerts: {e}")

    elif data.startswith("del_alert_"):
        aid = int(data.replace("del_alert_", ""))
        try:
            await db.delete_alert(uid, aid)
        except Exception as e:
            logger.error(f"del alert: {e}")
        await query.message.reply_text(t(lang, "alert_deleted"), reply_markup=main_kb(lang))

    # ── HUNTER ──
    elif data == "hunter":
        try:
            hunts = await db.get_user_hunts(uid)
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
            for h in hunts:
                status = t(lang, "hunt_found") if h["status"] == "found" else t(lang, "hunt_searching")
                budget = f"{sym}{int(h['budget_pp'])}" if h.get("budget_pp") else t(lang, "hunt_no_limit")
                text += f"{status} *{h['destination']}* — {budget} {t(lang,'pp')}\n"
                if h.get("best_deal"):
                    bd = h["best_deal"]
                    text += f"   └ {t(lang,'best_deal')}: {sym}{bd.get('price_pp','?')} — {bd.get('route','')}\n"
                text += "\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=hunter_list_kb(lang, hunts)
            )

    elif data == "new_hunt":
        context.user_data["state"] = "hunt_dest"
        await query.message.reply_text(t(lang, "hunt_dest_prompt"), parse_mode="Markdown")

    elif data.startswith("toggle_hunt_"):
        hid = int(data.replace("toggle_hunt_", ""))
        try:
            await db.toggle_hunt(uid, hid)
        except Exception as e:
            logger.error(f"toggle hunt: {e}")
        try:
            hunts = await db.get_user_hunts(uid)
            text = t(lang, "your_hunts")
            for h in hunts:
                status = t(lang, "hunt_found") if h["status"] == "found" else t(lang, "hunt_searching")
                budget = f"{sym}{int(h['budget_pp'])}" if h.get("budget_pp") else t(lang, "hunt_no_limit")
                text += f"{status} *{h['destination']}* — {budget} {t(lang,'pp')}\n"
                text += "\n"
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=hunter_list_kb(lang, hunts)
            )
        except Exception as e:
            logger.error(f"refresh hunts: {e}")

    elif data.startswith("del_hunt_"):
        hid = int(data.replace("del_hunt_", ""))
        try:
            await db.delete_hunt(uid, hid)
        except Exception as e:
            logger.error(f"del hunt: {e}")
        await query.message.reply_text(t(lang, "no_hunter"), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "start_hunt"), callback_data="new_hunt")],
                [InlineKeyboardButton(t(lang, "back"), callback_data="back_main")],
            ])
        )

    # ── SETTINGS ──
    elif data == "settings":
        await query.message.reply_text(
            t(lang, "settings_menu"), parse_mode="Markdown", reply_markup=settings_kb(lang)
        )

    elif data == "set_lang":
        await query.message.reply_text(t(lang, "lang_prompt"), reply_markup=settings_lang_kb())

    elif data.startswith("set_lang_"):
        new_lang = data.replace("set_lang_", "")
        try:
            await db.set_user_lang(uid, new_lang)
        except Exception as e:
            logger.error(f"set lang: {e}")
        await query.message.reply_text(
            t(new_lang, "lang_set"), reply_markup=main_kb(new_lang)
        )

    elif data == "set_curr":
        await query.message.reply_text(t(lang, "curr_prompt"), reply_markup=curr_kb("set_curr"))

    elif data.startswith("set_curr_"):
        parts = data.split("_", 3)
        if len(parts) == 4:
            curr_code, curr_sym = parts[2], parts[3]
            try:
                await db.set_user_currency(uid, curr_code, curr_sym)
            except Exception as e:
                logger.error(f"set curr: {e}")
            await query.message.reply_text(
                t(lang, "curr_set", sym=curr_sym), reply_markup=main_kb(lang)
            )

    elif data == "set_city":
        context.user_data["state"] = "settings_city"
        await query.message.reply_text(t(lang, "city_prompt"), parse_mode="Markdown")


# ── MESSAGE HANDLER ───────────────────────────────────────────────────────────

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    state = context.user_data.get("state", "")
    lang = await get_lang(uid)
    prefs = await get_prefs(uid)
    sym = prefs.get("currency_sym", "£")

    # ── ONBOARDING ──
    if state == "ob_city":
        context.user_data["state"] = None
        ob_lang = context.user_data.get("ob_lang", lang)
        try:
            await db.set_user_city(uid, text)
        except Exception as e:
            logger.error(f"set city ob: {e}")
        await update.message.reply_text(
            t(ob_lang, "ob_city_set", city=text),
            parse_mode="Markdown",
            reply_markup=main_kb(ob_lang)
        )

    # ── SEARCH FLOW ──
    elif state == "search_from":
        context.user_data.setdefault("search", {})["from"] = text
        context.user_data["state"] = "search_to"
        await update.message.reply_text(t(lang, "search_to"), parse_mode="Markdown")

    elif state == "search_to":
        context.user_data.setdefault("search", {})["to"] = text
        context.user_data["state"] = "search_flex"
        await update.message.reply_text(t(lang, "search_flex"), reply_markup=flex_kb(lang))

    elif state == "search_depart":
        parsed = parse_date(text)
        if not parsed:
            await update.message.reply_text(t(lang, "invalid_date"), parse_mode="Markdown")
            return
        context.user_data.setdefault("search", {})["dep_date"] = text
        stype = context.user_data.get("search", {}).get("type", "flights")
        if stype in ["flights", "mix", "package"]:
            context.user_data["state"] = "search_return"
            await update.message.reply_text(t(lang, "search_return"), parse_mode="Markdown")
        else:
            context.user_data["state"] = "search_adults"
            await update.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif state == "search_return":
        lower = text.lower()
        if lower in ["oneway", "one-way", "single", "soloida", "tekyön", "ذهاب فقط", "单程", "soida", "solo"]:
            context.user_data.setdefault("search", {})["trip"] = "oneway"
            context.user_data["state"] = "search_adults"
            await update.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))
        else:
            parsed = parse_date(text)
            if not parsed:
                await update.message.reply_text(t(lang, "invalid_date"), parse_mode="Markdown")
                return
            context.user_data.setdefault("search", {})["ret_date"] = text
            context.user_data.setdefault("search", {})["trip"] = "return"
            context.user_data["state"] = "search_adults"
            await update.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif state == "search_checkin":
        parsed = parse_date(text)
        if not parsed:
            await update.message.reply_text(t(lang, "invalid_date"), parse_mode="Markdown")
            return
        context.user_data.setdefault("search", {})["dep_date"] = text
        context.user_data["state"] = "search_checkout"
        await update.message.reply_text(t(lang, "search_checkout"), parse_mode="Markdown")

    elif state == "search_checkout":
        parsed = parse_date(text)
        if not parsed:
            await update.message.reply_text(t(lang, "invalid_date"), parse_mode="Markdown")
            return
        context.user_data.setdefault("search", {})["ret_date"] = text
        context.user_data["state"] = "search_adults"
        await update.message.reply_text(t(lang, "search_adults"), reply_markup=adults_kb(lang))

    elif state == "search_budget":
        context.user_data["state"] = None
        search = context.user_data.get("search", {})
        lower = text.lower()
        budget = 9999.0
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        if lower not in ["any", "sin límite", "illimité", "unbegrenzt", "بلا حد",
                         "sınırsız", "कोई सीमा नहीं", "illimitato", "sem limite", "无限制"]:
            try:
                budget = float(clean)
            except ValueError:
                pass

        origin = search.get("from", prefs.get("home_city", "London"))
        dest = search.get("to", "anywhere")
        adults = search.get("adults", 2)
        children = search.get("children", 0)
        dep = search.get("dep_date", "")
        ret = search.get("ret_date", "")
        stype = search.get("type", "mix")

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
            logger.error(f"search budget error: {e}")
            await msg.edit_text(t(lang, "no_deals"))

    # ── ALERT FLOW ──
    elif state == "alert_route":
        context.user_data["alert_route"] = text
        context.user_data["state"] = "alert_budget"
        await update.message.reply_text(
            t(lang, "alert_budget_prompt", route=text), parse_mode="Markdown"
        )

    elif state == "alert_budget":
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        try:
            budget = float(clean)
            route = context.user_data.get("alert_route", "")
            context.user_data["state"] = None
            await db.create_alert(uid, route, budget, prefs.get("currency","GBP"), sym)
            await update.message.reply_text(
                t(lang, "alert_set", route=route, sym=sym, budget=int(budget)),
                parse_mode="Markdown", reply_markup=main_kb(lang)
            )
        except (ValueError, Exception) as e:
            logger.error(f"create alert: {e}")
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")

    # ── HUNTER FLOW ──
    elif state == "hunt_dest":
        context.user_data["hunt_dest"] = text
        context.user_data["state"] = "hunt_budget"
        await update.message.reply_text(
            t(lang, "hunt_budget_prompt", dest=text), parse_mode="Markdown"
        )

    elif state == "hunt_budget":
        clean = text.replace("£","").replace("$","").replace("€","").replace(",","").strip()
        try:
            budget = float(clean)
            dest = context.user_data.get("hunt_dest", "Anywhere")
            context.user_data["state"] = None
            await db.create_hunt(uid, dest, budget, prefs.get("currency","GBP"), sym)
            budget_display = int(budget) if budget > 0 else t(lang, "hunt_no_limit")
            sym_d = sym if budget > 0 else ""
            await update.message.reply_text(
                t(lang, "hunt_started", dest=dest, sym=sym_d, budget=budget_display),
                parse_mode="Markdown", reply_markup=main_kb(lang)
            )
        except (ValueError, Exception) as e:
            logger.error(f"create hunt: {e}")
            await update.message.reply_text(t(lang, "invalid_budget"), parse_mode="Markdown")

    # ── SETTINGS CITY ──
    elif state == "settings_city":
        context.user_data["state"] = None
        try:
            await db.set_user_city(uid, text)
        except Exception as e:
            logger.error(f"set city: {e}")
        await update.message.reply_text(
            t(lang, "city_set", city=text), parse_mode="Markdown",
            reply_markup=main_kb(lang)
        )

    # ── DEFAULT ──
    else:
        msg = await update.message.reply_text(
            t(lang, "searching", query=text), parse_mode="Markdown"
        )
        try:
            deals = await scanner.search(text, budget_pp=9999)
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
            logger.error(f"default msg: {e}")
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
    logger.info("🚀 Fairo bot v3 starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
