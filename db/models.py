"""
Fairo Database — PostgreSQL via asyncpg (Supabase)
All tables auto-created on first run.
Complete — includes all methods called by bot and worker.
"""
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, url: str):
        self.url = url
        self._pool = None

    async def pool(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                self.url, min_size=1, max_size=10,
                command_timeout=30
            )
            await self._create_tables()
        return self._pool

    async def _create_tables(self):
        p = self._pool
        async with p.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT DEFAULT '',
                    lang TEXT DEFAULT 'en',
                    currency TEXT DEFAULT 'GBP',
                    currency_sym TEXT DEFAULT '£',
                    home_city TEXT DEFAULT 'London',
                    home_airport TEXT DEFAULT 'LHR',
                    budget_pp NUMERIC DEFAULT 9999,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    route TEXT NOT NULL,
                    route_key TEXT NOT NULL,
                    budget_pp NUMERIC NOT NULL,
                    currency TEXT DEFAULT 'GBP',
                    currency_sym TEXT DEFAULT '£',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS hunts (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    destination TEXT NOT NULL,
                    budget_pp NUMERIC DEFAULT 0,
                    currency TEXT DEFAULT 'GBP',
                    currency_sym TEXT DEFAULT '£',
                    status TEXT DEFAULT 'searching',
                    best_deal JSONB,
                    best_price_pp NUMERIC DEFAULT 9999,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    route_key TEXT,
                    dep_date TEXT,
                    sent_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
                CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(active);
                CREATE INDEX IF NOT EXISTS idx_hunts_user ON hunts(user_id);
                CREATE INDEX IF NOT EXISTS idx_hunts_status ON hunts(status);
                CREATE INDEX IF NOT EXISTS idx_notifs ON notifications(user_id, route_key, dep_date);
            """)

    # ── USERS ─────────────────────────────────────────────────────────────────

    async def upsert_user(self, user_id: int, username: str, lang_code: str = "en"):
        p = await self.pool()
        # Only use first 2 chars of lang code, default to en
        lang = (lang_code or "en")[:2]
        if lang not in ["en","es","fr","de","ar","tr","hi","it","pt","zh"]:
            lang = "en"
        async with p.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (id, username, lang)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username
            """, user_id, username or "", lang)

    async def get_user_lang(self, user_id: int) -> str:
        p = await self.pool()
        async with p.acquire() as conn:
            row = await conn.fetchrow("SELECT lang FROM users WHERE id = $1", user_id)
            return row["lang"] if row else "en"

    async def set_user_lang(self, user_id: int, lang: str):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "UPDATE users SET lang = $1 WHERE id = $2", lang, user_id
            )

    async def set_user_currency(self, user_id: int, currency: str, sym: str):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "UPDATE users SET currency = $1, currency_sym = $2 WHERE id = $3",
                currency, sym, user_id
            )

    async def set_user_city(self, user_id: int, city: str):
        p = await self.pool()
        async with p.acquire() as conn:
            # Try to extract airport code if 3 uppercase letters
            airport = city.strip().upper() if len(city.strip()) == 3 else "LHR"
            await conn.execute(
                "UPDATE users SET home_city = $1, home_airport = $2 WHERE id = $3",
                city, airport, user_id
            )

    async def get_user_prefs(self, user_id: int) -> dict:
        p = await self.pool()
        async with p.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            if row:
                return dict(row)
            return {
                "currency": "GBP", "currency_sym": "£",
                "lang": "en", "budget_pp": 9999,
                "home_city": "London", "home_airport": "LHR"
            }

    # ── ALERTS ────────────────────────────────────────────────────────────────

    async def create_alert(self, user_id: int, route: str, budget_pp: float, currency: str, sym: str):
        # Build a route_key like "LHR-DXB" from "London → Dubai"
        clean = route.upper().replace(" ", "").replace("→", "-").replace("->", "-").replace("–", "-")
        route_key = clean[:20]
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute("""
                INSERT INTO alerts (user_id, route, route_key, budget_pp, currency, currency_sym)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, route, route_key, budget_pp, currency, sym)

    async def get_user_alerts(self, user_id: int) -> list:
        p = await self.pool()
        async with p.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM alerts WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [dict(r) for r in rows]

    async def get_all_active_alerts(self) -> list:
        p = await self.pool()
        async with p.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM alerts WHERE active = TRUE")
            return [dict(r) for r in rows]

    async def toggle_alert(self, user_id: int, alert_id: int):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "UPDATE alerts SET active = NOT active WHERE id = $1 AND user_id = $2",
                alert_id, user_id
            )

    async def delete_alert(self, user_id: int, alert_id: int):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "DELETE FROM alerts WHERE id = $1 AND user_id = $2",
                alert_id, user_id
            )

    # ── HUNTS ─────────────────────────────────────────────────────────────────

    async def create_hunt(self, user_id: int, destination: str, budget_pp: float, currency: str, sym: str):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute("""
                INSERT INTO hunts (user_id, destination, budget_pp, currency, currency_sym)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, destination, budget_pp, currency, sym)

    async def get_user_hunts(self, user_id: int) -> list:
        p = await self.pool()
        async with p.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM hunts WHERE user_id = $1 AND status != 'stopped' ORDER BY created_at DESC",
                user_id
            )
            result = []
            for r in rows:
                d = dict(r)
                if d.get("best_deal"):
                    try:
                        d["best_deal"] = json.loads(d["best_deal"]) if isinstance(d["best_deal"], str) else d["best_deal"]
                    except Exception:
                        d["best_deal"] = None
                result.append(d)
            return result

    async def get_all_active_hunts(self) -> list:
        p = await self.pool()
        async with p.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM hunts WHERE status = 'searching'"
            )
            return [dict(r) for r in rows]

    async def toggle_hunt(self, user_id: int, hunt_id: int):
        """Pause a searching hunt or resume a paused hunt."""
        p = await self.pool()
        async with p.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status FROM hunts WHERE id = $1 AND user_id = $2",
                hunt_id, user_id
            )
            if row:
                new_status = "paused" if row["status"] == "searching" else "searching"
                await conn.execute(
                    "UPDATE hunts SET status = $1, updated_at = NOW() WHERE id = $2 AND user_id = $3",
                    new_status, hunt_id, user_id
                )

    async def delete_hunt(self, user_id: int, hunt_id: int):
        """Permanently stop and remove a hunt."""
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "UPDATE hunts SET status = 'stopped', updated_at = NOW() WHERE id = $1 AND user_id = $2",
                hunt_id, user_id
            )

    async def update_hunt_best(self, hunt_id: int, deal: dict):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute("""
                UPDATE hunts
                SET best_deal = $1, best_price_pp = $2, status = 'found', updated_at = NOW()
                WHERE id = $3
            """, json.dumps(deal), deal.get("price_pp", 9999), hunt_id)

    # ── NOTIFICATIONS ─────────────────────────────────────────────────────────

    async def already_notified(self, user_id: int, route_key: str, dep_date: str) -> bool:
        p = await self.pool()
        async with p.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id FROM notifications
                WHERE user_id = $1
                  AND route_key = $2
                  AND dep_date = $3
                  AND sent_at > NOW() - INTERVAL '24 hours'
            """, user_id, route_key, dep_date)
            return row is not None

    async def log_notification(self, user_id: int, route_key: str, dep_date: str):
        p = await self.pool()
        async with p.acquire() as conn:
            await conn.execute(
                "INSERT INTO notifications (user_id, route_key, dep_date) VALUES ($1, $2, $3)",
                user_id, route_key, dep_date
            )
