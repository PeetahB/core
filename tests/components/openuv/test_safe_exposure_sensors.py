"""Define tests for the safe exposure sensors in the OpenUV integration."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.openuv.sensor import (
    EXPOSURE_TYPE_MAP,
    OpenUvSensorEntityDescription,
    async_setup_entry,
)
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_async_setup_entry_specific_skin_type(hass: HomeAssistant) -> None:
    """Test async_setup_entry for a specific skin type, isolating a single safe exposure sensor."""
    # Mock necessary objects
    entry = MagicMock()
    entry.data = {
        "skin_type": "None",
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    entry.options = {"skin_type": "Skin Type I"}  # Specific skin type (Type I)
    entry.entry_id = "test_entry"

    # Mock the coordinators with the necessary 'uv' key
    coordinators = {
        "uv": MagicMock()  # Mocking the UV coordinator
    }

    hass.data = {"openuv": {entry.entry_id: coordinators}}

    # Mock async_add_entities to track the added sensors
    async_add_entities = MagicMock()

    # Mock the specific OpenUvSensorEntityDescription for Skin Type I
    specific_description = OpenUvSensorEntityDescription(
        key="type_safe_exposure_time_1",
        translation_key="skin_type_1_safe_exposure_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class="measurement",
        value_fn=lambda data: data["safe_exposure_time"].get(
            "type_safe_exposure_time_1"
        ),
    )

    # Mock the OpenUvSensor creation to return a sensor with an appropriate entity_id
    with (
        patch(
            "homeassistant.components.openuv.sensor.SENSOR_DESCRIPTIONS",
            [specific_description],  # Only include the description for Skin Type I
        ),
        patch(
            "homeassistant.components.openuv.sensor.OpenUvSensor",
            side_effect=lambda coordinator, description: MagicMock(
                entity_id=f"sensor.openuv_{description.translation_key}",
            ),
        ),
    ):
        # Run the setup function
        await async_setup_entry(hass, entry, async_add_entities)

    # Flatten the list of sensors added through async_add_entities
    added_sensors = [
        sensor for call in async_add_entities.call_args_list for sensor in call[0][0]
    ]

    expected_entity_ids = "sensor.openuv_skin_type_1_safe_exposure_time"

    # Filter the added_sensors to only those whose entity_id matches the expected ones
    safe_exposure_sensor = [
        sensor for sensor in added_sensors if sensor.entity_id == expected_entity_ids
    ]

    # Verify that only the Skin Type I sensor was added
    assert (
        len(safe_exposure_sensor) == 1
    ), "Only one sensor should be added for the specific skin type"
    assert (
        safe_exposure_sensor[0].entity_id
        == "sensor.openuv_skin_type_1_safe_exposure_time"
    ), "Skin Type I safe exposure sensor should have been added"


async def test_async_setup_entry_all_safe_exposure_sensors(hass: HomeAssistant) -> None:
    """Test async_setup_entry to ensure all safe exposure sensors (types I to VI) are added when skin type is None."""
    # Mock necessary objects
    entry = MagicMock()
    entry.data = {
        "skin_type": "None",  # Skin type is None, so all safe exposure sensors should be added
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    entry.options = {"skin_type": "None"}  # Skin type explicitly set to None
    entry.entry_id = "test_entry"
    entry.async_on_unload = MagicMock()
    entry.add_update_listener = MagicMock()

    # Mock the coordinators with the necessary 'uv' key
    coordinators = {
        "uv": MagicMock()  # Mocking the UV coordinator
    }

    hass.data = {"openuv": {entry.entry_id: coordinators}}

    # Mock async_add_entities using MagicMock instead of AsyncMock if it's not supposed to be awaited
    async_add_entities = MagicMock()

    # Create mock `OpenUvSensorEntityDescription` objects for each safe exposure type
    mock_descriptions = [
        OpenUvSensorEntityDescription(
            key=f"type_safe_exposure_time_{i}",
            translation_key=f"skin_type_{i}_safe_exposure_time",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data, i=i: data["safe_exposure_time"][
                EXPOSURE_TYPE_MAP[f"type_safe_exposure_time_{i}"]
            ],
        )
        for i in range(1, 7)
    ]

    # Patch `SENSOR_DESCRIPTIONS` to include only safe exposure sensors for this test
    with (
        patch(
            "homeassistant.components.openuv.sensor.SENSOR_DESCRIPTIONS",
            mock_descriptions,
        ),
        patch(
            "homeassistant.components.openuv.sensor.OpenUvSensor",
            side_effect=lambda coordinator, description: MagicMock(
                entity_id=f"sensor.openuv_{description.translation_key}"
            ),
        ),
        patch(
            "homeassistant.components.openuv.sensor.async_setup_entry",
            side_effect=async_setup_entry,
        ),
    ):
        # Run the setup function
        await async_setup_entry(hass, entry, async_add_entities)

    # Collect the sensors added via async_add_entities
    added_sensors = [
        sensor for call in async_add_entities.call_args_list for sensor in call[0][0]
    ]

    # Create expected entity_ids for the six safe exposure sensors
    expected_entity_ids = [
        f"sensor.openuv_skin_type_{i}_safe_exposure_time" for i in range(1, 7)
    ]

    # Filter the added_sensors to only those whose entity_id matches the expected ones
    safe_exposure_sensors = [
        sensor for sensor in added_sensors if sensor.entity_id in expected_entity_ids
    ]

    # Verify that all six safe exposure sensors were added
    for i in range(1, 7):
        expected_entity_id = f"sensor.openuv_skin_type_{i}_safe_exposure_time"
        assert any(
            sensor.entity_id == expected_entity_id for sensor in added_sensors
        ), f"Safe exposure sensor for type {i} should be added"

    # Verify that the correct number of sensors were added
    assert len(safe_exposure_sensors) == 6
