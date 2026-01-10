"""API Client for WestfalenWIND Tarifdynamik."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://api.wws.tarifdynamik.de"


class WWSTarifdynamikApiError(Exception):
    """Exception for API errors."""


class WWSTarifdynamikAuthError(WWSTarifdynamikApiError):
    """Exception for authentication errors."""


class WWSTarifdynamikApi:
    """API Client for WestfalenWIND Tarifdynamik."""

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        """Initialize the API client."""
        self.hass = hass
        self._username = username
        self._password = password
        self._token: str | None = None
        self._token_expiry: datetime | None = None
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session."""
        if self._session is None:
            self._session = async_get_clientsession(self.hass)
        return self._session

    async def _ensure_token(self) -> str:
        """Ensure we have a valid token, refresh if needed."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        await self._authenticate()
        return self._token

    async def _authenticate(self) -> None:
        """Authenticate and get a new token."""
        session = await self._get_session()
        
        try:
            async with session.post(
                f"{API_BASE_URL}/tokens/",
                data={
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status == 401:
                    raise WWSTarifdynamikAuthError("Invalid credentials")
                if response.status != 200:
                    raise WWSTarifdynamikApiError(f"Authentication failed: {response.status}")
                
                data = await response.json()
                self._token = data.get("access_token")
                
                # Token expires in ~24h, refresh after 23h to be safe
                expires_in = data.get("expires_in", 86400)
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 3600)
                
                _LOGGER.debug("Successfully authenticated with WWS API")
                
        except aiohttp.ClientError as err:
            raise WWSTarifdynamikApiError(f"Connection error: {err}") from err

    async def test_connection(self) -> bool:
        """Test if we can authenticate."""
        try:
            await self._authenticate()
            return True
        except WWSTarifdynamikApiError:
            return False

    async def get_prognosis(self, days: int = 2) -> list[dict[str, Any]]:
        """Get price prognosis for the next days."""
        token = await self._ensure_token()
        session = await self._get_session()
        
        today = datetime.now().strftime("%Y-%m-%d")
        page_size = days * 24 * 4  # 4 entries per hour (15 min intervals)
        
        try:
            async with session.get(
                f"{API_BASE_URL}/tariffs/prognosis",
                params={
                    "timezone": "Europe/Berlin",
                    "page_size": str(page_size),
                    "filters": f"valid_from:gte:{today}",
                },
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status == 401:
                    # Token might be expired, try to re-authenticate
                    self._token = None
                    token = await self._ensure_token()
                    return await self.get_prognosis(days)
                
                if response.status != 200:
                    raise WWSTarifdynamikApiError(f"API error: {response.status}")
                
                data = await response.json()
                return data.get("data", [])
                
        except aiohttp.ClientError as err:
            raise WWSTarifdynamikApiError(f"Connection error: {err}") from err

    async def get_saving_window(self, hours: int = 2) -> dict[str, Any] | None:
        """Get the best saving window for today."""
        token = await self._ensure_token()
        session = await self._get_session()
        
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            async with session.get(
                f"{API_BASE_URL}/tariffs/periods/saving_window",
                params={
                    "timezone": "Europe/Berlin",
                    "hours": str(hours),
                    "start": f"{today}T00:00:00",
                    "end": f"{tomorrow}T23:59:59",
                },
                headers={"Authorization": f"Bearer {token}"},
            ) as response:
                if response.status == 401:
                    self._token = None
                    token = await self._ensure_token()
                    return await self.get_saving_window(hours)
                
                if response.status != 200:
                    _LOGGER.warning("Could not get saving window: %s", response.status)
                    return None
                
                return await response.json()
                
        except aiohttp.ClientError as err:
            _LOGGER.warning("Connection error getting saving window: %s", err)
            return None
