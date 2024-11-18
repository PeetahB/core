"""Support for OpenUV buttons."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a OpenUV button."""

    async_add_entities([AddSkinTypeButton(hass)], update_before_add=False)


class AddSkinTypeButton(ButtonEntity):
    """Button to add a new skin type profile."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the Add Skin Type button."""

        self._hass = hass
        self._attr_unique_id = f"{DOMAIN}_add_skin_type_profile"
        self._attr_name = "Add Skin Type Profile"
        self._attr_icon = "mdi:face-plus"

    @property
    def device_info(self) -> dict:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "skintype_profiles")},
            "name": "Skin Type Profiles",
            "manufacturer": "OpenUV",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        # Define what happens when the button is pressed
        await self._hass.services.async_call(
            DOMAIN,
            "set_skintype_profile",
            {"username": "default_user", "skin_type": 1},
        )
