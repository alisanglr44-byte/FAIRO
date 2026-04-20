"""
DealScanner — fetches flights via Sky Scrapper API and hotels via Booking.com API
Both on RapidAPI with a single key.

Sky Scrapper: https://rapidapi.com/apiheya/api/sky-scrapper
Booking.com:  https://rapidapi.com/DataCrawler/api/booking-com15
"""
import asyncio
import aiohttp
import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

SKYSCRAPPER_HOST = "sky-scrapper.p.rapidapi.com"
BOOKING_HOST = "booking-com15.p.rapidapi.com"


class DealScanner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get(self, url: str, params: dict, host: str) -> dict:
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": host,
        }
        session = await self._get_session()
        try:
            async with session.get(
                url, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                text = await r.text()
                if r.status == 200:
                    import json
                    try:
                        return json.loads(text)
                    except Exception:
                        logger.error(f"JSON parse error from {host}: {text[:200]}")
                        return {}
                else:
                    logger.warning(f"API {r.status} from {host} {url}: {text[:200]}")
                    return {}
        except Exception as e:
            logger.error(f"Request failed {url}: {e}")
            return {}

    # ── AIRPORT LOOKUP ────────────────────────────────────────────────────────

    # Known IATA → Sky Scrapper entity ID map (expand as needed)
    KNOWN_AIRPORTS = {
        "LHR": "95565050", "LGW": "95565044", "MAN": "95565056",
        "STN": "95565067", "LTN": "95565052", "BHX": "95565038",
        "EDI": "95565043", "GLA": "95565045", "BRS": "95565039",
        "DXB": "95673691", "TFS": "95565118", "BCN": "95565072",
        "LIS": "95565088", "AGP": "95565069", "AYT": "95565077",
        "FAO": "95565085", "PMI": "95565103", "JFK": "95565058",
        "CDG": "95565079", "AMS": "95565070", "FCO": "95565086",
        "MAD": "95565092", "ATH": "95565074", "DUB": "95565042",
        "CPH": "95565080", "VIE": "95565096", "ZRH": "95565099",
        "PRG": "95565093", "BUD": "95565073", "WAW": "95565097",
        "IST": "95565087", "CAI": "95565078", "CMN": "95565081",
        "DEL": "95565041", "BOM": "95565040", "BKK": "95565076",
        "SIN": "95565094", "KUL": "95565089", "HKG": "95565046",
        "SYD": "95565095", "MEL": "95565091", "JNB": "95565048",
        "NBO": "95565092", "CPT": "95565038",
    }

    # City name → IATA code map for natural language searches
    CITY_TO_IATA = {
        "london": "LHR", "manchester": "MAN", "birmingham": "BHX",
        "edinburgh": "EDI", "glasgow": "GLA", "bristol": "BRS",
        "dubai": "DXB", "tenerife": "TFS", "barcelona": "BCN",
        "lisbon": "LIS", "malaga": "AGP", "antalya": "AYT",
        "faro": "FAO", "majorca": "PMI", "mallorca": "PMI",
        "new york": "JFK", "paris": "CDG", "amsterdam": "AMS",
        "rome": "FCO", "madrid": "MAD", "athens": "ATH",
        "dublin": "DUB", "istanbul": "IST", "cairo": "CAI",
        "delhi": "DEL", "mumbai": "BOM", "bangkok": "BKK",
        "singapore": "SIN", "kuala lumpur": "KUL", "hong kong": "HKG",
        "sydney": "SYD", "melbourne": "MEL", "johannesburg": "JNB",
        "nairobi": "NBO", "cape town": "CPT", "vienna": "VIE",
        "zurich": "ZRH", "prague": "PRG", "budapest": "BUD",
        "warsaw": "WAW", "copenhagen": "CPH", "costa rica": "SJO",
        "cancun": "CUN", "miami": "MIA", "los angeles": "LAX",
        "toronto": "YYZ", "tokyo": "NRT", "bali": "DPS",
        "maldives": "MLE", "doha": "DOH", "abu dhabi": "AUH",
        "marrakech": "RAK", "casablanca": "CMN",
    }

    def _city_to_iata(self, text: str) -> str:
        """Convert city name or IATA to IATA code."""
        text = text.strip()
        # Already a 3-letter IATA code
        if len(text) == 3 and text.upper() in self.KNOWN_AIRPORTS:
            return text.upper()
        # Try city lookup
        lower = text.lower()
        if lower in self.CITY_TO_IATA:
            return self.CITY_TO_IATA[lower]
        # Try partial match
        for city, iata in self.CITY_TO_IATA.items():
            if city in lower or lower in city:
                return iata
        # Return as-is (3 chars) or LHR default
        return text.upper()[:3] if len(text) >= 3 else "LHR"

    async def _get_airport_entity_id(self, iata: str) -> str:
        """Get Sky Scrapper entity ID for an IATA code."""
        iata = iata.upper()
        if iata in self.KNOWN_AIRPORTS:
            return self.KNOWN_AIRPORTS[iata]
        # API lookup fallback
        data = await self._get(
            f"https://{SKYSCRAPPER_HOST}/api/v1/flights/searchAirport",
            {"query": iata, "locale": "en-GB"},
            SKYSCRAPPER_HOST
        )
        places = data.get("data", [])
        if places:
            eid = places[0].get("entityId", "")
            logger.info(f"Resolved {iata} → entityId {eid}")
            return eid
        logger.warning(f"Could not resolve entityId for {iata}")
        return ""

    # ── FLIGHTS ───────────────────────────────────────────────────────────────

    async def search_flights(
        self,
        origin_iata: str,
        dest_iata: str,
        dep_date: str,       # YYYY-MM-DD
        ret_date: Optional[str] = None,
        adults: int = 2,
        currency: str = "GBP",
    ) -> list[dict]:

        origin_eid = await self._get_airport_entity_id(origin_iata)
        if not origin_eid:
            logger.warning(f"No entityId for origin {origin_iata}")
            return []

        dest_eid = ""
        if dest_iata.lower() not in ["anywhere", "any", ""]:
            dest_eid = await self._get_airport_entity_id(dest_iata)

        params = {
            "originSkyId": origin_iata,
            "destinationSkyId": dest_iata if dest_iata.lower() != "anywhere" else "anywhere",
            "originEntityId": origin_eid,
            "destinationEntityId": dest_eid,
            "date": dep_date,
            "adults": str(adults),
            "currency": currency,
            "market": "UK",
            "countryCode": "GB",
            "cabinClass": "economy",
            "sortBy": "best",
        }
        if ret_date:
            params["returnDate"] = ret_date

        url = f"https://{SKYSCRAPPER_HOST}/api/v2/flights/searchFlights"
        logger.info(f"Searching flights {origin_iata}→{dest_iata} {dep_date}")
        data = await self._get(url, params, SKYSCRAPPER_HOST)

        return self._parse_flights(data, origin_iata, dest_iata, dep_date, ret_date, currency)

    def _parse_flights(self, data: dict, origin: str, dest: str, dep_date: str, ret_date: Optional[str], currency: str) -> list[dict]:
        if not data:
            logger.warning(f"No data returned for {origin}→{dest}")
            return []

        itineraries = data.get("data", {}).get("itineraries", [])
        logger.info(f"Parsing {len(itineraries)} itineraries for {origin}→{dest}")

        results = []
        for it in itineraries[:20]:
            try:
                price_raw = it.get("price", {}).get("raw", 0)
                legs = it.get("legs", [])
                if not legs or not price_raw:
                    continue

                leg = legs[0]
                carriers = leg.get("carriers", {}).get("marketing", [{}])
                airline = carriers[0].get("name", "Airline") if carriers else "Airline"
                duration_mins = leg.get("durationInMinutes", 0)
                hours = duration_mins // 60
                mins = duration_mins % 60
                duration = f"{hours}h {mins}m" if hours else f"{mins}m"
                stops = leg.get("stopCount", 0)
                stop_label = "Direct ✈️" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"

                # Parse actual departure date from leg
                dep_display = dep_date
                try:
                    dep_str = leg.get("departure", dep_date)[:10]
                    dep_dt = datetime.fromisoformat(dep_str)
                    dep_display = dep_dt.strftime("%a %d %b %Y")
                except Exception:
                    pass

                ret_display = ""
                if ret_date and len(legs) > 1:
                    try:
                        ret_str = legs[1].get("departure", ret_date)[:10]
                        ret_dt = datetime.fromisoformat(ret_str)
                        ret_display = ret_dt.strftime("%a %d %b %Y")
                    except Exception:
                        ret_display = ret_date

                # Estimate "was" price — realistic 20-35% above current
                markup = random.uniform(1.20, 1.35)
                was_price = round(price_raw * markup, 2)
                saving_pct = int((1 - price_raw / was_price) * 100)

                # Label based on absolute price
                if price_raw < 50:
                    deal_label = "🚨 Error fare"
                elif price_raw < 120:
                    deal_label = "⚡ Flash sale"
                elif saving_pct >= 20:
                    deal_label = "🏷 Great deal"
                else:
                    deal_label = "✈️ Best price"

                results.append({
                    "type": "flight",
                    "route": f"{origin} → {dest}",
                    "route_key": f"{origin}-{dest}",
                    "airline": airline,
                    "duration": f"{duration} • {stop_label}",
                    "dep_date": dep_display,
                    "ret_date": ret_display,
                    "price_pp": round(price_raw, 2),
                    "was_pp": round(was_price, 2),
                    "saving_pct": saving_pct,
                    "deal_label": deal_label,
                    "seats_left": 20,
                    "currency": currency,
                    "affiliate_link": self._flight_link(origin, dest, dep_date, ret_date),
                })
            except Exception as e:
                logger.debug(f"Parse error on itinerary: {e}")
                continue

        # Sort cheapest first
        results.sort(key=lambda x: x["price_pp"])
        logger.info(f"Returning {len(results)} flights for {origin}→{dest}")
        return results

    def _flight_link(self, origin: str, dest: str, dep_date: str, ret_date: Optional[str]) -> str:
        marker = Config.TRAVELPAYOUTS_MARKER
        if marker:
            d = dep_date.replace("-", "")
            r = ret_date.replace("-", "") if ret_date else ""
            return f"https://www.aviasales.com/search/{origin}{d}{dest}{r}2?marker={marker}"
        dep = dep_date.replace("-", "")
        return f"https://www.skyscanner.net/transport/flights/{origin.lower()}/{dest.lower()}/{dep}/?adults=2"

    # ── HOTELS ────────────────────────────────────────────────────────────────

    async def search_hotels(
        self,
        city: str,
        checkin: str,
        checkout: str,
        adults: int = 2,
        currency: str = "GBP",
    ) -> list[dict]:

        dest_data = await self._get(
            f"https://{BOOKING_HOST}/api/v1/hotels/searchDestination",
            {"query": city},
            BOOKING_HOST
        )
        dest_list = dest_data.get("data", [])
        if not dest_list:
            logger.warning(f"No hotel destination found for {city}")
            return []

        dest_id = dest_list[0].get("dest_id", "")
        dest_type = dest_list[0].get("dest_type", "city")

        params = {
            "dest_id": dest_id,
            "search_type": dest_type,
            "arrival_date": checkin,
            "departure_date": checkout,
            "adults": str(adults),
            "currency_code": currency,
            "languagecode": "en-gb",
            "room_number": "1",
            "units": "metric",
        }
        data = await self._get(
            f"https://{BOOKING_HOST}/api/v2/hotels/searchHotels",
            params, BOOKING_HOST
        )
        return self._parse_hotels(data, city, checkin, checkout, currency)

    def _parse_hotels(self, data: dict, city: str, checkin: str, checkout: str, currency: str) -> list[dict]:
        hotels = data.get("data", {}).get("hotels", [])
        logger.info(f"Parsing {len(hotels)} hotels for {city}")

        try:
            checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_dt = datetime.strptime(checkout, "%Y-%m-%d")
            nights = (checkout_dt - checkin_dt).days
        except Exception:
            nights = 7

        results = []
        for h in hotels[:20]:
            try:
                prop = h.get("property", {})
                price_info = h.get("priceBreakdown", {}).get("grossPrice", {})
                price = float(price_info.get("value", 0))
                if not price:
                    continue

                name = prop.get("name", "Hotel")
                stars = int(prop.get("propertyClass", 0))
                hotel_id = prop.get("id", "")

                markup = random.uniform(1.20, 1.50)
                was_price = round(price * markup, 2)
                saving_pct = int((1 - price / was_price) * 100)
                price_pp = round(price / max(2, 1), 2)
                was_pp = round(was_price / max(2, 1), 2)

                deal_label = "⚡ Flash sale" if saving_pct >= 30 else "🏨 Best price"

                results.append({
                    "type": "hotel",
                    "name": name,
                    "city": city,
                    "route": f"{city} · {name[:30]}",
                    "route_key": f"hotel-{city.lower().replace(' ','-')}",
                    "stars": stars,
                    "dep_date": checkin,
                    "ret_date": checkout,
                    "nights": nights,
                    "price_pp": price_pp,
                    "was_pp": was_pp,
                    "saving_pct": saving_pct,
                    "deal_label": deal_label,
                    "currency": currency,
                    "affiliate_link": self._hotel_link(hotel_id, checkin, checkout),
                })
            except Exception as e:
                logger.debug(f"Hotel parse error: {e}")
                continue

        results.sort(key=lambda x: x["price_pp"])
        return results

    def _hotel_link(self, hotel_id: str, checkin: str, checkout: str) -> str:
        aff_id = Config.BOOKING_AFFILIATE_ID
        base = f"https://www.booking.com/hotel/gb/{hotel_id}.html?checkin={checkin}&checkout={checkout}&group_adults=2"
        if aff_id:
            base += f"&aid={aff_id}"
        return base

    # ── HOT DEALS ─────────────────────────────────────────────────────────────

    async def get_hot_deals(self, limit: int = 10) -> list[dict]:
        """Scan home routes and return results — no threshold filter."""
        today = datetime.now()

        # Get next 4 Fridays
        dates = []
        for i in range(1, 60):
            d = today + timedelta(days=i)
            if d.weekday() == 4:  # Friday
                dep = d.strftime("%Y-%m-%d")
                ret = (d + timedelta(days=9)).strftime("%Y-%m-%d")
                dates.append((dep, ret))
                if len(dates) >= 4:
                    break

        # Search top routes concurrently
        tasks = []
        for origin, dest in Config.HOT_ROUTES[:4]:
            if dates:
                dep, ret = dates[0]
                tasks.append(self.search_flights(origin, dest, dep, ret))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_deals = []
        for r in results:
            if isinstance(r, list):
                all_deals.extend(r)

        # Deduplicate by route, cheapest per route
        seen = {}
        for deal in all_deals:
            key = deal["route_key"]
            if key not in seen or deal["price_pp"] < seen[key]["price_pp"]:
                seen[key] = deal

        deduped = sorted(seen.values(), key=lambda x: x["price_pp"])
        return deduped[:limit]

    # ── SEARCH ────────────────────────────────────────────────────────────────

    async def search(self, query: str, budget_pp: float = 9999, dep_date: str = "", ret_date: str = "", adults: int = 2) -> list[dict]:
        """Parse query and search for flights."""
        query = query.strip()

        # Parse origin and destination
        origin_iata = "LHR"
        dest_iata = ""

        for sep in [" to ", " → ", " -> ", "→", " - "]:
            if sep in query:
                idx = query.index(sep)
                left = query[:idx].strip()
                right = query[idx + len(sep):].strip()
                origin_iata = self._city_to_iata(left)
                dest_iata = self._city_to_iata(right)
                break

        if not dest_iata:
            dest_iata = self._city_to_iata(query)

        # Default dates: 3 weeks from now, 1 week stay
        today = datetime.now()
        if not dep_date:
            dep_date = (today + timedelta(days=21)).strftime("%Y-%m-%d")
        if not ret_date:
            ret_date = (today + timedelta(days=28)).strftime("%Y-%m-%d")

        logger.info(f"Search: {origin_iata}→{dest_iata} dep={dep_date} ret={ret_date} adults={adults} budget={budget_pp}")
        deals = await self.search_flights(origin_iata, dest_iata, dep_date, ret_date, adults=adults)

        if budget_pp < 9999:
            deals = [d for d in deals if d["price_pp"] <= budget_pp]

        return deals

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
