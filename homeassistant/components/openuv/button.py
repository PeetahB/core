"Buttons for vitamin D."

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_UV, DOMAIN
from .coordinator import OpenUvCoordinator
from .sensor import get_uv_label


@dataclass(frozen=True, kw_only=True)
class OpenUVButtonEntityDescription(ButtonEntityDescription):
    """Class to describe a Button entity."""

    press_action: Callable  # any


ENTITY_DESCRIPTIONS = [
    OpenUVButtonEntityDescription(
        key="vitamin_d",
        name="Vitamin D",
        press_action=lambda coordinator, button: get_smt(coordinator, button),  # pylint: disable=unnecessary-lambda
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
    coordinators: dict[str, OpenUvCoordinator] = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OpenUVButton(coordinators[DATA_UV], description)
        for description in ENTITY_DESCRIPTIONS
    )


class OpenUVButton(ButtonEntity):
    """Representation of openuv button."""

    entity_description: OpenUVButtonEntityDescription
    sun_exposure_time: int
    basic_name: str

    def __init__(
        self,
        coordinator: OpenUvCoordinator,
        entity_description: OpenUVButtonEntityDescription,
    ) -> None:
        "Initialize the button."
        super().__init__()
        self.entity_description = entity_description
        self._key = entity_description.key
        self._coordinator = coordinator
        self.sun_exposure_time = 0
        self.basic_name = "Vitamin D button"

    @property
    def unique_id(self) -> str:
        "Create unique id for OpenUVButton."
        return f"button_{self._key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        self.entity_description.press_action(self._coordinator, self)
        # self.async_write_ha_state()


def get_smt(coordinator: OpenUvCoordinator, button_entity: OpenUVButton) -> None:
    "Extend the name of the button (treated as description)."
    # print(f"name before calling: {button_entity.entity_description.name}")
    if "uv" in coordinator.data:
        # I need to know the skin type in order to calculate the vitamin D intake
        uv_level = get_uv_label(coordinator.data["uv"])  # gets the current uv index
        _ = uv_level
        # print(f"current uv level: {uv_level}")
    if isinstance(button_entity.name, str):
        button_entity.sun_exposure_time = 20  # so far hardcoded
        button_entity.name = (
            button_entity.basic_name + str(button_entity.sun_exposure_time) + " mins"
        )
        # print(f"after calling: {button_entity.entity_description.name}")
