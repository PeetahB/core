"Buttons for vitamin D."

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


@dataclass(frozen=True, kw_only=True)
class OpenUVButtonEntityDescription(ButtonEntityDescription):
    """Class to describe a Button entity."""

    press_action: Callable  # any


ENTITY_DESCRIPTIONS = [
    OpenUVButtonEntityDescription(
        key="vitamin_d",
        name="Vitamin D",
        press_action=lambda x: get_smt(x),  # pylint: disable=unnecessary-lambda
        icon="mdi:target",
    ),
    # OpenUVButtonEntityDescription(
    #     key="stop-pump",
    #     name="Sunscreen",
    #     press_action=lambda x: get_smt(x),
    #     icon="mdi:stop",
    # ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the openuv buttons."""
    # Create and add the switch entity
    _ = hass, entry
    async_add_entities(OpenUVButton(description) for description in ENTITY_DESCRIPTIONS)


class OpenUVButton(ButtonEntity):
    """Representation of openuv button."""

    entity_description: OpenUVButtonEntityDescription

    def __init__(self, entity_description: OpenUVButtonEntityDescription) -> None:
        "Initialize the button."
        super().__init__()
        self.entity_description = entity_description
        self._key = entity_description.key

    @property
    def unique_id(self) -> str:
        "Create unique id for OpenUVButton."
        return f"button_{self._key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        self.entity_description.press_action(self)


def get_smt(button_entity_description: OpenUVButtonEntityDescription) -> None:
    "Extend the name of the button (treated as description)."
    if isinstance(button_entity_description.name, str):
        button_entity_description.name = button_entity_description.name + " 20mins"
