"""Sensor platform for WestfalenWIND Tarifdynamik."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WWSTarifdynamikCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WWS Tarifdynamik sensors."""
    coordinator: WWSTarifdynamikCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        WWSTarifdynamikCurrentPriceSensor(coordinator, entry),
        WWSTarifdynamikPriceModeSensor(coordinator, entry),
        WWSTarifdynamikNextPriceSensor(coordinator, entry),
        WWSTarifdynamikSavingWindowSensor(coordinator, entry),
        WWSTarifdynamikIsSmartSensor(coordinator, entry),
        WWSTarifdynamikPricesTodaySensor(coordinator, entry),
        WWSTarifdynamikPricesTomorrowSensor(coordinator, entry),
        WWSTarifdynamikNextSmartSensor(coordinator, entry),
        WWSTarifdynamikSmartHoursTodaySensor(coordinator, entry),
    ]
    
    async_add_entities(entities)


class WWSTarifdynamikBaseSensor(CoordinatorEntity[WWSTarifdynamikCoordinator], SensorEntity):
    """Base class for WWS Tarifdynamik sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WestfalenWIND Stromtarif",
            manufacturer="EnergieDock / WestfalenWIND",
            model="Dynamischer Stromtarif",
        )


class WWSTarifdynamikCurrentPriceSensor(WWSTarifdynamikBaseSensor):
    """Sensor for current electricity price."""

    _attr_name = "Strompreis Aktuell"
    _attr_native_unit_of_measurement = "ct/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-eur"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_price"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.coordinator.data and self.coordinator.data.get("current_price"):
            return self.coordinator.data["current_price"].get("price_ct_kwh")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data:
            if self.coordinator.data.get("current_price"):
                attrs["valid_from"] = self.coordinator.data["current_price"].get("valid_from")
                attrs["valid_to"] = self.coordinator.data["current_price"].get("valid_to")
                attrs["price_mode"] = self.coordinator.data["current_price"].get("price_mode")
            
            attrs["prices_today"] = self.coordinator.data.get("prices_today", [])
            attrs["prices_tomorrow"] = self.coordinator.data.get("prices_tomorrow", [])
            attrs["last_update"] = self.coordinator.data.get("last_update")
        return attrs


class WWSTarifdynamikPriceModeSensor(WWSTarifdynamikBaseSensor):
    """Sensor for current price mode (SMART/STANDARD)."""

    _attr_name = "Tarifmodus"
    _attr_icon = "mdi:tag"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_price_mode"

    @property
    def native_value(self) -> str | None:
        """Return the current price mode."""
        if self.coordinator.data and self.coordinator.data.get("current_price"):
            return self.coordinator.data["current_price"].get("price_mode")
        return None


class WWSTarifdynamikNextPriceSensor(WWSTarifdynamikBaseSensor):
    """Sensor for next electricity price."""

    _attr_name = "Strompreis Nächste Periode"
    _attr_native_unit_of_measurement = "ct/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-eur"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_price"

    @property
    def native_value(self) -> float | None:
        """Return the next price."""
        if self.coordinator.data and self.coordinator.data.get("next_price"):
            return self.coordinator.data["next_price"].get("price_ct_kwh")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data and self.coordinator.data.get("next_price"):
            attrs["valid_from"] = self.coordinator.data["next_price"].get("valid_from")
            attrs["valid_to"] = self.coordinator.data["next_price"].get("valid_to")
            attrs["price_mode"] = self.coordinator.data["next_price"].get("price_mode")
        return attrs


class WWSTarifdynamikSavingWindowSensor(WWSTarifdynamikBaseSensor):
    """Sensor for the best saving window."""

    _attr_name = "Bestes Sparfenster"
    _attr_icon = "mdi:piggy-bank"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_saving_window"

    @property
    def native_value(self) -> str | None:
        """Return the saving window start time."""
        if self.coordinator.data and self.coordinator.data.get("saving_window"):
            start = self.coordinator.data["saving_window"].get("start", "")
            if start:
                try:
                    dt = datetime.fromisoformat(start)
                    return dt.strftime("%H:%M")
                except ValueError:
                    return start
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        if self.coordinator.data and self.coordinator.data.get("saving_window"):
            sw = self.coordinator.data["saving_window"]
            attrs["start"] = sw.get("start")
            attrs["end"] = sw.get("end")
            attrs["avg_price_ct_kwh"] = sw.get("avg_price_ct_kwh")
            
            # Calculate duration
            try:
                start = datetime.fromisoformat(sw.get("start", ""))
                end = datetime.fromisoformat(sw.get("end", ""))
                duration = end - start
                attrs["duration_hours"] = duration.total_seconds() / 3600
            except (ValueError, TypeError):
                pass
        return attrs


class WWSTarifdynamikIsSmartSensor(WWSTarifdynamikBaseSensor):
    """Binary-like sensor showing if current price is SMART."""

    _attr_name = "Smart-Tarif Aktiv"
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_is_smart"

    @property
    def native_value(self) -> str:
        """Return if smart tariff is active."""
        if self.coordinator.data and self.coordinator.data.get("current_price"):
            is_smart = self.coordinator.data["current_price"].get("is_smart", False)
            return "Ja" if is_smart else "Nein"
        return "Unbekannt"

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        if self.coordinator.data and self.coordinator.data.get("current_price"):
            if self.coordinator.data["current_price"].get("is_smart", False):
                return "mdi:lightning-bolt"
        return "mdi:lightning-bolt-outline"


class WWSTarifdynamikPricesTodaySensor(WWSTarifdynamikBaseSensor):
    """Sensor showing all prices for today."""

    _attr_name = "Preise Heute"
    _attr_icon = "mdi:calendar-today"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_prices_today"

    @property
    def native_value(self) -> str:
        """Return summary of today's prices."""
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_today", [])
            if prices:
                smart_count = sum(1 for p in prices if p.get("is_smart"))
                return f"{len(prices)} Perioden, {smart_count} SMART"
        return "Keine Daten"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all prices for today."""
        attrs = {}
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_today", [])
            attrs["prices"] = prices
            attrs["count"] = len(prices)
            
            # Create hourly summary for easier visualization
            hourly = {}
            for p in prices:
                try:
                    dt = datetime.fromisoformat(p.get("valid_from", "").replace("Z", "+00:00"))
                    hour = dt.strftime("%H:00")
                    if hour not in hourly:
                        hourly[hour] = {
                            "price_ct_kwh": p.get("price_ct_kwh"),
                            "price_mode": p.get("price_mode"),
                            "is_smart": p.get("is_smart"),
                        }
                except (ValueError, TypeError):
                    pass
            attrs["hourly"] = hourly
            
            # Statistics
            if prices:
                price_values = [p.get("price_ct_kwh", 0) for p in prices if p.get("price_ct_kwh")]
                if price_values:
                    attrs["min_price"] = min(price_values)
                    attrs["max_price"] = max(price_values)
                    attrs["avg_price"] = round(sum(price_values) / len(price_values), 2)
                    
        return attrs


class WWSTarifdynamikPricesTomorrowSensor(WWSTarifdynamikBaseSensor):
    """Sensor showing all prices for tomorrow."""

    _attr_name = "Preise Morgen"
    _attr_icon = "mdi:calendar-tomorrow"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_prices_tomorrow"

    @property
    def native_value(self) -> str:
        """Return summary of tomorrow's prices."""
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_tomorrow", [])
            if prices:
                smart_count = sum(1 for p in prices if p.get("is_smart"))
                return f"{len(prices)} Perioden, {smart_count} SMART"
        return "Keine Daten"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all prices for tomorrow."""
        attrs = {}
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_tomorrow", [])
            attrs["prices"] = prices
            attrs["count"] = len(prices)
            
            # Create hourly summary
            hourly = {}
            for p in prices:
                try:
                    dt = datetime.fromisoformat(p.get("valid_from", "").replace("Z", "+00:00"))
                    hour = dt.strftime("%H:00")
                    if hour not in hourly:
                        hourly[hour] = {
                            "price_ct_kwh": p.get("price_ct_kwh"),
                            "price_mode": p.get("price_mode"),
                            "is_smart": p.get("is_smart"),
                        }
                except (ValueError, TypeError):
                    pass
            attrs["hourly"] = hourly
            
            # Statistics
            if prices:
                price_values = [p.get("price_ct_kwh", 0) for p in prices if p.get("price_ct_kwh")]
                if price_values:
                    attrs["min_price"] = min(price_values)
                    attrs["max_price"] = max(price_values)
                    attrs["avg_price"] = round(sum(price_values) / len(price_values), 2)
                    
        return attrs


class WWSTarifdynamikNextSmartSensor(WWSTarifdynamikBaseSensor):
    """Sensor showing when the next SMART period starts."""

    _attr_name = "Nächste SMART-Periode"
    _attr_icon = "mdi:clock-fast"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_smart"

    @property
    def native_value(self) -> str | None:
        """Return when next SMART period starts."""
        if self.coordinator.data:
            # Check if currently in SMART
            current = self.coordinator.data.get("current_price", {})
            if current and current.get("is_smart"):
                return "Jetzt aktiv"
            
            # Find next SMART period
            now = datetime.now().astimezone()
            all_prices = (
                self.coordinator.data.get("prices_today", []) +
                self.coordinator.data.get("prices_tomorrow", [])
            )
            
            for p in all_prices:
                if p.get("is_smart"):
                    try:
                        start = datetime.fromisoformat(p.get("valid_from", "").replace("Z", "+00:00"))
                        if start > now:
                            return start.strftime("%H:%M")
                    except (ValueError, TypeError):
                        pass
        return "Nicht verfügbar"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details about next SMART period."""
        attrs = {}
        if self.coordinator.data:
            now = datetime.now().astimezone()
            all_prices = (
                self.coordinator.data.get("prices_today", []) +
                self.coordinator.data.get("prices_tomorrow", [])
            )
            
            # Find next SMART period
            for p in all_prices:
                if p.get("is_smart"):
                    try:
                        start = datetime.fromisoformat(p.get("valid_from", "").replace("Z", "+00:00"))
                        if start > now:
                            attrs["start"] = p.get("valid_from")
                            attrs["price_ct_kwh"] = p.get("price_ct_kwh")
                            
                            # Calculate time until
                            delta = start - now
                            hours = int(delta.total_seconds() // 3600)
                            minutes = int((delta.total_seconds() % 3600) // 60)
                            attrs["time_until"] = f"{hours}h {minutes}min"
                            attrs["minutes_until"] = int(delta.total_seconds() // 60)
                            break
                    except (ValueError, TypeError):
                        pass
        return attrs


class WWSTarifdynamikSmartHoursTodaySensor(WWSTarifdynamikBaseSensor):
    """Sensor showing all SMART hours for today."""

    _attr_name = "SMART-Zeiten Heute"
    _attr_icon = "mdi:clock-check"

    def __init__(
        self,
        coordinator: WWSTarifdynamikCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_smart_hours_today"

    @property
    def native_value(self) -> str:
        """Return SMART hours as readable string."""
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_today", [])
            smart_hours = set()
            
            for p in prices:
                if p.get("is_smart"):
                    try:
                        dt = datetime.fromisoformat(p.get("valid_from", "").replace("Z", "+00:00"))
                        smart_hours.add(dt.hour)
                    except (ValueError, TypeError):
                        pass
            
            if smart_hours:
                # Group consecutive hours
                sorted_hours = sorted(smart_hours)
                ranges = []
                start = sorted_hours[0]
                end = start
                
                for h in sorted_hours[1:]:
                    if h == end + 1:
                        end = h
                    else:
                        ranges.append(f"{start:02d}-{end+1:02d}")
                        start = h
                        end = h
                ranges.append(f"{start:02d}-{end+1:02d}")
                
                return ", ".join(ranges) + " Uhr"
        return "Keine SMART-Zeiten"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed SMART periods."""
        attrs = {"smart_periods": []}
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices_today", [])
            
            for p in prices:
                if p.get("is_smart"):
                    attrs["smart_periods"].append({
                        "start": p.get("valid_from"),
                        "end": p.get("valid_to"),
                        "price_ct_kwh": p.get("price_ct_kwh"),
                    })
            
            # Count SMART quarters (15-min periods)
            attrs["smart_quarters"] = len(attrs["smart_periods"])
            attrs["smart_hours"] = len(attrs["smart_periods"]) / 4
            
        return attrs
