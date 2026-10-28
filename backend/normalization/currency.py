"""Currency conversion and exchange rate table."""
from typing import Tuple

# Fixed versioned exchange rate table (Rates per 1 foreign currency in USD)
EXCHANGE_RATES_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.30,
    "CAD": 0.72,
    "AUD": 0.66,
    "INR": 0.012,
    "JPY": 0.0065,
    "SGD": 0.76,
    "CHF": 1.15,
}

RATES_DATE = "2026-10-28"

def convert_to_usd(amount: float, currency: str) -> Tuple[float, float, str]:
    """
    Converts amount in given currency to USD.
    Returns (amount_usd, exchange_rate, rate_date).
    """
    curr = (currency or "USD").strip().upper()
    rate = EXCHANGE_RATES_USD.get(curr, 1.0)
    usd_val = round(float(amount or 0.0) * rate, 2)
    return usd_val, rate, RATES_DATE

