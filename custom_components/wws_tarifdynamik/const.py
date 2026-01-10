"""Constants for the WestfalenWIND Tarifdynamik integration."""

DOMAIN = "wws_tarifdynamik"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_PRICE_SMART = "price_smart"
CONF_PRICE_STANDARD = "price_standard"
CONF_SAVING_WINDOW_HOURS = "saving_window_hours"

DEFAULT_SCAN_INTERVAL = 900  # 15 minutes
DEFAULT_PRICE_SMART = 19.96
DEFAULT_PRICE_STANDARD = 29.96
DEFAULT_SAVING_WINDOW_HOURS = 2

ATTR_PRICE_CT_KWH = "price_ct_kwh"
ATTR_PRICE_MODE = "price_mode"
ATTR_VALID_FROM = "valid_from"
ATTR_VALID_TO = "valid_to"
ATTR_IS_SMART = "is_smart"
ATTR_PRICES_TODAY = "prices_today"
ATTR_PRICES_TOMORROW = "prices_tomorrow"
ATTR_SAVING_WINDOW_START = "saving_window_start"
ATTR_SAVING_WINDOW_END = "saving_window_end"
ATTR_SAVING_WINDOW_AVG_PRICE = "saving_window_avg_price"
