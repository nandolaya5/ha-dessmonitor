"""API client for ValueClouds (formerly DessMonitor)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import aiohttp
import async_timeout
from homeassistant.helpers.storage import Store

from .const import API_BASE_URL, DEFAULT_DEVADDR, DEFAULT_I18N, HEADER_PROJECT, UNITS, VERSION

_LOGGER = logging.getLogger(__name__)


def _mask_identifier(value: str | None) -> str:
    """Return a redacted identifier for logging."""
    if not value:
        return "***"
    trimmed = value.strip()
    if len(trimmed) <= 3:
        return "***"
    return f"{trimmed[:3]}***"


class DessMonitorAPI:
    """ValueClouds API client."""

    def __init__(
        self,
        username: str,
        password: str,
        pn: str = "",
        sn: str = "",
        devcode: str = "",
        devaddr: str = "",
        session: aiohttp.ClientSession | None = None,
        store: Store | None = None,
    ) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self.pn = pn
        self.sn = sn
        self.devcode = devcode
        self.devaddr = devaddr or DEFAULT_DEVADDR
        self.base_url = API_BASE_URL

        self._session = session
        self._close_session = False

        self.token: str | None = None
        self.secret: str | None = None
        self._store = store

        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

    async def close(self) -> None:
        """Close the session."""
        if self._session and self._close_session:
            await self._session.close()

    def _sha1(self, data: str) -> str:
        """Generate SHA-1 hash."""
        return hashlib.sha1(data.encode()).hexdigest().lower()

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers for authenticated requests."""
        return {
            "Token": self.token or "",
            "project": HEADER_PROJECT,
            "i18n": DEFAULT_I18N,
        }

    async def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make API request using GET with token header."""
        self._ensure_session()
        await self._ensure_token()

        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()

        _LOGGER.debug(
            "Making %s request with %d parameters", endpoint, len(params) if params else 0
        )

        response_data = await self._fetch_json(endpoint, url, params, headers)
        return self._validate_api_response(endpoint, response_data)

    async def _make_post_request(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Make API request using POST with JSON body."""
        self._ensure_session()

        url = f"{self.base_url}{endpoint}"

        _LOGGER.debug("Making POST request to %s", endpoint)

        response_data = await self._fetch_json_post(endpoint, url, payload)
        return self._validate_api_response(endpoint, response_data)

    def _ensure_session(self) -> None:
        """Ensure that an aiohttp session is available."""
        if not self._session:
            raise RuntimeError("Session not initialized")

    async def _ensure_token(self) -> None:
        """Refresh authentication token when required."""
        if self.token is None:
            await self.authenticate()

    async def _fetch_json(
        self,
        action: str,
        url: str,
        params: dict[str, Any] | None,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Execute HTTP GET and return JSON payload."""
        assert self._session is not None
        timeout_seconds = 30

        try:
            async with async_timeout.timeout(timeout_seconds):
                async with self._session.get(
                    url, params=params, headers=headers
                ) as response:
                    if response.status in (401, 403):
                        raise DessMonitorError(
                            f"Authentication rejected with HTTP status {response.status}"
                        )
                    response.raise_for_status()
                    try:
                        return await response.json(content_type=None)
                    except aiohttp.ContentTypeError as err:
                        text_preview = await response.text()
                        _LOGGER.error(
                            "Invalid JSON response for action '%s': %s",
                            action,
                            text_preview[:500],
                        )
                        raise DessMonitorError("Invalid response from server") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error(
                "API request for action '%s' timed out after %ss",
                action,
                timeout_seconds,
            )
            raise DessMonitorError("Request timed out") from err
        except asyncio.CancelledError as err:
            _LOGGER.error(
                "API request for action '%s' was cancelled (likely due to timeout)",
                action,
            )
            raise DessMonitorError("Request cancelled") from err
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "HTTP %s error for action '%s': %s",
                err.status,
                action,
                err.message,
            )
            raise DessMonitorError(
                f"Server returned HTTP {err.status}: {err.message or 'Unknown error'}"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed for action '%s': %s", action, err)
            raise DessMonitorError(f"Request failed: {err}") from err

    async def _fetch_json_post(
        self,
        action: str,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute HTTP POST with JSON body and return JSON payload."""
        assert self._session is not None
        timeout_seconds = 30

        try:
            async with async_timeout.timeout(timeout_seconds):
                async with self._session.post(url, json=payload) as response:
                    if response.status != 200:
                        raise DessMonitorError(
                            f"Login failed with HTTP status {response.status}"
                        )
                    try:
                        return await response.json(content_type=None)
                    except aiohttp.ContentTypeError as err:
                        text_preview = await response.text()
                        _LOGGER.error(
                            "Invalid JSON response for action '%s': %s",
                            action,
                            text_preview[:500],
                        )
                        raise DessMonitorError("Invalid response from server") from err
        except asyncio.TimeoutError as err:
            _LOGGER.error(
                "API request for action '%s' timed out after %ss",
                action,
                timeout_seconds,
            )
            raise DessMonitorError("Request timed out") from err
        except asyncio.CancelledError as err:
            _LOGGER.error(
                "API request for action '%s' was cancelled (likely due to timeout)",
                action,
            )
            raise DessMonitorError("Request cancelled") from err
        except aiohttp.ClientResponseError as err:
            _LOGGER.error(
                "HTTP %s error for action '%s': %s",
                err.status,
                action,
                err.message,
            )
            raise DessMonitorError(
                f"Server returned HTTP {err.status}: {err.message or 'Unknown error'}"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed for action '%s': %s", action, err)
            raise DessMonitorError(f"Request failed: {err}") from err

    @staticmethod
    def _validate_api_response(action: str, data: dict[str, Any]) -> dict[str, Any]:
        """Validate API payload and raise errors when needed."""
        code = data.get("code")
        success = data.get("success")
        _LOGGER.debug("API response for '%s': success=%s, code=%s", action, success, code)

        if success is False or (success is None and code is not None and code != 0):
            error_msg = data.get("message") or data.get("errorMessage") or f"API error {code}"
            _LOGGER.error(
                "API returned error %s for action '%s': %s",
                code,
                action,
                error_msg,
            )
            raise DessMonitorError(error_msg)
        return data

    @staticmethod
    def _is_auth_error(error_msg: str) -> bool:
        """Check if an error message indicates an authentication issue."""
        auth_keywords = [
            "token",
            "auth",
            "login",
            "session",
            "expired",
            "unauthorized",
            "forbidden",
        ]
        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in auth_keywords)

    async def authenticate(self) -> bool:
        """Authenticate with the ValueClouds API."""
        _LOGGER.debug(
            "Starting authentication process for user: %s",
            _mask_identifier(self.username),
        )
        try:
            self.token = None
            self.secret = None
            _LOGGER.debug("Cleared existing authentication tokens")

            hashed_password = self._sha1(self.password)
            payload = {
                "account": self.username,
                "password": hashed_password,
                "project": HEADER_PROJECT,
            }
            _LOGGER.debug(
                "Authentication parameters: %s",
                {
                    key: (
                        "***"
                        if key in {"account", "password"}
                        else value
                    )
                    for key, value in payload.items()
                },
            )

            response = await self._make_post_request("ppr/web/login/login", payload)

            _LOGGER.debug("Login response: %s", {
                "success": response.get("success"),
                "code": response.get("code"),
                "message": response.get("message"),
                "has_data": "data" in response,
            })

            if response.get("success") is False or (
                response.get("success") is None
                and response.get("code") is not None
                and response.get("code") != 0
            ):
                error_code = response.get("code")
                error_msg = (
                    response.get("message")
                    or response.get("errorMessage")
                    or f"Login failed with code {error_code}"
                )
                _LOGGER.error("Login rejected: code=%s, message=%s", error_code, error_msg)
                raise DessMonitorError(error_msg)

            data = response.get("data") or {}
            self.token = data.get("token")
            self.secret = data.get("secret")

            _LOGGER.debug(
                "Authentication response data keys: %s", list(data.keys())
            )
            _LOGGER.debug("Token received: %s", "Yes" if self.token else "No")
            _LOGGER.debug("Secret received: %s", "Yes" if self.secret else "No")

            if not self.token:
                raise DessMonitorError("Login response did not include a token")

            _LOGGER.info(
                "Successfully authenticated with ValueClouds API"
            )

            if self._store and self.token:
                await self._save_token()

            return True

        except Exception as err:
            _LOGGER.error(
                "Authentication failed for user %s: %s",
                _mask_identifier(self.username),
                err,
            )
            _LOGGER.debug("Authentication error details", exc_info=True)
            raise DessMonitorError(f"Authentication failed: {err}") from err

    async def load_saved_token(self) -> bool:
        """Load saved token from storage."""
        if not self._store:
            return False

        try:
            data = await self._store.async_load()
        except Exception as err:
            _LOGGER.debug("Failed to load saved token: %s", err)
            return False

        if not data:
            return False

        saved_token = data.get("token")

        if not saved_token:
            _LOGGER.debug("Saved token missing required fields, ignoring cached value")
            await self.clear_saved_token()
            return False

        self.token = saved_token
        self.secret = data.get("secret")

        _LOGGER.info("Reused saved token")
        return True

    async def _save_token(self) -> None:
        """Save current token to storage."""
        if not self._store:
            return

        try:
            await self._store.async_save(
                {
                    "token": self.token,
                    "secret": self.secret,
                }
            )
            _LOGGER.debug("Token saved to storage")
        except Exception as err:
            _LOGGER.debug("Failed to save token: %s", err)

    async def clear_saved_token(self) -> None:
        """Remove any saved token from storage and reset local state."""
        self.token = None
        self.secret = None

        if not self._store:
            return

        try:
            await self._store.async_remove()
            _LOGGER.debug("Cleared cached ValueClouds token from storage")
        except FileNotFoundError:
            _LOGGER.debug("Cached ValueClouds token file already removed")
        except Exception as err:
            _LOGGER.debug("Failed to clear cached token: %s", err)

    async def get_device_data(self) -> list[dict[str, Any]]:
        """Fetch the raw list of named field readings for the configured device.

        Logs in first if there is no cached token. On an auth-rejection
        response, performs exactly one reactive re-login and retry.
        """
        if self.token is None:
            await self.authenticate()

        try:
            return await self._async_fetch_device_data()
        except DessMonitorError as err:
            if self._is_auth_error(str(err)):
                _LOGGER.warning("Token rejected, re-authenticating and retrying once")
                await self.authenticate()
                return await self._async_fetch_device_data()
            raise

    async def _async_fetch_device_data(self) -> list[dict[str, Any]]:
        """Fetch device data using queryDeviceOneDataxxx endpoint."""
        params = {
            "pn": self.pn,
            "sn": self.sn,
            "devcode": self.devcode,
            "devaddr": self.devaddr,
            "i18n": DEFAULT_I18N,
        }

        _LOGGER.debug("Fetching device data with params: pn=%s, sn=%s, devcode=%s", 
                      _mask_identifier(self.pn), _mask_identifier(self.sn), self.devcode)

        response = await self._make_request(
            "ppe/api/auth/web/queryDeviceOneDataxxx", params
        )

        _LOGGER.debug("Device data response: success=%s, has_data=%s", 
                      response.get("success"), "data" in response)

        fields = response.get("data")
        if not isinstance(fields, list):
            _LOGGER.error("Device data response 'data' is not a list: %s", type(fields))
            raise DessMonitorError("Device data response 'data' was not a list")

        _LOGGER.debug("Retrieved %d data points for device", len(fields))

        return fields

    async def get_collectors(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Get list of collectors - returns configured device for ValueClouds."""
        if not self.pn or not self.sn or not self.devcode:
            raise DessMonitorError(
                "PN, SN, and devcode must be configured for ValueClouds"
            )

        collector = {
            "pn": self.pn,
            "pname": "ValueClouds Inverter",
        }

        _LOGGER.info("Using configured device: PN=%s, SN=%s", self.pn, self.sn)
        return [collector], [{"pid": 1, "pname": "ValueClouds"}]

    async def get_collector_devices(self, pn: str) -> dict[str, Any]:
        """Get devices under a collector - returns configured device."""
        return {
            "pn": pn,
            "dev": [
                {
                    "devcode": int(self.devcode) if self.devcode.isdigit() else 0,
                    "devaddr": 255,
                    "sn": self.sn,
                    "alias": f"Inverter {self.sn}",
                }
            ],
        }

    async def get_device_last_data(
        self, pn: str, devcode: int, devaddr: int, sn: str
    ) -> list[dict[str, Any]]:
        """Get latest device data - delegates to get_device_data."""
        return await self.get_device_data()

    async def get_device_summary_data(self, pid: int) -> dict[str, dict[str, Any]]:
        """Get device summary data - not available in ValueClouds API v1."""
        return {}

    async def get_device_control_fields(
        self, pn: str, devcode: int, devaddr: int, sn: str
    ) -> dict[str, Any]:
        """Get device control fields - not available in ValueClouds API v1."""
        return {}

    async def get_device_parameters(
        self, pn: str, devcode: int, devaddr: int, sn: str
    ) -> dict[str, Any]:
        """Get device parameters - not available in ValueClouds API v1."""
        return {}

    async def get_device_control_value(
        self, pn: str, devcode: int, devaddr: int, sn: str, field_id: str
    ) -> dict[str, Any]:
        """Get current value of a single control field - not available in ValueClouds API v1."""
        return {}

    async def set_device_control_value(
        self,
        pn: str,
        devcode: int,
        devaddr: int,
        sn: str,
        param_id: str,
        value: str,
    ) -> dict[str, Any]:
        """Set a device control value - not available in ValueClouds API v1."""
        _LOGGER.warning(
            "Setting device control values is not supported in ValueClouds API v1"
        )
        return {"success": False, "message": "Not supported in v1"}


class DessMonitorError(Exception):
    """Exception raised for ValueClouds API errors."""
