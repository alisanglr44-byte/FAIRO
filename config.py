import os

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
    TRAVELPAYOUTS_MARKER = os.getenv("TRAVELPAYOUTS_MARKER", "")
    BOOKING_AFFILIATE_ID = os.getenv("BOOKING_AFFILIATE_ID", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SCAN_INTERVAL_MINUTES = 15
    HOT_DEAL_THRESHOLD_PCT = 40
    ERROR_FARE_THRESHOLD_PCT = 70
    HOME_AIRPORTS = ["LHR", "LGW", "MAN", "BHX", "EDI", "STN", "LTN"]
    HOT_ROUTES = [
        ("LHR", "DXB"), ("LHR", "TFS"), ("LHR", "BCN"), ("LHR", "LIS"),
        ("LHR", "FAO"), ("LHR", "AGP"), ("LHR", "AYT"), ("LHR", "JFK"),
        ("MAN", "DXB"), ("MAN", "TFS"), ("MAN", "BCN"), ("MAN", "AGP"),
        ("LGW", "TFS"), ("LGW", "AGP"), ("LGW", "LIS"), ("LGW", "PMI"),
    ]
    RATES = {
        "GBP": 1.0, "USD": 1.26, "EUR": 1.17,
        "TRY": 40.8, "INR": 105.2, "AED": 4.67,
        "AUD": 1.92, "CAD": 1.71,
    }
    CURRENCY_SYMS = {
        "GBP": "£", "USD": "$", "EUR": "€", "TRY": "₺",
        "INR": "₹", "AED": "د.إ", "AUD": "A$", "CAD": "C$",
    }
