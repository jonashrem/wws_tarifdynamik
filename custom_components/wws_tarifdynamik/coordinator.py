"""DataUpdateCoordinator for WestfalenWIND Tarifdynamik."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WWSTarifdynamikApi, WWSTarifdynamikApiError
from .const import DOMAIN, DEFAULT_PRICE_SMART, DEFAULT_PRICE_STANDARD, DEFAULT_SAVING_WINDOW_HOURS

_LOGGER = logging.getLogger(__name__)


class WWSTarifdynamikCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching WWS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: WWSTarifdynamikApi,
        price_smart: float = DEFAULT_PRICE_SMART,
        price_standard: float = DEFAULT_PRICE_STANDARD,
        saving_window_hours: int = DEFAULT_SAVING_WINDOW_HOURS,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=self._calculate_next_update_interval(),
        )
        self.api = api
        self.price_smart = price_smart
        self.price_standard = price_standard
        self.saving_window_hours = saving_window_hours

    @staticmethod
    def _calculate_next_update_interval() -> timedelta:
        """Calculate time until the next 15-minute boundary + 50 seconds.

        Updates are aligned to HH:00:50, HH:15:50, HH:30:50, HH:45:50
        to match WestfalenWIND's 15-minute tariff change schedule.
        """
        now = datetime.now()
        current_minute = now.minute
        # Find the next quarter-hour mark (0, 15, 30, 45)
        next_quarter = ((current_minute // 15) + 1) * 15

        if next_quarter >= 60:
            next_time = now.replace(minute=0, second=50, microsecond=0) + timedelta(hours=1)
        else:
            next_time = now.replace(minute=next_quarter, second=50, microsecond=0)

        delta = next_time - now

        # Safety: if we're very close or past the target, skip to next quarter
        if delta.total_seconds() <= 5:
            next_time += timedelta(minutes=15)
            delta = next_time - now

        _LOGGER.debug(
            "Next update scheduled in %s (at %s)",
            delta,
            next_time.strftime("%H:%M:%S"),
        )
        return delta

    def _get_actual_price(self, tariff_name: str) -> float:
        """Convert API tariff name to actual configured price."""
        if tariff_name == "SMART":
            return self.price_smart
        return self.price_standard

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Get prognosis for today and tomorrow
            prognosis = await self.api.get_prognosis(days=2)
            
            # Get saving window
            saving_window = await self.api.get_saving_window(hours=self.saving_window_hours)
            
            # Process the data
            now = datetime.now()
            current_price = None
            next_price = None
            prices_today = []
            prices_tomorrow = []
            
            today_str = now.strftime("%Y-%m-%d")
            tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            
            for entry in prognosis:
                valid_from = entry.get("start", "")
                valid_to = entry.get("end", "")
                tariff_name = entry.get("tariff_name", "STANDARD")
                actual_price = self._get_actual_price(tariff_name)
                
                price_data = {
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "price_ct_kwh": actual_price,
                    "price_mode": tariff_name,
                    "is_smart": tariff_name == "SMART",
                    "api_price_ct_kwh": entry.get("price_ct_kwh"),
                }
                
                # Sort into today/tomorrow
                if valid_from.startswith(today_str):
                    prices_today.append(price_data)
                elif valid_from.startswith(tomorrow_str):
                    prices_tomorrow.append(price_data)
                
                # Find current price
                try:
                    entry_start = datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
                    if valid_to:
                        entry_end = datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
                    else:
                        entry_end = entry_start + timedelta(minutes=15)
                    
                    # Make now timezone-aware for comparison
                    now_aware = now.astimezone()
                    
                    if entry_start <= now_aware < entry_end:
                        current_price = price_data
                    elif entry_start > now_aware and next_price is None:
                        next_price = price_data
                except (ValueError, TypeError):
                    pass
            
            # Process saving window with actual prices
            if saving_window:
                saving_window["avg_price_ct_kwh"] = self.price_smart
            
            # Build result
            result = {
                "current_price": current_price,
                "next_price": next_price,
                "prices_today": prices_today,
                "prices_tomorrow": prices_tomorrow,
                "saving_window": saving_window,
                "last_update": now.isoformat(),
                "config": {
                    "price_smart": self.price_smart,
                    "price_standard": self.price_standard,
                },
            }
            
            _LOGGER.debug("Updated WWS data: current=%s", current_price)

            # Recalculate interval so the next update aligns to the clock
            self.update_interval = self._calculate_next_update_interval()

            return result
            
        except WWSTarifdynamikApiError as err:
            # Still realign on error so we retry at the next quarter hour
            self.update_interval = self._calculate_next_update_interval()
            raise UpdateFailed(f"Error fetching data: {err}") from err
