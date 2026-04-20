import os

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # RapidAPI — one key covers Sky Scrapper (flights) + Booking.com (hotels)
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

    # Travelpayouts affiliate marker (apply at travelpayouts.com)
    TRAVELPAYOUTS_MARKER = os.getenv("TRAVELPAYOUTS_MARKER", "")

    # Booking.com affiliate ID (apply at booking.com/affiliate-program)
    BOOKING_AFFILIATE_ID = os.getenv("BOOKING_AFFILIATE_ID", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Scanner settings
    SCAN_INTERVAL_MINUTES = 15
    HOT_DEAL_THRESHOLD_PCT = 40   # min saving % to class as a hot deal
    ERROR_FARE_THRESHOLD_PCT = 70  # min saving % to class as error fare

    # Home routes to scan for hot deals (expand as you grow)
    HOME_AIRPORTS = ["LHR", "LGW", "MAN", "BHX", "EDI", "STN", "LTN"]
    HOT_ROUTES = [
        ("LHR", "DXB"), ("LHR", "TFS"), ("LHR", "BCN"), ("LHR", "LIS"),
        ("LHR", "FAO"), ("LHR", "AGP"), ("LHR", "AYT"), ("LHR", "JFK"),
        ("MAN", "DXB"), ("MAN", "TFS"), ("MAN", "BCN"), ("MAN", "AGP"),
        ("LGW", "TFS"), ("LGW", "AGP"), ("LGW", "LIS"), ("LGW", "PMI"),
    ]

    # Currency conversion rates (GBP base — update weekly or use a rates API)
    RATES = {
        "GBP": 1.0, "USD": 1.26, "EUR": 1.17,
        "TRY": 40.8, "INR": 105.2, "AED": 4.67,
        "AUD": 1.92, "CAD": 1.71,
    }
    CURRENCY_SYMS = {
        "GBP": "£", "USD": "$", "EUR": "€", "TRY": "₺",
        "INR": "₹", "AED": "د.إ", "AUD": "A$", "CAD": "C$",
    }
