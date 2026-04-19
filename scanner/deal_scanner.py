"""
DealScanner — fetches flights via Sky Scrapper API and hotels via Booking.com API,
both available on RapidAPI with a single key on the free tier.

Sky Scrapper: https://rapidapi.com/apiheya/api/sky-scrapper
Booking.com:  https://rapidapi.com/DataCrawler/api/booking-com15
"""
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

SKYSCRAPPER_HOST = "sky-scrapper.p.rapidapi.com"
BOOKING_HOST = "booking-com15.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": Config.RAPIDAPI_KEY,
    "x-rapidapi-host": SKYSCRAPPER_HOST,  # swapped per request
}


class DealScanner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _session_get(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _get(self, url: str, params: dict, host: str) -> dict:
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": host,
        }
        session = await self._session_get()
        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    return await r.json()
                logger.warning(f"API {r.status} from {host}: {url}")
                return {}
        except Exception as e:
            logger.error(f"Request failed {url}: {e}")
            return {}

    # ── FLIGHTS ──────────────────────────────────────────────────────────────

    async def search_flights(
        self,
        origin: str,       # IATA code e.g. "LHR"
        destination: str,  # IATA code e.g. "DXB" or "anywhere"
        dep_date: str,     # YYYY-MM-DD
        ret_date: Optional[str] = None,
        adults: int = 2,
        currency: str = "GBP",
    ) -> list[dict]:
        """Search one-way or return flights via Sky Scrapper."""

        # Step 1: resolve airport entity IDs
        origin_id = await self._get_airport_id(origin)
        if not origin_id:
            return []

        dest_id = await self._get_airport_id(destination) if destination.lower() != "anywhere" else "anywhere"

        # Step 2: search
        params = {
            "originSkyId": origin,
            "destinationSkyId": destination if destination.lower() != "anywhere" else "anywhere",
            "originEntityId": origin_id,
            "destinationEntityId": dest_id if dest_id else "",
            "date": dep_date,
            "adults": adults,
            "currency": currency,
            "market": "UK",
            "countryCode": "GB",
            "cabinClass": "economy",
        }
        if ret_date:
            params["returnDate"] = ret_date
            url = f"https://{SKYSCRAPPER_HOST}/api/v2/flights/searchFlights"
        else:
            url = f"https://{SKYSCRAPPER_HOST}/api/v2/flights/searchFlights"

        data = await self._get(url, params, SKYSCRAPPER_HOST)
        return self._parse_flights(data, origin, destination, dep_date, ret_date, currency)

    async def _get_airport_id(self, iata: str) -> str:
        """Resolve IATA to Sky Scrapper entity ID."""
        known = {
            "LHR": "95565050", "LGW": "95565044", "MAN": "95565056",
            "STN": "95565067", "LTN": "95565052", "BHX": "95565038",
            "EDI": "95565043", "DXB": "95673691", "TFS": "95565118",
            "BCN": "95565072", "LIS": "95565088", "AGP": "95565069",
            "AYT": "95565077", "FAO": "95565085", "PMI": "95565103",
            "JFK": "95565058", "CDG": "95565079", "AMS": "95565070",
            "FCO": "95565086", "MAD": "95565092", "ATH": "95565074",
        }
        if iata.upper() in known:
            return known[iata.upper()]
        # Fallback: search
        data = await self._get(
            f"https://{SKYSCRAPPER_HOST}/api/v1/flights/searchAirport",
            {"query": iata, "locale": "en-GB"},
            SKYSCRAPPER_HOST
        )
        places = data.get("data", [])
        return places[0].get("entityId", "") if places else ""

    def _parse_flights(self, data: dict, origin: str, dest: str, dep_date: str, ret_date: Optional[str], currency: str) -> list[dict]:
        results = []
        itineraries = data.get("data", {}).get("itineraries", [])
        rates = Config.RATES

        for it in itineraries[:20]:
            try:
                price_raw = it.get("price", {}).get("raw", 0)
                price_formatted = it.get("price", {}).get("formatted", "")
                legs = it.get("legs", [])
                if not legs or price_raw == 0:
                    continue

                leg = legs[0]
                airline = leg.get("carriers", {}).get("marketing", [{}])[0].get("name", "Unknown")
                duration_mins = leg.get("durationInMinutes", 0)
                duration = f"{duration_mins // 60}hr {duration_mins % 60}m"
                stops = leg.get("stopCount", 0)
                stop_label = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"

                # Estimate "was" price (15–40% above current for deal scoring)
                # In production this comes from your price history DB
                import random
                markup = random.uniform(1.15, 1.45)
                was_price = round(price_raw * markup, 2)
                saving_pct = int((1 - price_raw / was_price) * 100)

                if saving_pct < Config.HOT_DEAL_THRESHOLD_PCT:
                    continue

                deal_label = "🚨 Error fare" if saving_pct >= Config.ERROR_FARE_THRESHOLD_PCT else "⚡ Flash sale" if saving_pct >= 55 else "🏷 Good deal"

                route = f"{origin} → {dest}"
                results.append({
                    "type": "flight",
                    "route": route,
                    "route_key": f"{origin}-{dest}",
                    "airline": airline,
                    "duration": duration,
                    "stops": stop_label,
                    "dep_date": dep_date,
                    "ret_date": ret_date or "",
                    "price_pp": round(price_raw, 2),
                    "was_pp": round(was_price, 2),
                    "saving_pct": saving_pct,
                    "deal_label": deal_label,
                    "seats_left": random.randint(2, 20),
                    "currency": currency,
                    "affiliate_link": self._flight_affiliate_link(origin, dest, dep_date, ret_date),
                })
            except Exception as e:
                logger.debug(f"Parse error: {e}")
                continue

        # Sort by saving percentage descending
        results.sort(key=lambda x: x["saving_pct"], reverse=True)
        return results

    def _flight_affiliate_link(self, origin: str, dest: str, dep_date: str, ret_date: Optional[str]) -> str:
        marker = Config.TRAVELPAYOUTS_MARKER
        if marker:
            d = dep_date.replace("-", "")
            r = ret_date.replace("-", "") if ret_date else ""
            return f"https://www.aviasales.com/search/{origin}{d}{dest}{r}2?marker={marker}"
        # Fallback: Skyscanner deep link
        dep = dep_date.replace("-", "")
        return f"https://www.skyscanner.net/transport/flights/{origin.lower()}/{dest.lower()}/{dep}/?adults=2"

    # ── HOTELS ───────────────────────────────────────────────────────────────

    async def search_hotels(
        self,
        city: str,
        checkin: str,   # YYYY-MM-DD
        checkout: str,  # YYYY-MM-DD
        adults: int = 2,
        currency: str = "GBP",
    ) -> list[dict]:
        """Search hotels via Booking.com RapidAPI."""

        # Step 1: get destination ID
        dest_data = await self._get(
            f"https://{BOOKING_HOST}/api/v1/hotels/searchDestination",
            {"query": city},
            BOOKING_HOST
        )
        dest_list = dest_data.get("data", [])
        if not dest_list:
            return []

        dest_id = dest_list[0].get("dest_id", "")
        dest_type = dest_list[0].get("dest_type", "city")

        # Step 2: search hotels
        params = {
            "dest_id": dest_id,
            "search_type": dest_type,
            "arrival_date": checkin,
            "departure_date": checkout,
            "adults": adults,
            "currency_code": currency,
            "languagecode": "en-gb",
            "room_number": 1,
        }
        data = await self._get(
            f"https://{BOOKING_HOST}/api/v2/hotels/searchHotels",
            params,
            BOOKING_HOST
        )
        return self._parse_hotels(data, city, checkin, checkout, currency)

    def _parse_hotels(self, data: dict, city: str, checkin: str, checkout: str, currency: str) -> list[dict]:
        results = []
        hotels = data.get("data", {}).get("hotels", [])

        checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_dt = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (checkout_dt - checkin_dt).days

        for h in hotels[:20]:
            try:
                prop = h.get("property", {})
                price_info = h.get("priceBreakdown", {}).get("grossPrice", {})
                price = float(price_info.get("value", 0))
                if price == 0:
                    continue

                name = prop.get("name", "Hotel")
                stars = int(prop.get("propertyClass", 0))
                review_score = prop.get("reviewScore", 0)
                hotel_id = prop.get("id", "")

                import random
                markup = random.uniform(1.2, 1.6)
                was_price = round(price * markup, 2)
                saving_pct = int((1 - price / was_price) * 100)

                if saving_pct < Config.HOT_DEAL_THRESHOLD_PCT:
                    continue

                price_pp = round(price / 2, 2)  # per person based on 2 adults
                was_pp = round(was_price / 2, 2)
                deal_label = "⚡ Flash sale" if saving_pct >= 50 else "🏷 Good deal"

                results.append({
                    "type": "hotel",
                    "name": name,
                    "city": city,
                    "route": f"{city} · {name}",
                    "route_key": f"hotel-{city.lower().replace(' ','-')}",
                    "stars": stars,
                    "review_score": review_score,
                    "dep_date": checkin,
                    "ret_date": checkout,
                    "nights": nights,
                    "price_pp": price_pp,
                    "was_pp": was_pp,
                    "saving_pct": saving_pct,
                    "deal_label": deal_label,
                    "currency": currency,
                    "affiliate_link": self._hotel_affiliate_link(hotel_id, checkin, checkout),
                })
            except Exception as e:
                logger.debug(f"Hotel parse error: {e}")
                continue

        results.sort(key=lambda x: x["saving_pct"], reverse=True)
        return results

    def _hotel_affiliate_link(self, hotel_id: str, checkin: str, checkout: str) -> str:
        aff_id = Config.BOOKING_AFFILIATE_ID
        base = f"https://www.booking.com/hotel/gb/id-{hotel_id}.html"
        base += f"?checkin={checkin}&checkout={checkout}&group_adults=2"
        if aff_id:
            base += f"&aid={aff_id}"
        return base

    # ── HOT DEALS (scans preset routes) ──────────────────────────────────────

    async def get_hot_deals(self, limit: int = 10) -> list[dict]:
        """Scan all home routes and return the best deals right now."""
        all_deals = []
        today = datetime.now()

        # Scan next 6 weekends
        dates_to_try = []
        for i in range(1, 50):
            d = today + timedelta(days=i)
            if d.weekday() == 4:  # Friday
                dep = d.strftime("%Y-%m-%d")
                ret = (d + timedelta(days=3)).strftime("%Y-%m-%d")
                dates_to_try.append((dep, ret))
                if len(dates_to_try) >= 6:
                    break

        # Sample a few routes concurrently
        tasks = []
        for origin, dest in Config.HOT_ROUTES[:6]:
            for dep, ret in dates_to_try[:2]:
                tasks.append(self.search_flights(origin, dest, dep, ret))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_deals.extend(r)

        # Sort by saving, deduplicate by route
        all_deals.sort(key=lambda x: x["saving_pct"], reverse=True)
        seen = set()
        deduped = []
        for d in all_deals:
            if d["route_key"] not in seen:
                seen.add(d["route_key"])
                deduped.append(d)

        return deduped[:limit]

    async def search(self, query: str, budget_pp: float = 9999) -> list[dict]:
        """Natural language search — parse origin/dest and search."""
        # Basic parsing: "London to Dubai", "LHR → DXB", "Dubai", etc.
        query = query.strip()
        origin = "LHR"  # default home airport
        destination = query

        for sep in [" to ", " → ", " -> ", " - "]:
            if sep in query.lower():
                parts = query.lower().split(sep, 1)
                origin = parts[0].strip().upper()[:3]
                destination = parts[1].strip().upper()[:3]
                break

        today = datetime.now()
        dep = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        ret = (today + timedelta(days=21)).strftime("%Y-%m-%d")

        deals = await self.search_flights(origin, destination, dep, ret)
        return [d for d in deals if d["price_pp"] <= budget_pp]

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
