"""Support for OpenUV skin type profiles."""

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_KEY = f"{DOMAIN}_skintype_profiles"
STORAGE_VERSION = 1

# Service schema
SET_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("skin_type"): int,
    }
)


async def async_setup_skintype_profiles(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the skin type profiles feature."""
    # Initialize storage
    store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    profiles = await store.async_load() or {"skintype_profiles": []}

    # Save data to `hass.data`
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["skintype_profiles_store"] = store
    hass.data[DOMAIN]["skintype_profiles"] = profiles
    hass.data[DOMAIN]["platform"] = {"async_add_entities": async_add_entities}

    # Define service to manage profiles
    async def async_set_skintype_profile(call: ServiceCall) -> None:
        """Handle adding/updating skin type profiles."""
        username = call.data["username"]
        skin_type = call.data["skin_type"]

        updated = False
        for profile in profiles["skintype_profiles"]:
            if profile["username"] == username:
                profile["skin_type"] = skin_type
                updated = True
                break

        if not updated:
            profiles["skintype_profiles"].append(
                {"username": username, "skin_type": skin_type}
            )

        # Save updated profiles
        await store.async_save(profiles)

        # Update or create corresponding entities
        await async_add_or_update_entity(hass, username)

    # Register the service
    hass.services.async_register(
        DOMAIN,
        "set_skintype_profile",
        async_set_skintype_profile,
        schema=SET_PROFILE_SCHEMA,
    )

    # Initialize existing profiles as entities
    for profile in profiles["skintype_profiles"]:
        await async_add_or_update_entity(hass, profile["username"])


async def async_add_or_update_entity(hass: HomeAssistant, username: str) -> None:
    """Add or update an entity for the specified username."""
    store = hass.data[DOMAIN]["skintype_profiles_store"]
    profiles = hass.data[DOMAIN]["skintype_profiles"]

    # Find the profile by username
    profile = next(
        (p for p in profiles["skintype_profiles"] if p["username"] == username),
        None,
    )

    if not profile:
        return  # Profile does not exist

    # Create or update entity
    entity_id = f"{DOMAIN}.skintype_{username}"

    # Update existing entity
    if entity_id in hass.states.async_entity_ids():
        await async_update_entity(hass, entity_id)
        return

    # Add new entity
    async_add_entities = hass.data[DOMAIN]["platform"].get("async_add_entities")
    if async_add_entities:
        entity = SkinTypeProfileEntity(username, profile["skin_type"], store)
        async_add_entities([entity])


class SkinTypeProfileEntity(SensorEntity):
    """Representation of a skin type profile."""

    def __init__(self, username: str, skin_type: int, store: Store) -> None:
        """Initialize the entity."""
        self._username = username
        self._skin_type = skin_type
        self._store = store
        self._attr_unique_id = f"{DOMAIN}_skintype_profile_{username}"
        self._attr_name = f"{username} Skin Type Profile"  # Name of the entity

    @property
    def state(self) -> int:
        """Return the current state."""
        return self._skin_type

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional attributes."""
        return {"username": self._username}

    async def async_update(self) -> None:
        """Update the entity state."""
        profiles = await self._store.async_load() or {"skintype_profiles": []}
        profile = next(
            (
                p
                for p in profiles["skintype_profiles"]
                if p["username"] == self._username
            ),
            None,
        )
        if profile:
            self._skin_type = profile["skin_type"]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await self.async_update()
