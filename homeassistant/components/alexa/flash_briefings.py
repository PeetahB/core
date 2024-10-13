"""Support for Alexa skill service end point."""

import hmac
from http import HTTPStatus
import logging
import uuid

from aiohttp.web_response import StreamResponse

from homeassistant.components import http
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import template
from homeassistant.helpers.typing import ConfigType
import homeassistant.util.dt as dt_util

from .const import (
    API_PASSWORD,
    ATTR_MAIN_TEXT,
    ATTR_REDIRECTION_URL,
    ATTR_STREAM_URL,
    ATTR_TITLE_TEXT,
    ATTR_UID,
    ATTR_UPDATE_DATE,
    CONF_AUDIO,
    CONF_DISPLAY_URL,
    CONF_TEXT,
    CONF_TITLE,
    CONF_UID,
    DATE_FORMAT,
)

_LOGGER = logging.getLogger(__name__)

FLASH_BRIEFINGS_API_ENDPOINT = "/api/alexa/flash_briefings/{briefing_id}"


@callback
def async_setup(hass: HomeAssistant, flash_briefing_config: ConfigType) -> None:
    """Activate Alexa component."""
    hass.http.register_view(AlexaFlashBriefingView(hass, flash_briefing_config))


class AlexaFlashBriefingView(http.HomeAssistantView):
    """Handle Alexa Flash Briefing skill requests."""

    url = FLASH_BRIEFINGS_API_ENDPOINT
    requires_auth = False
    name = "api:alexa:flash_briefings"

    def __init__(self, hass: HomeAssistant, flash_briefings: ConfigType) -> None:
        """Initialize Alexa view."""
        super().__init__()
        self.flash_briefings = flash_briefings

    @callback
    def get(
        self, request: http.HomeAssistantRequest, briefing_id: str
    ) -> StreamResponse | tuple[bytes, HTTPStatus]:
        """Handle Alexa Flash Briefing request."""
        _LOGGER.debug("Received Alexa flash briefing request for: %s", briefing_id)

        # Check for the presence of API password
        api_password = request.query.get(API_PASSWORD)
        if api_password is None:
            return self._unauthorized_response(
                "No password provided for Alexa flash briefing: %s", briefing_id
            )

        # Validate the provided password
        if not self._is_valid_password(api_password):
            return self._unauthorized_response(
                "Wrong password for Alexa flash briefing: %s", briefing_id
            )

        # Check if the briefing exists
        briefing = self.flash_briefings.get(briefing_id)
        if not isinstance(briefing, list):
            return self._not_found_response(
                "No configured Alexa flash briefing was found for: %s", briefing_id
            )

        # Generate and return the briefing response
        response = [self._render_briefing_item(item) for item in briefing]
        return self.json(response)

    def _unauthorized_response(
        self, error_msg: str, briefing_id: str
    ) -> tuple[bytes, HTTPStatus]:
        """Return a 401 Unauthorized error with logging."""
        _LOGGER.error(error_msg, briefing_id)
        return b"", HTTPStatus.UNAUTHORIZED

    def _not_found_response(
        self, error_msg: str, briefing_id: str
    ) -> tuple[bytes, HTTPStatus]:
        """Return a 404 Not Found error with logging."""
        _LOGGER.error(error_msg, briefing_id)
        return b"", HTTPStatus.NOT_FOUND

    def _is_valid_password(self, password: str) -> bool:
        """Validate the API password for the flash briefing."""
        return hmac.compare_digest(
            password.encode("utf-8"),
            self.flash_briefings[CONF_PASSWORD].encode("utf-8"),
        )

    def _render_briefing_item(self, item: dict) -> dict:
        """Render a single briefing item."""
        return {
            ATTR_TITLE_TEXT: self._render_template(item, CONF_TITLE),
            ATTR_MAIN_TEXT: self._render_template(item, CONF_TEXT),
            ATTR_UID: item.get(CONF_UID) or str(uuid.uuid4()),
            ATTR_STREAM_URL: self._render_template(item, CONF_AUDIO),
            ATTR_REDIRECTION_URL: self._render_template(item, CONF_DISPLAY_URL),
            ATTR_UPDATE_DATE: dt_util.utcnow().strftime(DATE_FORMAT),
        }

    def _render_template(self, item: dict, key: str) -> str | None:
        """Render template if the item has a templated field, otherwise return its value."""
        if item.get(key) is None:
            return None

        if isinstance(item.get(key), template.Template):
            return item[key].async_render(parse_result=False)

        return item.get(key)
